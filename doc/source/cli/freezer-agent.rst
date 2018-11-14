=============
freezer-agent
=============

---------------------------------
backup and restore your resources
---------------------------------

:Author: openstack@lists.openstack.org
:Date:   2017-09-19
:Copyright: OpenStack Foundation
:Version: 1.0.0
:Manual section: 1
:Manual group: cloud backup and restore

SYNOPSIS
========

freezer-agent [<args>]

DESCRIPTION
===========

freezer-agent is being used to backup and restore cloud resources, It can also be used to perform admin operations on your backup like (remove old backups, list backups, ...). More information about OpenStack Freezer is at https://docs.openstack.org/freezer/latest/.

OPTIONS
=======
.. oslo.config:group:: DEFAULT

.. oslo.config:option:: debug

  :Type: boolean
  :Default: ``false``
  :Mutable: This option can be changed without restarting.

  If set to true, the logging level will be set to DEBUG instead of the default INFO level.


.. oslo.config:option:: log_config_append

  :Type: string
  :Default: ``<None>``
  :Mutable: This option can be changed without restarting.

  The name of a logging configuration file. This file is appended to any existing logging configuration files. For details about logging configuration files, see the Python logging module documentation. Note that when logging configuration files are used then all logging configuration is set in the configuration file and other logging configuration options are ignored (for example, logging_context_format_string).

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * log-config
     - * DEFAULT
       * log_config


.. oslo.config:option:: log_date_format

  :Type: string
  :Default: ``%Y-%m-%d %H:%M:%S``

  Defines the format string for %(asctime)s in log records. Default: the value above . This option is ignored if log_config_append is set.


.. oslo.config:option:: log_file

  :Type: string
  :Default: ``<None>``

  (Optional) Name of log file to send logging output to. If no default is set, logging will go to stderr as defined by use_stderr. This option is ignored if log_config_append is set.

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * logfile


.. oslo.config:option:: log_dir

  :Type: string
  :Default: ``<None>``

  (Optional) The base directory used for relative log_file  paths. This option is ignored if log_config_append is set.

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * logdir


.. oslo.config:option:: watch_log_file

  :Type: boolean
  :Default: ``false``

  Uses logging handler designed to watch file system. When log file is moved or removed this handler will open a new log file with specified path instantaneously. It makes sense only if log_file option is specified and Linux platform is used. This option is ignored if log_config_append is set.


.. oslo.config:option:: use_syslog

  :Type: boolean
  :Default: ``false``

  Use syslog for logging. Existing syslog format is DEPRECATED and will be changed later to honor RFC5424. This option is ignored if log_config_append is set.


.. oslo.config:option:: use_journal

  :Type: boolean
  :Default: ``false``

  Enable journald for logging. If running in a systemd environment you may wish to enable journal support. Doing so will use the journal native protocol which includes structured metadata in addition to log messages.This option is ignored if log_config_append is set.


.. oslo.config:option:: syslog_log_facility

  :Type: string
  :Default: ``LOG_USER``

  Syslog facility to receive log lines. This option is ignored if log_config_append is set.


.. oslo.config:option:: use_stderr

  :Type: boolean
  :Default: ``false``

  Log output to standard error. This option is ignored if log_config_append is set.


.. oslo.config:option:: logging_context_format_string

  :Type: string
  :Default: ``%(asctime)s.%(msecs)03d %(process)d %(levelname)s %(name)s [%(request_id)s %(user_identity)s] %(instance)s%(message)s``

  Format string to use for log messages with context.


.. oslo.config:option:: logging_default_format_string

  :Type: string
  :Default: ``%(asctime)s.%(msecs)03d %(process)d %(levelname)s %(name)s [-] %(instance)s%(message)s``

  Format string to use for log messages when context is undefined.


.. oslo.config:option:: logging_debug_format_suffix

  :Type: string
  :Default: ``%(funcName)s %(pathname)s:%(lineno)d``

  Additional data to append to log message when logging level for the message is DEBUG.


