====================================
Scheduler Coordination (Clustering)
====================================

What clustered mode is
======================

By default each ``freezer-scheduler`` registers in freezer-api as a
client (its ``client_id`` defaults to the machine hostname) and only
runs the jobs bound to that ``client_id``. This has two problems:

* If the scheduler dies, its jobs stop running until it is restarted —
  there is no HA.
* Two schedulers configured with the same ``client_id`` both match the
  same jobs and race to execute them, producing duplicate runs.

Clustered mode solves both: several schedulers configured with the
**same** ``client_id`` form a cluster and share the jobs bound to that
``client_id``. Jobs are spread across the members, and when a member
dies its jobs are picked up by the survivors.

How it works
============

Coordination is entirely scheduler-side and uses the `tooz`_ library;
freezer-api and its data model are unchanged. To the API a cluster
looks like a single client.

* On startup each scheduler joins a tooz group named after its
  ``client_id``, under a unique per-process member id
  (``<hostname>-<pid>``), and runs a heartbeat. A member that stops
  heartbeating is dropped from the group after the backend timeout.
* Job ownership is decided with a consistent hash ring built from the
  live group members. Every member computes the same ring, so they all
  agree on each job's owner without any messaging.
* Before spawning ``freezer-agent`` the owning member takes a per-job
  distributed lock, which prevents duplicate execution during the brief
  window when membership is changing. If a member dies holding the
  lock, the lock is released when its heartbeat expires.

If a scheduler dies mid-backup, that run is lost; the job's new owner
picks it up on the next scheduled tick. Recovery time after a member
dies is approximately the tooz session timeout plus the poll interval.

If the tooz backend itself becomes unreachable, members fail safe: they
cannot determine ownership or hold locks, so they skip executing jobs
until coordination is restored rather than all running everything
(which would duplicate backups). A delayed backup is preferable to
duplicate or racing backups.

A firing that is skipped because its lock cannot be taken is not lost:
it is retried with exponential backoff (starting at 60 seconds and
capped at one hour) until the lock becomes available. This matters most
for run-once jobs, which have no later scheduled tick to fall back on;
recurring jobs whose own next tick arrives sooner than the next retry
are left to that tick instead.

When to use it
==============

Use clustered mode when backup jobs must keep running even if a
scheduler host dies, or when you want to spread many jobs across a pool
of schedulers instead of pinning each job to one host. For a single
scheduler per host with host-bound jobs (e.g. filesystem backups of
that host), keep the default standalone mode.

How to configure it
===================

1. Deploy a tooz-supported coordination backend (ZooKeeper, etcd or
   Redis) reachable from all scheduler hosts, and secure it — its
   credentials live in the scheduler config file.

2. Install the matching tooz backend client library on every scheduler
   host, e.g. ``pip install tooz[redis]`` (or ``tooz[zookeeper]``,
   ``tooz[etcd3gw]``); distribution packages typically provide it as
   the corresponding Python client package.

3. Configure every member with the same ``client_id`` and the backend
   URL:

   .. code-block:: ini

      [scheduler]
      client_id = backup-cluster-1

      [coordination]
      backend_url = redis://coordination-host:6379

4. Start as many schedulers as desired. Members join and leave the
   cluster dynamically; jobs rebalance automatically.

Clustered mode is opt-in: if ``backend_url`` is unset the scheduler
runs standalone exactly as before.

.. warning::

   Without a coordination backend, schedulers sharing a ``client_id``
   will duplicate job runs.

.. warning::

   Clustered mode is not supported in Windows service mode.

The ``[coordination]`` options are documented in the generated
:doc:`configuration reference <config-reference>`.

.. _tooz: https://docs.openstack.org/tooz/latest/
