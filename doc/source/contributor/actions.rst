Actions
=======

Actions are stored only to facilitate the assembling of different actions into jobs in the web UI.
They are not directly used by the scheduler.
They are stored in this structure

.. code-block:: none


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

