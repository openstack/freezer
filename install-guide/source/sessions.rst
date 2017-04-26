.. _sessions:

Sessions
========

A session is a group of jobs which share the same scheduling time. A session is identified
by its **session_id** and has a numeric tag (**session_tag**) which is incremented each time that a new session
is started.
The purpose of the *session_tag* is that of identifying a group of jobs which have been executed
together and which therefore represent a snapshot of a distributed system.

When a job is added to a session, the scheduling time of the session is copied into the
job data structure, so that any job belonging to the same session will start at the same time.


Session Data Structure
----------------------

.. code-block:: none

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
    "time_start": int timestamp,
    "time_end": int timestamp,
    "time_started": int  (timestamp),
    "time_ended":   int  (timestamp),
    "status": string "completed" "running",
    "result": string "success" "fail",
    "user_id": string
  }

Session actions
---------------

When the freezer scheduler running on a node wants to start a session,
it sends a POST request to the following endpoint:

.. code-block::  none

    POST   /v1/sessions/{sessions_id}/action

The body of the request bears the action and parameters

Session START action
--------------------

.. code-block:: none

    {
        "start": {
            "job_id": "JOB_ID_HERE",
            "current_tag": 22
        }
    }

Example of a successful response

.. code-block:: none

    {
        'result': 'success',
        'session_tag': 23
    }

Session STOP action
-------------------

.. code-block:: none

    {
        "end": {
            "job_id": "JOB_ID_HERE",
            "current_tag": 23,
            "result": "success|fail"
        }
    }

Session-Job association
-----------------------

.. code-block:: rest

    PUT    /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
    DELETE /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
