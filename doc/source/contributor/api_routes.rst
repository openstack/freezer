API routes
==========

General
-------

.. code-block:: rest

    GET /       List API version
    GET /v1     JSON Home document, see https://tools.ietf.org/html/draft-nottingham-json-home-03, v1 API
    GET /v2     JSON Home document, v2 API

Backup metadata(v1)
-------------------

.. code-block:: rest

    GET    /v1/backups(?limit,offset)  Lists backups
    POST   /v1/backups                 Creates backup entry

    GET    /v1/backups/{backup_id}     Get backup details
    DELETE /v1/backups/{backup_id}     Deletes the specified backup

Freezer clients management(v1)
------------------------------

.. code-block:: rest

    GET    /v1/clients(?limit,offset)       Lists registered clients
    POST   /v1/clients                      Creates client entry

    GET    /v1/clients/{freezerc_id}     Get client details
    UPDATE /v1/clients/{freezerc_id}     Updates the specified client information
    DELETE /v1/clients/{freezerc_id}     Deletes the specified client information

Freezer jobs management(v1)
---------------------------

.. code-block:: rest

    GET    /v1/jobs(?limit,offset)     Lists registered jobs
    POST   /v1/jobs                    Creates job entry

    GET    /v1/jobs/{jobs_id}          Get job details
    POST   /v1/jobs/{jobs_id}          creates or replaces a job entry using the specified job_id
    DELETE /v1/jobs/{jobs_id}          Deletes the specified job information
    PATCH  /v1/jobs/{jobs_id}          Updates part of the document

Freezer actions management(v1)
------------------------------

.. code-block:: rest

    GET    /v1/actions(?limit,offset)  Lists registered action
    POST   /v1/actions                 Creates action entry

    GET    /v1/actions/{actions_id}    Get action details
    POST   /v1/actions/{actions_id}    creates or replaces a action entry using the specified action_id
    DELETE /v1/actions/{actions_id}    Deletes the specified action information
    PATCH  /v1/actions/{actions_id}    Updates part of the action document

Freezer sessions management(v1)
-------------------------------

.. code-block:: rest

    GET    /v1/sessions(?limit,offset)  Lists registered session
    POST   /v1/sessions                 Creates session entry

    GET    /v1/sessions/{sessions_id}    Get session details
    POST   /v1/sessions/{sessions_id}    creates or replaces a session entry using the specified session_id
    DELETE /v1/sessions/{sessions_id}    Deletes the specified session information
    PATCH  /v1/sessions/{sessions_id}    Updates part of the session document

    POST   /v1/sessions/{sessions_id}/action           requests actions (e.g. start/end) upon a specific session

    PUT    /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
    DELETE /v1/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session

Backup metadata(v2)
-------------------

.. code-block:: rest

    GET    /v2/{project_id}/backups(?limit,offset)  Lists backups
    POST   /v2/{project_id}/backups                 Creates backup entry

    GET    /v2/{project_id}/backups/{backup_id}     Get backup details
    DELETE /v2/{project_id}/backups/{backup_id}     Deletes the specified backup

Freezer clients management(v2)
------------------------------

.. code-block:: rest

    GET    /v2/{project_id}/clients(?limit,offset)       Lists registered clients
    POST   /v2/{project_id}/clients                      Creates client entry

    GET    /v2/{project_id}/clients/{freezerc_id}     Get client details
    UPDATE /v2/{project_id}/clients/{freezerc_id}     Updates the specified client information
    DELETE /v2/{project_id}/clients/{freezerc_id}     Deletes the specified client information

Freezer jobs management(v2)
---------------------------

.. code-block:: rest

    GET    /v2/{project_id}/jobs(?limit,offset)     Lists registered jobs
    POST   /v2/{project_id}/jobs                    Creates job entry

    GET    /v2/{project_id}/jobs/{jobs_id}          Get job details
    POST   /v2/{project_id}/jobs/{jobs_id}          creates or replaces a job entry using the specified job_id
    DELETE /v2/{project_id}/jobs/{jobs_id}          Deletes the specified job information
    PATCH  /v2/{project_id}/jobs/{jobs_id}          Updates part of the document

Freezer actions management(v2)
------------------------------

.. code-block:: rest

    GET    /v2/{project_id}/actions(?limit,offset)  Lists registered action
    POST   /v2/{project_id}/actions                 Creates action entry

    GET    /v2/{project_id}/actions/{actions_id}    Get action details
    POST   /v2/{project_id}/actions/{actions_id}    creates or replaces a action entry using the specified action_id
    DELETE /v2/{project_id}/actions/{actions_id}    Deletes the specified action information
    PATCH  /v2/{project_id}/actions/{actions_id}    Updates part of the action document

Freezer sessions management(v2)
-------------------------------

.. code-block:: rest

    GET    /v2/{project_id}/sessions(?limit,offset)  Lists registered session
    POST   /v2/{project_id}/sessions                 Creates session entry

    GET    /v2/{project_id}/sessions/{sessions_id}    Get session details
    POST   /v2/{project_id}/sessions/{sessions_id}    creates or replaces a session entry using the specified session_id
    DELETE /v2/{project_id}/sessions/{sessions_id}    Deletes the specified session information
    PATCH  /v2/{project_id}/sessions/{sessions_id}    Updates part of the session document

    POST   /v2/{project_id}/sessions/{sessions_id}/action           requests actions (e.g. start/end) upon a specific session

    PUT    /v2/{project_id}/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
    DELETE /v2/{project_id}/sessions/{sessions_id}/jobs/{job_id}    adds the job to the session
