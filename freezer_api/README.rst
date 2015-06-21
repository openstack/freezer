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


API registration
================
keystone user-create --name freezer --pass FREEZER_PWD
keystone user-role-add --user freezer --tenant service --role admin

keystone service-create --name freezer --type backup \
  --description "Freezer Backup Service"

keystone endpoint-create \
  --service-id $(keystone service-list | awk '/ backup / {print $2}') \
  --publicurl http://freezer_api_publicurl:port \
  --internalurl http://freezer_api_internalurl:port \
  --adminurl http://freezer_api_adminurl:port \
  --region regionOne


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

Freezer clients management
--------------------------
GET    /v1/clients(?limit,offset)       Lists registered clients
POST   /v1/clients                      Creates client entry

GET    /v1/clients/{freezerc_id}     Get client details
UPDATE /v1/clients/{freezerc_id}     Updates the specified client information
DELETE /v1/clients/{freezerc_id}     Deletes the specified client information

Freezer jobs management
-----------------------
GET    /v1/jobs(?limit,offset)     Lists registered jobs
POST   /v1/jobs                    Creates job entry

GET    /v1/jobs/{jobs_id}          Get job details
POST   /v1/jobs/{jobs_id}          creates or replaces a job entry using the specified job_id
UPDATE /v1/jobs/{jobs_id}          Updates the existing job information
DELETE /v1/jobs/{jobs_id}          Deletes the specified job information
PATCH  /v1/jobs/{jobs_id}          Updates part of the document

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


Freezer Client document structure
---------------------------------
Identifies a freezer client for the purpose of sending action

# client_info document contains information relevant for client identification
client_info:=
{
  "client_id": string   actually a concatenation "tenant-id_hostname"
  "hostname": string
  "description": string
  "config_id": string   # configuration in use by the client
}


# client_type document embeds the client_info and adds user_id
client_type :=
{
  "client" : client_info document,
  "user_id": string,    # owner of the information (OS X-User-Id, keystone provided, added by api)
}


Jobs
----
A job describes a single action to be executed by a freezer client, for example a backup, or a restore.
It contains the necessary information as if they were provided on the command line.

A job is stored in the api together with some metadata information such as:
job_id, user_id, client_id, status, scheduling information etc

Scheduling information enables future/recurrent execution of jobs

+---------------------+
| Job                 |
|                     |   job_action      +-------------------+
|  +job_id            +------------------>| job action dict   |
|  +client_id         |                   +-------------------+
|  +user_id           |
|  +description       |  job_schedule
|                     +---------------+
|                     |               |   +-------------------+
+---------------------+               +-->| job schedule dict |
                                          +-------------------+


job document structure:

"job": {
  "job_action":   { parameters for freezer to execute a specific action }
  "job_schedule": { scheduling information }
  "job_id":       string
  "client_id":    string
  "user_id":      string
  "description":  string
}

