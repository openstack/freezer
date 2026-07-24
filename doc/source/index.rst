==================================
Welcome to Freezer's documentation
==================================

Freezer is a distributed Backup and Restore as a Service platform for
OpenStack environments and multi-OS heterogeneous infrastructure (Linux,
Windows, FreeBSD, macOS).

It delivers automated, efficient, and secure backup and restore capabilities
for file systems, databases, block storage volumes, and OpenStack cloud
infrastructure.

.. note::
   For a deep dive into component roles, performance tuning, and workflow
   details, see the :doc:`Freezer Overview & Architecture <overview>`
   document.

Key Features
============

Backup Engines & Workloads
--------------------------
* **File System Backups**: Point-in-time snapshots and tree backups (GNU
  Tar archive engine).
* **Database Backups**: Consistent LVM-backed snapshots for MongoDB
  journalled directory trees and MySQL DBs.
* **Block Storage Support**: Differential block backups using rsync
  algorithms and OpenStack Cinder volume integration.
* **Granular Restores**: Automated point-in-time restoration to local
  filesystems or volume targets.

Storage & Security
------------------
* **Multiple Storage Media**: Pluggable storage engines supporting OpenStack
  Swift object storage, local filesystems, S3, and SSH targets.
* **Strong Encryption**: Client-side AES-256-CFB encryption payload
  protection.
* **Compression**: Multiple compression algorithm support (zlib, bzip2,
  xz/lzma).
* **Automated Retention**: Policy-driven removal of expired backups.

Orchestration & Operations
--------------------------
* **Distributed Scheduler**: Orchestrator daemon managing multi-job
  scheduling and execution.
* **High Availability**: Clustered scheduler support with distributed
  coordination (tooz).
* **Multi-Node Job Sync**: Synchronized job execution across multiple
  compute nodes.
* **Web User Interface**: Native OpenStack Horizon dashboard plugin
  integration.
* **Hook Execution**: Custom pre-job and post-job script execution hooks.


Architecture Summary
====================

Freezer is structured around a 3-tier separation of concerns:

1. **Freezer Web UI**: OpenStack Horizon dashboard interface for job
   monitoring and configuration.
2. **Freezer API**: RESTful control plane API managing job schedules, client
   registrations, and metadata.
3. **Freezer Scheduler & Agent**: Client-side orchestrator daemon and
   stateless worker execution agent.

For full architectural diagrams, component interactions, and resource
tuning details, see :doc:`overview`.


Documentation
=============

.. toctree::
   :maxdepth: 2
   :caption: System Overview

   overview

.. toctree::
   :maxdepth: 2
   :caption: Installation Guides

   install/index

.. toctree::
   :maxdepth: 2
   :caption: User & CLI Guides

   user/index
   cli/index

.. toctree::
   :maxdepth: 2
   :caption: Administrator Guides

   admin/index
   admin/config

.. toctree::
   :maxdepth: 2
   :caption: Developer & Reference

   contributor/index
   reference/index
