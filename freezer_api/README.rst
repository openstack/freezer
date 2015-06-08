===========
Freezer API
===========


1. Installation
===============

1.1 Install required packages
-----------------------------
::

  # pip install keystonemiddleware falcon

Elasticsearch support
::

  # pip install elasticsearch


1.2 Install freezer_api
-----------------------
::

  # git clone https://github.com/stackforge/freezer.git
  # cd freezer/freezer_api && sudo python setup.py install

this will install into /usr/local


1.3 edit config file
--------------------
::

  # sudo vi /etc/freezer-api.conf


1.4 run simple instance
-----------------------
::

  # freezer-api


1.5 examples running using uwsgi
--------------------------------
::

  # uwsgi --http :9090 --need-app --master --module freezer_api.cmd.api:application

  # uwsgi --https :9090,foobar.crt,foobar.key --need-app --master --module freezer_api.cmd.api:application


2. Concepts and definitions
===========================

*hostname* is _probably_ going to be the host fqdn.

*backup_id*
defined as "container_hostname_backupname_timestamp_level" uniquely
identifies a backup

*backup_set*
defined as "container_hostname_backupname" identifies a group of related
backups which share the same container,hostname and backupname


3. API registration
===================
::

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


4. API routes
=============

General
-------
::

    GET /       List API version
    GET /v1     JSON Home document, see http://tools.ietf.org/html/draft-nottingham-json-home-03

Backup metadata
---------------
::

    GET    /v1/backups(?limit,marker)     Lists backups
    POST   /v1/backups                    Creates backup entry

    GET    /v1/backups/{backup_id}     Get backup details
    UPDATE /v1/backups/{backup_id}     Updates the specified backup
    DELETE /v1/backups/{backup_id}     Deletes the specified backup

Freezer clients management
--------------------------
::

    GET    /v1/clients(?limit,offset)       Lists registered clients
    POST   /v1/clients                      Creates client entry

    GET    /v1/clients/{freezerc_id}     Get client details
    UPDATE /v1/clients/{freezerc_id}     Updates the specified client information
    DELETE /v1/clients/{freezerc_id}     Deletes the specified client information

Freezer jobs management
-----------------------
::

    GET    /v1/jobs(?limit,offset)     Lists registered jobs
    POST   /v1/jobs                    Creates job entry

    GET    /v1/jobs/{jobs_id}          Get job details
    POST   /v1/jobs/{jobs_id}          creates or replaces a job entry using the specified job_id
    DELETE /v1/jobs/{jobs_id}          Deletes the specified job information
    PATCH  /v1/jobs/{jobs_id}          Updates part of the document

Freezer actions management
--------------------------
::

    GET    /v1/actions(?limit,offset)  Lists registered action
    POST   /v1/actions                 Creates action entry

    GET    /v1/actions/{actions_id}    Get action details
    POST   /v1/actions/{actions_id}    creates or replaces a action entry using the specified action_id
    DELETE /v1/actions/{actions_id}    Deletes the specified action information
    PATCH  /v1/actions/{actions_id}    Updates part of the action document

Freezer sessions management
---------------------------
::

    GET    /v1/sessions(?limit,offset)  Lists registered session
    POST   /v1/sessions                 Creates session entry

    GET    /v1/sessions/{sessions_id}    Get session details
    POST   /v1/sessions/{sessions_id}    creates or replaces a session entry using the specified session_id
    DELETE /v1/sessions/{sessions_id}    Deletes the specified session information
    PATCH  /v1/sessions/{sessions_id}    Updates part of the session document

    POST   /v1/sessions/{sessions_id}/action           requests actions (e.g. start/end) upon a specific session

    PUT    /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
    DELETE /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session

