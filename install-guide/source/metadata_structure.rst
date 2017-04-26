.. _metadata_structure:

Backup metadata structure
=========================

.. note::
   sizes are in MB

.. code-block::  none

    backup_metadata:=
    {
      "container": string,
      "host_name": string,      # fqdn, client has to provide consistent information here !
      "backup_name": string,
      "time_stamp": int,
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
It stores and returns the information provided in this form

.. code-block:: none

    {
      "backup_id": string         # backup UUID
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