.. oslo.config:option:: logging_exception_prefix

  :Type: string
  :Default: ``%(asctime)s.%(msecs)03d %(process)d ERROR %(name)s %(instance)s``

  Prefix each line of exception output with this format.


.. oslo.config:option:: logging_user_identity_format

  :Type: string
  :Default: ``%(user)s %(tenant)s %(domain)s %(user_domain)s %(project_domain)s``

  Defines the format string for %(user_identity)s that is used in logging_context_format_string.


.. oslo.config:option:: default_log_levels

  :Type: list
  :Default: ``amqp=WARN,amqplib=WARN,boto=WARN,sqlalchemy=WARN,suds=INFO,oslo.messaging=INFO,oslo_messaging=INFO,iso8601=WARN,requests.packages.urllib3.connectionpool=WARN,urllib3.connectionpool=WARN,websocket=WARN,requests.packages.urllib3.util.retry=WARN,urllib3.util.retry=WARN,keystonemiddleware=WARN,routes.middleware=WARN,stevedore=WARN,taskflow=WARN,keystoneauth=WARN,oslo.cache=INFO,dogpile.core.dogpile=INFO``

  List of package logging levels in logger=LEVEL pairs. This option is ignored if log_config_append is set.


.. oslo.config:option:: publish_errors

  :Type: boolean
  :Default: ``false``

  Enables or disables publication of error events.


.. oslo.config:option:: instance_format

  :Type: string
  :Default: ``"[instance: %(uuid)s] "``

  The format for an instance that is passed with the log message.


.. oslo.config:option:: instance_uuid_format

  :Type: string
  :Default: ``"[instance: %(uuid)s] "``

  The format for an instance UUID that is passed with the log message.


.. oslo.config:option:: rate_limit_interval

  :Type: integer
  :Default: ``0``

  Interval, number of seconds, of log rate limiting.


.. oslo.config:option:: rate_limit_burst

  :Type: integer
  :Default: ``0``

  Maximum number of logged messages per rate_limit_interval.


.. oslo.config:option:: rate_limit_except_level

  :Type: string
  :Default: ``CRITICAL``

  Log level name used by rate limiting: CRITICAL, ERROR, INFO, WARNING, DEBUG or empty string. Logs with level greater or equal to rate_limit_except_level are not filtered. An empty string means that all levels are filtered.


.. oslo.config:option:: fatal_deprecations

  :Type: boolean
  :Default: ``false``

  Enables or disables fatal status of deprecations.


.. oslo.config:option:: action

  :Type: string
  :Default: ``<None>``
  :Valid Values: backup, restore, info, admin, exec

  Set the action to be taken. backup and restore are self explanatory, info is used to retrieve info from the storage media, exec is used to execute a script, while admin is used to delete old backups and other admin actions. Default backup.


.. oslo.config:option:: path_to_backup

  :Type: string
  :Default: ``<None>``

  The file or directory you want to back up to Swift


.. oslo.config:option:: backup_name

  :Type: string
  :Default: ``<None>``

  The backup name you want to use to identify your backup on Swift


.. oslo.config:option:: mode

  :Type: string
  :Default: ``fs``

  Set the technology to back from. Options are, fs (filesystem),mongo (MongoDB), mysql (MySQL), sqlserver(SQL Server), cinder(OpenStack Volume backup by freezer), cindernative(OpenStack native cinder-volume backup)nova(OpenStack Instance). Default set to fs


.. oslo.config:option:: engine_name

  :Type: string
  :Default: ``tar``
  :Valid Values: tar, rsync, rsyncv2, nova, osbrick

  Engine to be used for backup/restore. With tar, the file inode will be checked for changes amid backup execution. If the file inode changed, the whole file will be backed up. With rsync, the data blocks changes will be verified and only the changed blocks will be backed up. Tar is faster, but is uses more space and bandwidth. Rsync is slower, but uses less space and bandwidth. Nova engine can be used to backup/restore running instances. Backing up instances and it's metadata.


.. oslo.config:option:: container

  :Type: string
  :Default: ``freezer_backups``

  The Swift container (or path to local storage) used to upload files to


