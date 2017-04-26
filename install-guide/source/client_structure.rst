.. _client_structure:

Freezer Client document structure
=================================

Identifies a freezer client for the purpose of sending action

client_info document contains information relevant for client identification

.. code-block:: none

    client_info:
    {
      "client_id": string   actually a concatenation "tenant-id_hostname"
      "hostname": string
      "description": string
      "uuid":
    }


client_type document embeds the client_info and adds user_id

.. code-block:: none

    client_type :
    {
      "client" : client_info document,
      "user_id": string,    # owner of the information (OS X-User-Id, keystone provided, added by api)
    }
