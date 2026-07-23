# Copyright 2026 Cleura AB
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import shutil
import tempfile
import unittest
from unittest import mock

from freezer.scheduler import coordination


class TestSchedulerCoordinator(unittest.TestCase):
    def setUp(self):
        self.coord = coordination.SchedulerCoordinator(
            client_id='project_host',
            backend_url='redis://localhost:6379')

    def _set_members(self, members):
        fake_coord = mock.MagicMock()
        fake_coord.get_members.return_value.get.return_value = members
        self.coord._coordinator = fake_coord
        return fake_coord

    def test_group_id_is_client_id(self):
        self.assertEqual(b'project_host', self.coord._group_id)

    def test_member_id_is_unique_per_process(self):
        # <hostname>-<pid>: hostname for readability, pid for uniqueness.
        self.assertIn('-', self.coord.member_id)
        self.assertTrue(self.coord.member_id.rsplit('-', 1)[1].isdigit())

    def test_start_is_idempotent(self):
        # The daemon's restart-on-error loop may call start() repeatedly;
        # once connected it must not create another coordinator.
        self.coord._coordinator = mock.MagicMock()
        with mock.patch.object(coordination.coordination,
                               'get_coordinator') as mock_get:
            self.coord.start()
            mock_get.assert_not_called()

    def test_refresh_builds_ring_and_owns_some_jobs(self):
        self._set_members({self.coord._member_id, b'other-1'})
        self.coord.refresh()
        self.assertIsNotNone(self.coord._ring)
        owned = [j for j in ('job-%d' % i for i in range(20))
                 if self.coord.is_owner(j)]
        self.assertTrue(owned)

    def test_refresh_rejoins_when_evicted(self):
        # Member missing from the group (evicted after a backend outage,
        # or blocked by a stale session at startup): refresh rejoins.
        fake_coord = self._set_members(set())
        fake_coord.get_members.return_value.get.side_effect = [
            set(), {self.coord._member_id}]
        self.coord.refresh()
        fake_coord.join_group_create.assert_called_once_with(
            self.coord._group_id)
        self.assertIsNotNone(self.coord._ring)

    def test_refresh_failsafe_on_backend_error(self):
        # Backend unreachable -> no ring -> jobs skipped, not run
        # uncoordinated.
        fake_coord = self._set_members(set())
        fake_coord.get_members.side_effect = Exception('backend down')
        self.coord.refresh()
        self.assertIsNone(self.coord._ring)
        self.assertFalse(self.coord.is_owner('job1'))

    def test_is_owner_false_without_ring(self):
        self.assertFalse(self.coord.is_owner('job1'))

    def test_is_owner_false_when_other_owns(self):
        self.coord._ring = mock.MagicMock()
        self.coord._ring.get_nodes.return_value = {b'other-1'}
        self.assertFalse(self.coord.is_owner('job1'))

    def test_job_lock_acquired_and_released(self):
        fake_coord = mock.MagicMock()
        lock = mock.MagicMock()
        lock.acquire.return_value = True
        fake_coord.get_lock.return_value = lock
        self.coord._coordinator = fake_coord

        with self.coord.job_lock('job1') as acquired:
            self.assertTrue(acquired)
        lock.release.assert_called_once()

    def test_job_lock_not_acquired(self):
        fake_coord = mock.MagicMock()
        lock = mock.MagicMock()
        lock.acquire.return_value = False
        fake_coord.get_lock.return_value = lock
        self.coord._coordinator = fake_coord

        with self.coord.job_lock('job1') as acquired:
            self.assertFalse(acquired)
        lock.release.assert_not_called()

    def test_job_lock_releases_and_propagates_on_body_error(self):
        # An error while running the job must propagate to the caller and
        # still release the lock.
        fake_coord = mock.MagicMock()
        lock = mock.MagicMock()
        lock.acquire.return_value = True
        fake_coord.get_lock.return_value = lock
        self.coord._coordinator = fake_coord

        def run():
            with self.coord.job_lock('job1'):
                raise ValueError('job failed')

        self.assertRaises(ValueError, run)
        lock.release.assert_called_once()

    def test_job_lock_failsafe_on_backend_error(self):
        fake_coord = mock.MagicMock()
        fake_coord.get_lock.side_effect = Exception('backend down')
        self.coord._coordinator = fake_coord

        with self.coord.job_lock('job1') as acquired:
            self.assertFalse(acquired)


class TestCoordinationFunctionalFileDriver(unittest.TestCase):
    """Functional tests against the local tooz ``file`` driver.

    The file driver keeps membership and locks in a shared directory, so
    several coordinators in one process behave like real cluster members —
    membership, ring ownership and locks are exercised for real, without
    external services.
    """

    def setUp(self):
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp_dir, ignore_errors=True)
        self._backend_url = 'file://%s' % tmp_dir

    def _make_member(self, member_id):
        coord = coordination.SchedulerCoordinator(
            client_id='cluster1', backend_url=self._backend_url)
        # Member ids are <hostname>-<pid> in production; in-process test
        # members would collide, so give each an explicit unique id.
        coord._member_id = member_id
        coord.start()
        self.addCleanup(coord.stop)
        return coord

    def test_single_member_owns_everything(self):
        c1 = self._make_member(b'member-1')
        c1.refresh()
        for job_id in ('job-a', 'job-b', 'job-c'):
            self.assertTrue(c1.is_owner(job_id))

    def test_ring_agreement_exactly_one_owner(self):
        members = [self._make_member(b'member-%d' % i) for i in range(3)]
        for m in members:
            m.refresh()
        for i in range(20):
            job_id = 'job-%d' % i
            owners = [m for m in members if m.is_owner(job_id)]
            self.assertEqual(
                1, len(owners),
                'job %s owned by %d members' % (job_id, len(owners)))

    def test_rebalance_on_leave(self):
        c1 = self._make_member(b'member-1')
        c2 = self._make_member(b'member-2')
        job_ids = ['job-%d' % i for i in range(20)]
        # With both members alive each job has exactly one owner.
        c1.refresh()
        c2.refresh()
        for job_id in job_ids:
            self.assertEqual(
                1, sum(m.is_owner(job_id) for m in (c1, c2)))
        # After member-2 leaves, member-1 owns everything.
        c2.stop()
        c1.refresh()
        for job_id in job_ids:
            self.assertTrue(c1.is_owner(job_id))

    def test_refresh_recovers_membership(self):
        # Simulate eviction: leave the group behind refresh()'s back,
        # then check the next tick rejoins instead of staying out forever.
        c1 = self._make_member(b'member-1')
        c1._coordinator.leave_group(c1._group_id).get()
        c1.refresh()
        self.assertTrue(c1.is_owner('job-a'))

    def test_job_lock_is_exclusive_across_members(self):
        c1 = self._make_member(b'member-1')
        c2 = self._make_member(b'member-2')
        with c1.job_lock('job-x') as acquired:
            self.assertTrue(acquired)
            with c2.job_lock('job-x') as acquired_other:
                self.assertFalse(acquired_other)
        # Released on exit: the other member can take it now.
        with c2.job_lock('job-x') as acquired_other:
            self.assertTrue(acquired_other)
