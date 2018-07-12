Backup/Restore and DR service overview
======================================
The Backup/Restore and DR service provides an easy way to backup and restore
 your OpenStack workloads to different storage.

The Backup and restore service consists of the following components:
 - freezer-api
 - freezer-agent
 - freezer-scheduler

The Disaster Recovery service consists of the following components:
 - freezer-dr

The service features a RESTful API, which can be used to maintain the status of
your jobs, backups and metadata.

This chapter assumes a working setup of OpenStack following the base
Installation Guide.


Concepts and definitions
========================


``freezer-api`` service
  Accepts and responds to end user API calls...


``freezer-scheduler`` service
  Does API calls to ``freezer-api`` to schedule, fetch, update or Delete backup
  jobs.


``freezer-agent`` service
  Python application run on the same node like ``freezer-scheduler`` and it
  gets called by ``freezer-scheduler`` to execute backups/restore operations.


``freezer-dr`` service
  Independent service from all other freezer services. It runs on the control
  plane to do disaster recovery in case of any compute node failed (more to
  follow)

*hostname* is _probably_ going to be the host fqdn.

*backup_id* defined as UUID of a backup.
