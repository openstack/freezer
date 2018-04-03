========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/freezer.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

OpenStack Freezer
=================

.. image:: freezer_logo.jpg

Freezer is a Backup Restore DR as a Service platform that helps you to automate
the data backup and restore process.

The following features are available:

-  Backup file system using point-in-time snapshot
-  Strong encryption supported: AES-256-CFB
-  Backup file system tree directly (without volume snapshot)
-  Backup journalled MongoDB directory tree using lvm snapshot to Swift
-  Backup MySQL with lvm snapshot
-  Restore data from a specific date automatically to file system
-  Low storage consumption as the backup are uploaded as a stream
-  Flexible backup policy (incremental and differential)
-  Data is archived in GNU Tar format for file based incremental
-  Multiple compression algorithm support (zlib, bzip2, xz)
-  Remove old backup automatically according to the provided parameters
-  Multiple storage media support (Swift, local file system, or ssh)
-  Flush kernel buffered memory to disk
-  Multi-platform (Linux, Windows, \*BSD, OSX)
-  Manage multiple jobs (I.e., multiple backups on the same node)
-  Synchronize backups and restore on multiple nodes
-  Web user interface integrated with OpenStack Horizon
-  Execute scripts/commands before or after a job execution
-  More ...

To learn how to use Freezer's API, consult the documentation available online
at:

- `Backup API Reference <https://developer.openstack.org/api-ref/backup/>`__
- `Freezer API <https://github.com/openstack/freezer-api>`__

Freezer Disaster Recovery:
- `Freezer DR <https://github.com/openstack/freezer-dr>`__

Freezer Horizon plugin:
- `Freezer Web UI <https://github.com/openstack/freezer-web-ui>`__

For more information on OpenStack APIs, SDKs and CLIs in general, refer to:

- `OpenStack for App Developers <https://www.openstack.org/appdev/>`__
- `Development resources for OpenStack clouds
  <https://developer.openstack.org/>`__

Operators
---------

To learn how to deploy and configure OpenStack Freezer, consult the
documentation available online at:

- `OpenStack Freezer <https://docs.openstack.org/freezer/latest/>`__

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate bug tracker. If you obtained the software from a 3rd party
operating system vendor, it is often wise to use their own bug tracker for
reporting problems. In all other cases use the master OpenStack bug tracker,
available at:

- `Bug Tracker <https://bugs.launchpad.net/freezer>`__

Developers
----------

Any new code must follow the development guidelines detailed in the HACKING.rst
file and OpenStack general development guidelines, and pass all unit tests.

Further developer focused documentation is available at:

- `Official Freezer Documentation <https://docs.openstack.org/freezer/latest/>`__
- `Official Client Documentation
  <https://docs.openstack.org/python-freezerclient/latest/>`__

Other Information
-----------------

During each `Summit`_ and `Project Team Gathering`_, we agree on what the whole
community wants to focus on for the upcoming release. The plans for freezer can
be found at:

- `Freezer Old README <https://github.com/openstack/freezer/tree/master/doc/README.rst>`__

- `Freezer Specs <http://specs.openstack.org/openstack/freezer-specs/>`__

.. _Summit: https://www.openstack.org/summit/
.. _Project Team Gathering: https://www.openstack.org/ptg/