.. oslo.config:option:: snapshot

  :Type: string
  :Default: ``<None>``

  Create a snapshot of the fs containing the resource to backup. When used, the lvm parameters will be guessed and/or the  default values will be used, on windows it will invoke  vssadmin


.. oslo.config:option:: sync

  :Type: boolean
  :Default: ``true``

  Flush file system buffers. Force changed blocks to disk, update the super block. Default is True


.. oslo.config:option:: lvm_srcvol

  :Type: string
  :Default: ``<None>``

  Set the lvm volume you want to take a snapshot from. Default no volume


.. oslo.config:option:: lvm_snapname

  :Type: string
  :Default: ``<None>``

  Set the name of the snapshot that will be created. If not provided, a unique name will be generated.


.. oslo.config:option:: lvm_snapperm

  :Type: string
  :Default: ``ro``
  :Valid Values: ro, rw

  Set the lvm snapshot permission to use. If the permission is set to ro The snapshot will be immutable - read only -. If the permission is set to rw it will be mutable


.. oslo.config:option:: lvm_snapsize

  :Type: string
  :Default: ``1G``

  Set the lvm snapshot size when creating a new snapshot. Please add G for Gigabytes or M for Megabytes, i.e. 500M or 8G. It is also possible to use percentages as with the -l option of lvm, i.e. 80%FREE Default 1G.


.. oslo.config:option:: lvm_dirmount

  :Type: string
  :Default: ``<None>``

  Set the directory you want to mount the lvm snapshot to. If not provided, a unique directory will be generated in /var/lib/freezer


.. oslo.config:option:: lvm_volgroup

  :Type: string
  :Default: ``<None>``

  Specify the volume group of your logical volume. This is important to mount your snapshot volume. Default not set


.. oslo.config:option:: max_level

  :Type: integer
  :Default: ``False``

  Set the backup level used with tar to implement incremental backup. If a level 1 is specified but no level 0 is already available, a level 0 will be done and subsequently backs to level 1. Default 0 (No Incremental)


.. oslo.config:option:: always_level

  :Type: integer
  :Default: ``False``

  Set backup maximum level used with tar to implement incremental backup. If a level 3 is specified, the backup will be executed from level 0 to level 3 and to that point always a backup level 3 will be executed.  It will not restart from level 0. This option has precedence over --max-backup-level. Default False (Disabled)


.. oslo.config:option:: restart_always_level

  :Type: floating point
  :Default: ``False``

  Restart the backup from level 0 after n days. Valid only if --always-level option if set. If --always-level is used together with --remove-older-than, there might be the chance where the initial level 0 will be removed. Default False (Disabled)


.. oslo.config:option:: remove_older_than

  :Type: floating point
  :Default: ``<None>``

  Checks in the specified container for objects older than the specified days. If i.e. 30 is specified, it will remove the remote object older than 30 days. Default False (Disabled)


.. oslo.config:option:: remove_from_date

  :Type: string
  :Default: ``<None>``

  Checks the specified container and removes objects older than the provided datetime in the form 'YYYY-MM-DDThh:mm:ss' i.e. '1974-03-25T23:23:23'. Make sure the 'T' is between date and time


.. oslo.config:option:: no_incremental

  :Type: string
  :Default: ``<None>``

  Disable incremental feature. By default freezer build the meta data even for level 0 backup. By setting this option incremental meta data is not created at all. Default disabled


.. oslo.config:option:: hostname

  :Type: string
  :Default: ``<None>``

  Set hostname to execute actions. If you are executing freezer from one host but you want to delete objects belonging to another host then you can set this option that hostname and execute appropriate actions. Default current node hostname.


.. oslo.config:option:: mysql_conf

  :Type: string
  :Default: ``False``

  Set the MySQL configuration file where freezer retrieve important information as db_name, user, password, host, port. Following is an example of config file: # backup_mysql_confhost     = <db-host>user     = <mysqluser>password = <mysqlpass>port     = <db-port>


.. oslo.config:option:: metadata_out

  :Type: string
  :Default: ``<None>``

  Set the filename to which write the metadata regarding the backup metrics. Use '-' to output to standard output.


