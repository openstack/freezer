**************
Freezer API v1
**************

1. API versions
===============

=========  ==========  ===============================================
Method     URI         Description
=========  ==========  ===============================================
GET        /           List information about freezer API versions
=========  ==========  ===============================================


1.1 Request
-----------
This operation does not accept a body

1.2 Response
------------

Example

::

  {
    "versions": [
      {
         "id": "1",
         "links": [
            {
                "href": "/v1/",
                "rel": "self"
            }
         ],
         "status": "CURRENT",
         "updated": "2015-03-23T13:45:00"
      }
    ]
  }


2. API doc home
===============

=========  ==========  ===============================================
Method     URI         Description
=========  ==========  ===============================================
GET        /v1         Provides information about how to interact
                       with the freezer API server
=========  ==========  ===============================================

2.1 Request
-----------
This operation does not accept a body

2.2 Response
------------

Example

::

 {
     }
     "resources": {
         "rel/backups": {
             "hints": {
                "allow": [
                    "GET"
                ],
                "formats": {
                    "application/json": {}
                }
             },
             "href-template": "/v1/backups/{backup_id}",
             "href-vars": {
                "backup_id": "param/backup_id"
             }
         }
     }
 }


3. Backups
==========

=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
POST     /v1/backups                  creates a backup entry in the API storage
-------  ---------------------------  -----------------------------------------------
GET      /v1/backups{?limit,offset}   List backup information
-------  ---------------------------  -----------------------------------------------
GET      /v1/backups/{backup_id}      Get details for a specific backup
-------  ---------------------------  -----------------------------------------------
DELETE   /v1/backups/{backup_id}      Deletes the specific backup information
=======  ===========================  ===============================================


3.1 Create backup information entry
-----------------------------------

=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
POST     /v1/backups                  creates a backup entry in the API storage
=======  ===========================  ===============================================

Normal response codes: 201

3.1.1 Request
-------------

Example. Uploading backup metadata

::

    {
        "backup_name": "important_data_backup",
        "backup_session": 12344311,
        "backup_size_compressed": 1212,
        "backup_size_uncompressed": 1212,
        "client_os": "linux",
        "compression_alg": "None",
        "container": "freezer_container",
        "encrypted": "false",
        "fs_real_path": "/blabla",
        "host_name": "alpha",
        "level": 0,
        "max_level": 5,
        "mode": "fs",
        "timestamp": 123444311,
        "total_backup_session_size": 1212,
        "total_broken_links": 0,
        "total_directories": 2,
        "total_fs_files": 11,
    "vol_snap_path": "/blablasnap"
    }

3.1.2 Response
Example

::

    {
        "backup_id": "freezer_container_alpha_important_data_backup_123444324_1"
    }

3.2 List backup information
---------------------------
=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
GET      /v1/backups{?limit,offset}   List backup information
=======  ===========================  ===============================================

Normal response codes:200

3.2.1 Request
-------------

This operation does not accept a bode

3.2.2 Response
--------------
Example

::

  {
    "backups": [
        {
            "backup_id":
            "freezer_container_alpha_important_data_backup_123444324_1",
            "backup_metadata": {
                "backup_name": "important_data_backup",
                "backup_session": 12344321,
                "backup_size_compressed": 1212,
                "backup_size_uncompressed": 1212,
                "client_os": "linux",
                "compression_alg": "None",
                "container": "freezer_container",
                "encrypted": "false",
                "fs_real_path": "/blabla",
                "host_name": "alpha",
                "level": 1,
                "max_level": 5,
                "mode": "fs",
                "timestamp": 123444324,
                "total_backup_session_size": 1212,
                "total_broken_links": 0,
                "total_directories": 2,
                "total_fs_files": 11,
                "vol_snap_path": "/blablasnap"
            }
        },
        {
            "backup_id":
            "freezer_container_alpha_important_data_backup_123444311_0",
            "backup_metadata": {
                "backup_name": "important_data_backup",
                "backup_session": 12344311,
                "backup_size_compressed": 1212,
                "backup_size_uncompressed": 1212,
                "client_os": "linux",
                "compression_alg": "None",
                "container": "freezer_container",
                "encrypted": "false",
                "fs_real_path": "/blabla",
                "host_name": "alpha",
                "level": 0,
                "max_level": 5,
                "mode": "fs",
                "timestamp": 123444311,
                "total_backup_session_size": 1212,
            }
        }
    ]
    "total_broken_links": 0,
    "total_directories": 2,
    "total_fs_files": 11,
    "vol_snap_path": "/blablasnap"
  }

3.3 Get backup details
----------------------
=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
GET      /v1/backups/{backup_id}      Get details for a specific backup
=======  ===========================  ===============================================

Normal response codes: 200

3.3.1 Request
-------------
This operation does not accept a body

3.3.2 Response
--------------
Example