"job_action": {
{
  "action" :      string
  "mode" :        string
  "src_file" :    string
  "backup_name" : string
  "container" :   string
  ...
}

"job_schedule": {
  "time_created":    int  (timestamp)
  "time_started":    int  (timestamp)
  "time_ended":      int  (timestamp)
  "status":          string  ["stop", "scheduled", "running", "aborting", "removed"]
  "event":           string  ["", "stop", "start", "abort", "remove"]
  "result":          string  ["", "success", "fail", "aborted"]

  SCHEDULING TIME INFORMATION
}


Scheduling Time Information
---------------------------

Three types of scheduling can be identified:
  * date - used for single run jobs
  * interval - periodic jobs, providing an interval value
  * cron-like jobs

Each type has specific parameters which can be given.

date scheduling
---------------

  "schedule_date":      : datetime isoformat

interval scheduling
-------------------
  "schedule_interval"   : "continuous", "N weeks" / "N days" / "N hours" / "N minutes" / "N seconds"

  "schedule_start_date" : datetime isoformat
  "schedule_end_date"   : datetime isoformat

cron-like scheduling
--------------------

  "schedule_year"       : 4 digit year
  "schedule_month"      : 1-12
  "schedule_day"        : 1-31
  "schedule_week"       : 1-53
  "schedule_day_of_week": 0-6 or string mon,tue,wed,thu,fri,sat,sun
  "schedule_hour"       : 0-23
  "schedule_minute"     : 0-59
  "schedule_second"     : 0-59

  "schedule_start_date" : datetime isoformat
  "schedule_end_date"   : datetime isoformat



example backup job_action
"job_action": {
  "action" : "backup"
  "mode" : "fs"
  "src_file" : "/home/tylerdurden/project_mayhem"
  "backup_name" : "project_mayhem_backup"
  "container" : "my_backup_container"
  "max_backup_level" : int
  "always_backup_level": int
  "restart_always_backup": int
  "no_incremental" : bool
  "encrypt_pass_file" : private_key_file
  "log_file" : "/var/log/freezer.log"
  "hostname" : false
  "max_cpu_priority" : false
}

example restore job_action
"job_action": {
  "action": "restore"
  "restore-abs-path": "/home/tylerdurden/project_mayhem"
  "container" : "my_backup_container"
  "backup-name": "project_mayhem_backup"
  "restore-from-host": "another_host"
  "max_cpu_priority": true
}


example scheduled backup job
job will be executed once at the provided datetime

"job": {
  "job_action": {
      "action" : "backup",
      "mode" : "fs",
      "src_file" : "/home/tylerdurden/project_mayhem",
      "backup_name" : "project_mayhem_backup",
      "container" : "my_backup_container",
  }
  "job_schedule": {
    "time_created": 1234,
    "time_started": 1234,
    "time_ended":   0,
    "status":  "scheduled",
    "schedule_date": "2015-06-02T16:20:00"
  }
  "job_id": "blabla",
  "client_id": "blabla",
  "user_id": "blabla",
  "description": "scheduled one shot",
}


new job, in stop status, with pending start request
job will be executed daily at the provided hour:min:sec
while year,month,day are ignored, if provided

"job": {
  "job_action": {
      "action" : "backup"
      "mode" : "fs"
      "src_file" : "/home/tylerdurden/project_mayhem"
      "backup_name" : "project_mayhem_backup"
      "container" : "my_backup_container"
  },
  "job_schedule": {
    "time_created": 1234,
    "time_started": 1234,
    "time_ended":   0,
    "status":  "stop",
    "event": "start"
    "schedule_period" : "daily"
    "schedule_time": "2015-06-02T16:20:00"
  },
  "job_id": "blabla",
  "client_id": "blabla",
  "user_id": "blabla",
  "description": "daily backup",
}


multiple scheduling choices allowed
"job": {
  "job_action": {
      "action" : "backup"
      "mode" : "fs"
      "src_file" : "/home/tylerdurden/project_mayhem"
      "backup_name" : "project_mayhem_backup"
      "container" : "my_backup_container"
  }
  "job_schedule": {
    "time_created": 1234,
    "time_started": 1234,
    "time_ended":   0,
    "status":  "scheduled"
    "schedule_month" : "1-6, 9-12"
    "schedule_day" : "mon, wed, fri"
    "schedule_hour": "03"
    "schedule_minute": "25"
  }
  "job_id": "blabla",
  "client_id": "blabla",
  "user_id": "blabla",
  "description": "daily backup",
}


Finished job with result:
"job": {
  "job_action": {
      "action" : "backup"
      "mode" : "fs"
      "src_file" : "/home/tylerdurden/project_mayhem"
      "backup_name" : "project_mayhem_backup"
      "container" : "my_backup_container"
  },
  "job_schedule": {
    "time_created": 1234,
    "time_started": 1234,
    "time_ended":   4321,
    "status":  "stop",
    "event": "",
    "result": "success",
    "schedule_time": "2015-06-02T16:20:00"
  },
  "job_id": "blabla",
  "client_id": "blabla",
  "user_id": "blabla",
  "description": "one shot job",
}


Ini version:

[job]
job_id = 12344321
client_id = 12344321
user_id = qwerty
description = scheduled one shot

[job_action]
action = backup
mode = fs
src_file = /home/tylerdurden/project_mayhem
backup_name = project_mayhem_backup
container = my_backup_container

[job_schedule]
time_created = 1234
time_started = 1234
time_ended =
status = scheduled
schedule_time = 2015-06-02T16:20:00