.. oslo.config:option:: exclude

  :Type: string
  :Default: ``<None>``

  Exclude files, given as a PATTERN.Ex: --exclude '\*.log' will exclude any file with name ending with .log. Default no exclude


.. oslo.config:option:: dereference_symlink

  :Type: string
  :Default: ``<None>``
  :Valid Values: <None>, soft, hard, all

  Follow hard and soft links and archive and dump the files they refer to. Default False.


.. oslo.config:option:: encrypt_pass_file

  :Type: string
  :Default: ``<None>``

  Passing a private key to this option, allow you to encrypt the files before to be uploaded in Swift. Default do not encrypt.


.. oslo.config:option:: max_segment_size

  :Type: integer
  :Default: ``33554432``

  Set the maximum file chunk size in bytes to upload to swift. Default 33554432 bytes (32MB)


.. oslo.config:option:: rsync_block_size

  :Type: integer
  :Default: ``4096``

  Set the data block size of used by rsync to generate signature. Default 4096 bytes (4K).


.. oslo.config:option:: restore_abs_path

  :Type: string
  :Default: ``<None>``

  Set the absolute path where you want your data restored. Default False.


.. oslo.config:option:: restore_from_date

  :Type: string
  :Default: ``<None>``

  Set the date of the backup from which you want to restore.This will select the most recent backup previous to the specified date (included). Example: if the last backup was created at '2016-03-22T14:29:01' and restore-from-date is set to '2016-03-22T14:29:01', the backup will be restored successfully. The same for any date after that, even if the provided date is in the future. However if restore-from-date is set to '2016-03-22T14:29:00' or before, that backup will not be found. Please provide datetime in format 'YYYY-MM-DDThh:mm:ss' i.e. '1979-10-03T23:23:23'. Make sure the 'T' is between date and time Default None.


.. oslo.config:option:: max_priority

  :Type: string
  :Default: ``<None>``

  Set the cpu process to the highest priority (i.e. -20 on Linux) and real-time for I/O. The process priority will be set only if nice and ionice are installed Default disabled. Use with caution.


.. oslo.config:option:: quiet

  :Type: boolean
  :Default: ``false``

  Suppress error messages


.. oslo.config:option:: insecure

  :Type: boolean
  :Default: ``false``

  Allow to access swift servers without checking SSL certs.


.. oslo.config:option:: os_identity_api_version

  :Type: string
  :Default: ``<None>``
  :Valid Values: 1, 2, 2.0, 3

  Openstack identity api version, can be 1, 2, 2.0 or 3

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * os-auth-ver
     - * DEFAULT
       * os_auth_ver


.. oslo.config:option:: proxy

  :Type: string
  :Default: ``<None>``

  Enforce proxy that alters system HTTP_PROXY and HTTPS_PROXY, use '' to eliminate all system proxies


.. oslo.config:option:: dry_run

  :Type: boolean
  :Default: ``false``

  Do everything except writing or removing objects


.. oslo.config:option:: upload_limit

  :Type: integer
  :Default: ``-1``

  Upload bandwidth limit in Bytes per sec. Can be invoked with dimensions (10K, 120M, 10G).


.. oslo.config:option:: download_limit

  :Type: integer
  :Default: ``-1``

  Download bandwidth limit in Bytes per sec. Can be invoked  with dimensions (10K, 120M, 10G).


.. oslo.config:option:: cinder_vol_id

  :Type: string
  :Default:

  Id of cinder volume for backup


.. oslo.config:option:: cinder_vol_name

  :Type: string
  :Default:

  Name of cinder volume for backup


.. oslo.config:option:: cinderbrick_vol_id

  :Type: string
  :Default:

  Id of cinder volume for backup using os-brick


.. oslo.config:option:: cindernative_vol_id

  :Type: string
  :Default:

  Id of cinder volume for native backup


.. oslo.config:option:: cindernative_backup_id

  :Type: string
  :Default: ``<None>``

  Id of the cindernative backup to be restored