::


  {
    "backup_id": "freezer_container_alpha_important_data_backup_123444311_0",
    "backup_metadata": {
        "backup_name": "important_data_backup",
        "backup_session": 12344311,
        "backup_size_compressed": 1212,
        "backup_size_uncompressed": 1212,
        "client_os": "linux",
        "compression_alg": "None",
        "container": "freezer_container",
        "encrypted": "false",
        "fs_real_path": "/blabla",
        "host_name": "alpha",
        "level": 0,
        "max_level": 5,
        "mode": "fs",
        "timestamp": 123444311,
        "total_backup_session_size": 1212,
        "total_broken_links": 0,
        "total_directories": 2,
        "total_fs_files": 11,
        "vol_snap_path": "/blablasnap"
    }
  }

3.4 Delete backup information
-----------------------------
=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
DELETE   /v1/backups/{backup_id}      Deletes the specific backup information
=======  ===========================  ===============================================

Normal response codes: 204

3.4.1 Request
-------------
This operation does not accept a body

3.4.2 Response
--------------
This operation does not return a body

4 Clients
=========

=======  ===========================  ===============================================
Method   URI                          Description
=======  ===========================  ===============================================
GET      /v1/clients(?limit,offset)   Lists registered clients
-------  ---------------------------  -----------------------------------------------
GET      /v1/clients/{client_id}      Get client details
-------  ---------------------------  -----------------------------------------------
POST     /v1/clients                  Creates client entry
-------  ---------------------------  -----------------------------------------------
DELETE   /v1/clients/{freezerc_id}    Deletes the specified client information
=======  ===========================  ===============================================

4.1 List registered clients
---------------------------
=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
GET      /v1/clients(?limit,offset)   Lists registered clients
=======  ===========================  ===============================================

4.1.1 Request
-------------
This operation does not accept a body

4.1.2 Response
--------------
Example

::

  {
    "clients":
        [
            {
                "client":
                    {
                        "hostname": "my-workstation",
                        "description": "my simple freezer client description",
                        "client_id": "5c869f05e23149e4bf18639f2dd96380_vannif-HP-Z420-Workstation"
                    },
                "user_id": "fe93b43c374247c38b456c08041e6765"
            },
            {
                "client":
                    {
                        "hostname": "another-node",
                        "description": "my second workstation",
                        "client_id": "5c869f05e23149e4bf18639f2dd96380_another-node"
                    },
                "user_id": "fe93b43c374247c38b456c08041e6765"
            }
        ]
  }

4.2 Get client details
----------------------
=======  ===========================  ===============================================
Method     URI                        Description
=======  ===========================  ===============================================
GET      /v1/clients/{client_id}      Get client details
=======  ===========================  ===============================================

4.2.1 Request
-------------
This operation does not accept a body

4.2.2 Response
--------------
Example

::

  {
    u'client': {
        u'client_id': u'5c869f05e23149e4bf18639f2dd96380_my-workstation',
        u'description': u'my simple freezer client description',
        u'hostname': u'my-workstation',
    },
    u'user_id': u'fe93b43c374247c38b456c08041e6765',
  }

4.3 Creates client entry
------------------------
=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
POST     /v1/clients                  Creates client entry
=======  ===========================  ===============================================

4.3.1 Request
-------------

::

  {
     "hostname": "my-workstation",
     "description": "my simple freezer client description",
     "client_id": "5c869f05e23149e4bf18639f2dd96380_my-workstation"
  }

4.3.2 Response
--------------

::

  {
    "client_id": "5c869f05e23149e4bf18639f2dd96380_my-workstation"
  }


4.4 Deletes the specified client information
--------------------------------------------
=======  ===========================  ===============================================
Method     URI                           Description
=======  ===========================  ===============================================
DELETE   /v1/clients/{client_id}      Deletes the specified client information
=======  ===========================  ===============================================

4.4.1 Request
-------------
This operation does not accept a body

4.4.2 Response
--------------
This operation does not return a body

5 Jobs
======

=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
GET      /v1/jobs(?limit,offset)     Lists registered jobs
-------  --------------------------  -----------------------------------------------
GET      /v1/jobs/{jobs_id}          Get job details
-------  --------------------------  -----------------------------------------------
POST     /v1/jobs                    Creates job entry
-------  --------------------------  -----------------------------------------------
POST     /v1/jobs/{jobs_id}          creates or replaces a job entry
                                     using the specified job_id
-------  --------------------------  -----------------------------------------------
DELETE   /v1/jobs/{jobs_id}          Deletes the specified job information
-------  --------------------------  -----------------------------------------------
PATCH    /v1/jobs/{jobs_id}          Updates part of the document
=======  ==========================  ===============================================

5.1 Lists registered jobs
-------------------------
=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
GET      /v1/jobs(?limit,offset)     Lists registered jobs
=======  ==========================  ===============================================

5.1.1 Request
-------------
Example

::

  {
    "match": [
        {
            "client_id": "5c869f05e23149e4bf18639f2dd96380_my-workstation"
        }
    ]
  }

5.1.2 Response
--------------
Example

