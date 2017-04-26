======================================
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

*hostname* is _probably_ going to be the host fqdn.

*backup_id*
defined as UUID of a backup


``freezer-api`` service
  Accepts and responds to end user API calls...