.. oslo.config:option:: nova_inst_id

  :Type: string
  :Default:

  Id of nova instance for backup


.. oslo.config:option:: nova_inst_name

  :Type: string
  :Default:

  Name of nova instance for backup


.. oslo.config:option:: project_id

  :Type: string
  :Default: ``<None>``

  Id of project for backup


.. oslo.config:option:: sql_server_conf

  :Type: string
  :Default: ``False``

  Set the SQL Server configuration file where freezer retrieve the sql server instance. Following is an example of config file: instance = <db-instance>


.. oslo.config:option:: command

  :Type: string
  :Default: ``<None>``

  Command executed by exec action


.. oslo.config:option:: compression

  :Type: string
  :Default: ``gzip``
  :Valid Values: gzip, bzip2, xz

  Compression algorithm to use. Gzip is default algorithm


.. oslo.config:option:: storage

  :Type: string
  :Default: ``swift``
  :Valid Values: local, swift, ssh, s3

  Storage for backups. Can be Swift, Local, SSH and S3 now. Swift is default storage now. Local stores backups on the same defined path, swift will store files in container, and s3 will store files in bucket in S3 compatible storage.


.. oslo.config:option:: access_key

  :Type: string
  :Default:

  Access key for S3 compatible storage


.. oslo.config:option:: secret_key

  :Type: string
  :Default:

  Secret key for S3 compatible storage


.. oslo.config:option:: endpoint

  :Type: string
  :Default:

  Endpoint of S3 compatible storage


.. oslo.config:option:: ssh_key

  :Type: string
  :Default:

  Path to ssh-key for ssh storage only


.. oslo.config:option:: ssh_username

  :Type: string
  :Default:

  Remote username for ssh storage only


.. oslo.config:option:: ssh_host

  :Type: string
  :Default:

  Remote host for ssh storage only


.. oslo.config:option:: ssh_port

  :Type: integer
  :Default: ``22``

  Remote port for ssh storage only (default 22)


.. oslo.config:option:: config

  :Type: string
  :Default: ``<None>``

  Config file abs path. Option arguments are provided from config file. When config file is used any option from command line provided take precedence.


.. oslo.config:option:: overwrite

  :Type: boolean
  :Default: ``false``

  With overwrite removes files from restore path before restore.


.. oslo.config:option:: consistency_check

  :Type: boolean
  :Default: ``false``

  Compute the checksum of the fileset before backup. This checksum is stored as part of the backup metadata, which can be obtained either by using --metadata-out or through the freezer API. On restore, it is possible to verify for consistency. Please note this option is currently only available for file system backups. Please also note checking backup consistency is a resource intensive operation, so use it carefully!


.. oslo.config:option:: consistency_checksum

  :Type: string
  :Default: ``<None>``

  Compute the checksum of the restored file(s) and compare it to the (provided) checksum to verify that the backup was successful


.. oslo.config:option:: incremental

  :Type: boolean
  :Default: ``<None>``

  When the option is set, freezer will perform a cindernative incremental backup instead of the default full backup. And if True, but volume do not have a basefull backup, freezer will do a full backup first


.. oslo.config:option:: nova_restore_network

  :Type: string
  :Default: ``<None>``

  ID of the network to attach to the restored VM. In the case of a project containing multiple networks, it is necessary to provide the ID of the network to attach to the restored VM.


.. oslo.config:option:: timeout

  :Type: integer
  :Default: ``120``

  Timeout for the running operation. This option can be used with any operation running with freezer and after this time it will raise a TimeOut Exception. Default is 120


.. oslo.config:option:: fullbackup_rotation

  :Type: integer
  :Default: ``1``
  :Minimum Value: 1

  Keep the last N fullbackups of cinder-volume, the parameter should be greater than 0. If set action to admin and set the parameter, it should keep the last N fullbackups, other backups should be deleted


SEE ALSO
========

* `OpenStack Freezer <https://docs.openstack.org/freezer/latest/>`__

BUGS
====

* Freezer bugs are managed at Launchpad `Bugs : Freezer <https://bugs.launchpad.net/freezer>`__