::

  {
    "jobs": [
        {
            u'client_id': u'5c869f05e23149e4bf18639f2dd96380_my-workstation',
            u'job_action': {
                u'action': u'backup',
                u'backup_name': u'workday_backup_of_my_work_stuff',
                u'container': u'my_backups',
                u'max_level': u'4',
                u'path_to_backup': u'/home/me/work_stuff',
            },
            u'job_id': u'685eab6e3a2744b6bce789fe7e71d6e7',
            u'job_schedule': {
                u'schedule_day_of_week': u'tue,wed,thu,fri,sat',
                u'schedule_hour': u'03',
                u'schedule_minute': u'20',
                u'time_created': 1435064743,
                u'time_ended': -1,
                u'time_started': -1,
            },
            u'user_id': u'fe93b43c374247c38b456c08041e6765',
        },
        {
            u'client_id': u'5c869f05e23149e4bf18639f2dd96380_my-workstation',
            u'job_action': {
                u'action': u'backup',
                u'backup_name': u'daily_backup_my_documents',
                u'container': u'my_backups',
                u'max_level': u'7',
                u'path_to_backup': u'/home/me/my_documents',
            },
            u'job_id': u'a4ff2f1937864470b8f35e69c59454fa',
            u'job_schedule': {
                u'schedule_interval': u'1 days',
                u'schedule_start_date': u'2015-06-02T03:20:00',
                u'time_created': 1435064743,
                u'time_ended': -1,
                u'time_started': -1,
            },
            u'user_id': u'fe93b43c374247c38b456c08041e6765',
        }
    ]
  }

5.2 Get job details
-------------------
=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
GET      /v1/jobs/{jobs_id}          Get job details
=======  ==========================  ===============================================

5.2.1 Request
-------------
This operation does not accept a body

5.2.2 Response
--------------
Example

::

    {
        u'client_id': u'5c869f05e23149e4bf18639f2dd96380_my-workstation',
        u'job_id': u'685eab6e3a2744b6bce789fe7e71d6e7',
        u'user_id': u'fe93b43c374247c38b456c08041e6765',
        u'job_action': {
            u'action': u'backup',
            u'backup_name': u'workday_backup_of_my_work_stuff',
            u'container': u'my_backups',
            u'max_level': u'4',
            u'path_to_backup': u'/home/me/work_stuff',
        },
        u'job_schedule': {
            u'schedule_day_of_week': u'tue,wed,thu,fri,sat',
            u'schedule_hour': u'03',
            u'schedule_minute': u'20',
            u'time_created': 1435064743,
            u'time_ended': -1,
            u'time_started': -1,
        }
    }

5.3 Creates job entry
---------------------
=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
POST     /v1/jobs                    Creates job entry
=======  ==========================  ===============================================

5.3.1 Request
-------------

::

    {
        u'client_id': u'5c869f05e23149e4bf18639f2dd96380_my-workstation',
        u'job_action': {
            u'action': u'backup',
            u'backup_name': u'workday_backup_of_my_work_stuff',
            u'container': u'my_backups',
            u'max_level': u'4',
            u'path_to_backup': u'/home/me/work_stuff',
        },
        u'job_schedule': {
            u'schedule_day_of_week': u'tue,wed,thu,fri,sat',
            u'schedule_hour': u'03',
            u'schedule_minute': u'20',
        },
    }

5.3.2 Response
--------------
Example

::

    {
        "job_id": "685eab6e3a2744b6bce789fe7e71d6e7"
    }

5.4 Creates or replaces a job entry
-----------------------------------
=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
POST     /v1/jobs/{jobs_id}          creates or replaces a job entry
                                     using the specified job_id
=======  ==========================  ===============================================

5.4.1 Request
-------------

::

    {
        u'client_id': u'5c869f05e23149e4bf18639f2dd96380_my-workstation',
        u'job_action': {
            u'action': u'backup',
            u'backup_name': u'workday_backup_of_my_work_stuff',
            u'container': u'my_backups',
            u'max_level': u'4',
            u'path_to_backup': u'/home/me/work_stuff',
        },
        u'job_schedule': {
            u'schedule_day_of_week': u'tue,wed,thu,fri,sat',
            u'schedule_hour': u'03',
            u'schedule_minute': u'20',
        },
    }



5.4.2 Response
--------------

::

    {
        "job_id": "685eab6e3a2744b6bce789fe7e71d6e7",
        "version": "3"
    }


5.5 Deletes the specified job information
-----------------------------------------
=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
DELETE   /v1/jobs/{jobs_id}          Deletes the specified job information
=======  ==========================  ===============================================

5.5.1 Request
-------------
This operation does not accept a body

5.5.2 Response
--------------
This operation does not return a body

5.6 Updates part of the document
--------------------------------
=======  ==========================  ===============================================
Method     URI                           Description
=======  ==========================  ===============================================
PATCH    /v1/jobs/{jobs_id}          Updates part of the document
=======  ==========================  ===============================================

5.6.1 Request
-------------

::

    {
        "job_schedule":
            {
                "event": "start"
            }
    }


5.6.2 Response
--------------

::

    {
        "job_id": "923b9d436bca41d79007fe14bd103ed1",
        "version": 3
    }


