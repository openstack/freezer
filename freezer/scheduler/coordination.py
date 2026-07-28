# Copyright 2026 Cleura AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Coordination layer for running freezer-scheduler as a cluster.

Several schedulers configured with the same ``client_id`` form a cluster.
To freezer-api they look like a single client and therefore all poll the
same set of jobs; coordination decides which member actually runs each job
so backups are not duplicated.

The mechanism is entirely scheduler-side and uses `tooz`_:

* The tooz group is named after the shared ``client_id`` (the cluster
  identity). Members are told apart by a unique per-process member id
  (``<hostname>-<pid>``), the hostname being kept only for readability in
  ``get_members()`` output and logs. tooz heartbeats the membership at the
  cadence the backend session timeout requires (tunable via the backend
  URL, e.g. ``redis://host:6379?timeout=30``).
* Job ownership is decided with a consistent hash ring built once per
  poll tick from the live group members (see :meth:`refresh`). Because
  every member feeds the same member set and the same job id into the
  same ring, they all agree on the owner with no messaging.
* Before running a job the owner takes a per-job distributed lock, which
  guards the brief window when membership is changing.

All coordination calls fail safe: if the backend is unreachable ownership
cannot be determined and the lock cannot be taken, so jobs are skipped
rather than run without coordination (which would risk duplicate
backups). refresh() also self-heals: it (re)connects and (re)joins the
group, so a backend that was down at startup or a member evicted during
an outage recovers on a later poll tick without a restart.

.. _tooz: https://docs.openstack.org/tooz/latest/
"""

import contextlib
import os
import socket
import typing

from oslo_log import log
from oslo_utils import encodeutils
from tooz import coordination
from tooz import hashring


LOG = log.getLogger(__name__)


class SchedulerCoordinator(object):
    """Wraps tooz group membership, hash-ring ownership and job locks."""

    def __init__(self, client_id: str, backend_url: str) -> None:
        self._client_id = client_id
        self._backend_url = backend_url
        # Group name == client_id: the shared cluster identity.
        self._group_id = encodeutils.to_utf8(client_id)
        # Unique per-process member id. If a restarted process reuses the
        # id (containers: stable hostname, pid 1) the stale session blocks
        # the join until it expires; refresh() then rejoins.
        self._member_id = encodeutils.to_utf8(
            f'{socket.gethostname()}-{os.getpid()}')
        self._coordinator: typing.Optional[
            coordination.CoordinationDriver] = None
        self._ring: typing.Optional[hashring.HashRing] = None

    @property
    def member_id(self) -> str:
        return self._member_id.decode('utf-8')

    def start(self) -> None:
        """Connect to the backend and join the group.

        Idempotent: a repeated call (e.g. from the daemon's
        restart-on-error loop) is a no-op once connected, so connections
        and heartbeat threads cannot accumulate. Heartbeating is handled
        by tooz itself (``start_heart``).
        """
        if self._coordinator:
            return
        coord = coordination.get_coordinator(
            self._backend_url, self._member_id)
        coord.start(start_heart=True)
        self._coordinator = coord
        self._join_group()
        LOG.info('Coordination started: group=%s member=%s backend=%s',
                 self._client_id, self.member_id, self._backend_url)

    def _join_group(self) -> None:
        try:
            self._coordinator.join_group_create(self._group_id)
        except coordination.MemberAlreadyExist:
            LOG.warning('Member %s already present in group %s '
                        '(stale session?), will rejoin when it expires',
                        self.member_id, self._client_id)

    def stop(self) -> None:
        if not self._coordinator:
            LOG.debug('No coordinator to stop')
            return
        try:
            self._coordinator.leave_group(self._group_id).get()
        except Exception as e:
            LOG.warning('Error leaving coordination group %s: %s',
                        self._client_id, e)
        try:
            self._coordinator.stop()
        except Exception as e:
            LOG.warning('Error stopping coordinator: %s', e)
        self._coordinator = None
        self._ring = None

    def _members(self) -> typing.Set[bytes]:
        return set(self._coordinator.get_members(self._group_id).get())

    def refresh(self) -> None:
        """Rebuild the hash ring from live members; call once per tick.

        Self-healing: (re)connects and (re)joins as needed, covering a
        backend unreachable at startup and eviction after an outage.
        Fail-safe: on any error no ring is kept, so is_owner() returns
        False and jobs are skipped rather than run uncoordinated.
        """
        self._ring = None
        try:
            self.start()
            members = self._members()
            if self._member_id not in members:
                self._join_group()
                members = self._members()
            if self._member_id in members:
                self._ring = hashring.HashRing(members)
            else:
                LOG.warning('Not a member of group %s this tick, '
                            'skipping jobs', self._client_id)
        except Exception as e:
            LOG.warning('Coordination unavailable, skipping jobs: %s', e)

    def is_owner(self, job_id: str) -> bool:
        """Return True if this member owns ``job_id`` on the current ring.

        Uses the ring built by the last refresh(); without one (backend
        unreachable, not a group member) everything is skipped.
        """
        if self._ring is None:
            return False
        return self._member_id in self._ring.get_nodes(
            encodeutils.to_utf8(job_id))

    @contextlib.contextmanager
    def job_lock(self, job_id: str) -> typing.Iterator[bool]:
        """Yield True if the per-job distributed lock was acquired.

        Fail-safe: if the lock is held elsewhere or the backend is
        unreachable, yields False and the caller must not run the job.
        The lock is released automatically when the block exits (and, if
        this member dies, when its tooz heartbeat expires).
        """
        try:
            lock = self._coordinator.get_lock(encodeutils.to_utf8(job_id))
            acquired = lock.acquire(blocking=False)
        except Exception as e:
            LOG.warning('Cannot acquire lock for job %s, skipping: %s',
                        job_id, e)
            yield False
            return
        try:
            yield acquired
        finally:
            if acquired:
                try:
                    lock.release()
                except Exception as e:
                    LOG.warning('Error releasing lock for job %s: %s',
                                job_id, e)