5. Backup metadata structure
============================
NOTE: sizes are in MB
::

    backup_metadata:=
    {
      "container": string,
      "host_name": string,      # fqdn, client has to provide consistent information here !
      "backup_name": string,
      "timestamp": int,
      "level": int,
      "max_level": int,
      "mode" : string,            (fs mongo mysql)
      "fs_real_path": string,
      "vol_snap_path": string,
      "total_broken_links" : int,
      "total_fs_files" : int,
      "total_directories" : int,
      "backup_size_uncompressed" : int,
      "backup_size_compressed" : int,
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

::

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


6. Freezer Client document structure
====================================

Identifies a freezer client for the purpose of sending action

client_info document contains information relevant for client identification::

    client_info:=
    {
      "client_id": string   actually a concatenation "tenant-id_hostname"
      "hostname": string
      "description": string
      "uuid":
    }


client_type document embeds the client_info and adds user_id::

    client_type :=
    {
      "client" : client_info document,
      "user_id": string,    # owner of the information (OS X-User-Id, keystone provided, added by api)
    }


7. Jobs
=======
A job describes a single action to be executed by a freezer client, for example a backup, or a restore.
It contains the necessary information as if they were provided on the command line.

A job is stored in the api together with some metadata information such as:
job_id, user_id, client_id, status, scheduling information etc

Scheduling information enables future/recurrent execution of jobs

::

    +---------------------+
    | Job                 |
    +---------------------+   job_actions   +--------------+
    |                     +---------------->|  job_action  |
    |  +job_id            | 0..*            +--------------+  freezer_action
    |  +client_id         |                 | +mandatory   |-------------+
    |  +user_id           |                 | +retries     |             |  +----------------+
    |  +description       |  job_schedule   +--------------+             +->| freezer_action |
    |                     +---------------+                                 +----------------+
    |                     |               |   +-------------------+
    +---------------------+               +-->| job schedule dict |
                                              +-------------------+


job document structure::

    "job": {
      "job_action":   { parameters for freezer to execute a specific action }
      "job_schedule": { scheduling information }
      "job_id":       string
      "client_id":    string
      "user_id":      string
      "description":  string
    }

    "job_actions":
        [
            {
                "freezer_action" :
                    {
                        "action" :      string
                        "mode" :        string
                        "src_file" :    string
                        "backup_name" : string
                        "container" :   string
                        ...
                    },
                "mandatory": False,
                "max_retries": 3,
                "max_retry_interval": 60
            },
            {
                "freezer_action" :
                    {
                        ...
                    },
                "mandatory": False,
                "max_retries": 3,
                "max_retry_interval": 60

            }
        ]

    "job_schedule": {
      "time_created":    int  (timestamp)
      "time_started":    int  (timestamp)
      "time_ended":      int  (timestamp)
      "status":          string  ["stop", "scheduled", "running", "aborting", "removed"]
      "event":           string  ["", "stop", "start", "abort", "remove"]
      "result":          string  ["", "success", "fail", "aborted"]

      SCHEDULING TIME INFORMATION
    }


7.1 Scheduling Time Information
-------------------------------

Three types of scheduling can be identified:
  * date - used for single run jobs
  * interval - periodic jobs, providing an interval value
  * cron-like jobs

Each type has specific parameters which can be given.

7.1.1 date scheduling
---------------------
::

  "schedule_date":      : datetime isoformat

7.1.2 interval scheduling
-------------------------
::

  "schedule_interval"   : "continuous", "N weeks" / "N days" / "N hours" / "N minutes" / "N seconds"

  "schedule_start_date" : datetime isoformat
  "schedule_end_date"   : datetime isoformat

7.1.3 cron-like scheduling
--------------------------
::

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

7.2 Job examples
----------------

example backup freezer_action::

    "freezer_action": {
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

example restore freezer_action::

    "freezer_action": {
      "action": "restore"
      "restore-abs-path": "/home/tylerdurden/project_mayhem"
      "container" : "my_backup_container"
      "backup-name": "project_mayhem_backup"
      "restore-from-host": "another_host"
      "max_cpu_priority": true
    }


example scheduled backup job.
job will be executed once at the provided datetime::

    "job": {
        "job_actions":
            [
                {
                    "freezer_action":
                        {
                            "action" : "backup",
                            "mode" : "fs",
                            "src_file" : "/home/tylerdurden/project_mayhem",
                            "backup_name" : "project_mayhem_backup",
                            "container" : "my_backup_container",
                        }
                    "exit_status": "fail|success"
                    "max_retries": int,
                    "max_retries_interval": secs,
                    "mandatory": bool
                },
                {
                    action
                    ...
                },
                {
                    action
                    ...
                }
            ],
        "job_schedule":
            {
                "time_created": 1234,
                "time_started": 1234,
                "time_ended":   0,
                "status":  "stop | scheduled | running",
                "schedule_date": "2015-06-02T16:20:00",
            }
        "job_id": "blabla",
        "client_id": "blabla",
        "user_id": "blabla",
        "description": "scheduled one shot",
    }


    "job": {
        "job_actions":
            [ ... ],
        "job_schedule":
            {
                "time_created": 1234,
                "time_started": 1234,
                "time_ended":   0,

                "status":  "stop",
                "event": "start"
                "schedule_interval" : "1 day"
                "schedule_start_date" : "2015-06-02T16:20:00"
            },
        "job_id": "blabla",
        "client_id": "blabla",
        "user_id": "blabla",
        "description": "daily backup",
    }


multiple scheduling choices allowed::

    "job": {
        "job_actions":
            [ ... ],
        "job_schedule":
            {
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


Finished job with result::

    "job": {
        "job_actions": [ ... ],
        "job_schedule":
            {
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



8 Actions
=========
Actions are stored only to facilitate the assembling of different actions into jobs in the web UI.
They are not directly used by the scheduler.
They are stored in this structure:
::

  {
      "freezer_action": {
        "action": string,
        "backup_name": string,
        ....
      },
      "mandatory": bool,
      "max_retries": int,
      "max_retries_interval": int

      "action_id": string,
      "user_id": string
  }


9. Sessions
===========
A session is a group of jobs which share the same scheduling time. A session is identified
by its **session_id** and has a numeric tag (**session_tag**) which is incremented each time that a new session
is started.
The purpose of the *session_tag* is that of identifying a group of jobs which have been executed
together and which therefore represent a snapshot of a distributed system.

When a job is added to a session, the scheduling time of the session is copied into the
job data structure, so that any job belonging to the same session will start at the same time.


9.1 Session Data Structure
--------------------------
::

  session =
  {
    "session_id": string,
    "session_tag": int,
    "description": string,
    "hold_off": int (seconds),
    "schedule": { scheduling information, same as jobs },
    "jobs": { 'job_id_1': {
                "client_id": string,
                "status": string,
                "result": string
                "time_started": int  (timestamp),
                "time_ended":   int  (timestamp),
              },
              'job_id_2': {
                "client_id": string,
                "status": string,
                "result": string
                "time_started": int  (timestamp),
                "time_ended":   int  (timestamp),
              }
            }
    "time_start": int timestam,
    "time_end": int timestam,
    "time_started": int  (timestamp),
    "time_ended":   int  (timestamp),
    "status": string "completed" "running",
    "result": string "success" "fail",
    "user_id": string
  }

9.2 Session actions
-------------------
When the freezer scheduler running on a node wants to start a session,
it sends a POST request to the following endpoint: ::

    POST   /v1/sessions/{sessions_id}/action

The body of the request bears the action and parameters

9.2.1 Session START action
--------------------------
::

    {
        "start": {
            "job_id": "JOB_ID_HERE",
            "current_tag": 22
        }
    }

Example of a succesfull response: ::

    {
        'result': 'success',
        'session_tag': 23
    }

8.2.2 Session STOP action
-------------------------
::

    {
        "end": {
            "job_id": "JOB_ID_HERE",
            "current_tag": 23,
            "result": "success|fail"
        }
    }

8.3 Session-Job association
---------------------------

    PUT    /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
    DELETE /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session

