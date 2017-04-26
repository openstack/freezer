.. _jobs:

Jobs
====

A job describes a single action to be executed by a freezer client, for example a backup, or a restore.
It contains the necessary information as if they were provided on the command line.

A job is stored in the api together with some metadata information such as:
job_id, user_id, client_id, status, scheduling information etc

Scheduling information enables future/recurrent execution of jobs

.. code-block:: none

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


job document structure

.. code-block:: none

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


Scheduling Time Information
---------------------------

Three types of scheduling can be identified

  * date - used for single run jobs
  * interval - periodic jobs, providing an interval value
  * cron-like jobs

Each type has specific parameters which can be given.

date scheduling
---------------

.. code-block:: none

  "schedule_date":      : datetime isoformat

interval scheduling
-------------------

.. code-block:: none

  "schedule_interval"   : "continuous", "N weeks" / "N days" / "N hours" / "N minutes" / "N seconds"

  "schedule_start_date" : datetime isoformat
  "schedule_end_date"   : datetime isoformat

cron-like scheduling
--------------------

.. code-block:: none

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

Job examples
------------

example backup freezer_action

.. code-block:: none

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

example restore freezer_action

.. code-block:: none

    "freezer_action": {
      "action": "restore"
      "restore-abs-path": "/home/tylerdurden/project_mayhem"
      "container" : "my_backup_container"
      "backup_name": "project_mayhem_backup"
      "restore-from-host": "another_host"
      "max_cpu_priority": true
    }


example scheduled backup job.
job will be executed once at the provided datetime

.. code-block:: none

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
                "schedule_interval" : "1 days"
                "schedule_start_date" : "2015-06-02T16:20:00"
            },
        "job_id": "4822e482fcbb439189a1ad616ac0a72f",
        "client_id": "26b4ea367ac64702868653912e9428cc_freezer.mydomain.myid",
        "user_id": "35a322dfb2b14f40bc53a29a14309021",
        "description": "daily backup",
    }


multiple scheduling choices allowed

.. code-block:: none

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


Finished job with result

.. code-block:: none

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


Actions default values
----------------------

It is possible to define properties that span across multiple actions
This allow not to rewrite values that might be the same in multiple actions.
If properties are specifically set in one action, then the specified value is the one used.

Example

.. code-block:: none

    "job": {
        "action_defaults": {
            "log_file": "/tmp/freezer_tmp_log",
            "container": "my_backup_container"
        },
        "job_actions": [{
            "freezer_action": {
                "action": "backup",
                "mode": "fs",
                "src_file": "/home/user1/file",
                "backup_name": "user1_backup"
            }
        }, {
            "freezer_action": {
                "action": "backup",
                "mode": "fs",
                "src_file": "/home/user2/file",
                "backup_name": "user2_backup"
            }
        }, {
            "freezer_action": {
                "action": "backup",
                "mode": "fs",
                "src_file": "/home/user3/file",
                "backup_name": "user2_backup",
                "log_file": "/home/user3/specific_log_file"
            }
        }],
        "description": "scheduled one shot"
    }


Is Equivalent to

.. code-block:: none

    "job": {
        "job_actions": [{
            "freezer_action": {
                "action": "backup",
                "mode": "fs",
                "src_file": "/home/user1/file",
                "backup_name": "user1_backup",
                "log_file": "/tmp/freezer_tmp_log",
                "container": "my_backup_container"
            }
        }, {
            "freezer_action": {
                "action": "backup",
                "mode": "fs",
                "src_file": "/home/user2/file",
                "backup_name": "user2_backup",
                "log_file": "/tmp/freezer_tmp_log",
                "container": "my_backup_container"
            }
        }, {
            "freezer_action": {
                "action": "backup",
                "mode": "fs",
                "src_file": "/home/user3/file",
                "backup_name": "user2_backup",
                "log_file": "/home/user3/specific_log_file",
                "container": "my_backup_container"
            }
        }],
        "description": "scheduled one shot"
    }
