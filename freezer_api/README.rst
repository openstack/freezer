===========
Freezer API
===========


Installation
============

Install required packages
-------------------------
  # pip install keystonemiddleware falcon

Elasticsearch support::
  # pip install elasticsearch


Install freezer_api
-------------------
  # git clone https://github.com/stackforge/freezer.git
  # cd freezer/freezer_api && sudo python setup.py install

this will install into /usr/local


edit config file
----------------
  # sudo vi /etc/freezer-api.conf


run simple instance
-------------------
  # freezer-api


examples running using uwsgi
----------------------------
  # uwsgi --http :9090 --need-app --master --module freezer_api.cmd.api:application

  # uwsgi --https :9090,foobar.crt,foobar.key --need-app --master --module freezer_api.cmd.api:application


Concepts and definitions
========================

*hostname* is _probably_ going to be the host fqdn.

*backup_id*
defined as "container_hostname_backupname_timestamp_level" uniquely
identifies a backup

*backup_set*
defined as "container_hostname_backupname" identifies a group of related
backups which share the same container,hostname and backupname

*backup_session*
is a group of backups which share container,hostname and backupname, but
are also related by dependency.

*backup_session_id*
utilizes the timestamp of the first (level 0) backup in the session
It is identified by (container, hostname, backupname, timestamp-of-level-0)


API routes
==========

General
-------
GET /       List API version
GET /v1     JSON Home document, see http://tools.ietf.org/html/draft-nottingham-json-home-03

Backup metadata
---------------
GET    /v1/backups(?limit,marker)     Lists backups
POST   /v1/backups                    Creates backup entry

GET    /v1/backups/{backup_id}     Get backup details
UPDATE /v1/backups/{backup_id}     Updates the specified backup
DELETE /v1/backups/{backup_id}     Deletes the specified backup


Data Structures
===============

Backup metadata structure
-------------------------
NOTE: sizes are in MB

backup_metadata:=
{
  "container": string,
  "host_name": string,      # fqdn, client has to provide consistent information here !
  "backup_name": string,
  "timestamp": int,
  "level": int,
  "backup_session": int,
  "max_level": int,
  "mode" : string,            (fs mongo mysql)
  "fs_real_path": string,
  "vol_snap_path": string,
  "total_broken_links" : int,
  "total_fs_files" : int,
  "total_directories" : int,
  "backup_size_uncompressed" : int,
  "backup_size_compressed" : int,
  "total_backup_session_size" : int,
  "compression_alg": string,            (gzip bzip xz)
  "encrypted": bool,
  "client_os": string
  "broken_links" : [string, string, string],
  "excluded_files" : [string, string, string]
  "cli": string,         equivalent cli used when executing the backup ?
  "version": string
}


The api wraps backup_metadata dictionary with some additional information.
It stores and returns the information provided in this form:

{
  "backup_id": string         #  container_hostname_backupname_timestamp_level
  "user_id": string,          # owner of the backup metadata (OS X-User-Id, keystone provided)
  "user_name": string         # owner of the backup metadata (OS X-User-Name, keystone provided)

  "backup_metadata": {        #--- actual backup_metadata provided
    "container": string,
    "host_name": string,
    "backup_name": string,
    "timestamp": int,
    ...
  }
}
