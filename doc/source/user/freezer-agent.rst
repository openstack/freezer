Agent User Guide
================

Before Start
------------

Freezer will automatically add prefix "freezer" to the container name,
where it is provided by the user and doesn't already start with this prefix.
If no container name is provided, the default is "freezer_backups".

The execution options can be set from the command line and/or config file in
ini format. There's an example of the job config file available in
freezer/freezer/specs/job-backup.conf.example.

Command line options always precedes options in config file.

Backup Options
==============

Freezer Agent can be used as standalone backup tool from command line.
In it is most simple form, you can run commands to backup your data to
OpenStack Swift, local directory or remote SSH.

Basic File System Backup
------------------------
Here is the most basic use example:

.. code:: bash
    
    # On Linux
    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \ 
    --container freezer_[new-data-to-backup] --backup-name [my-backup-name]
    
    # On Windows (need admin rights)
    freezer-agent --action backup --mode fs --backup-name [testwindows] \
    --path-to-backup "[C:\path\to\backup]" --container freezer_[new-windows-backup] \
    --log-file  [C:\path\to\log\freezer.log]
    
By default --mode fs is set. The command would generate a compressed tar gzip
file of the directory "/data/dir/to/backup". The generated file will be segmented
in stream and uploaded in the swift container called freezer_new-data-backup,
with backup name my-backup-name.

Now you can check /var/log/freezer.log file or in Windows
C:\path\to\log\freezer.log if your backup job finished successfully.

MongoDB Backup With LVM Snapshot
--------------------------------

If backed up system has LVM system, Freezer can use LVM Snapshot feature
to freezes the file system. This will prevent data corruption for volumes that
contains data bases.

First let's check where your MongoDB database files are located:

.. code:: bash
    
    mount -l
    [...]
    
Once we know the volume on which our Mongo data is mounted, we can get the
volume group and logical volume info:

.. code:: bash
    
    sudo vgdisplay
    [...]
    
    sudo lvdisplay
    [...]

Now let's start MongoDB backup with LVM Snapshot:

.. code:: bash

    sudo freezer-agent --lvm-srcvol [logical/volume/path] \
    --lvm-dirmount /var/lib/snapshot-backup \
    --lvm-volgroup [lvm-group-name] \
    --path-to-backup /var/lib/snapshot-backup/mongod_ops2 \
    --container freezer_[container-name-for-new-backup] \
    --exclude "*.lock" --mode mongo --backup-name [name-for-new-backup]
    
Now freezer-agent creates an LVM snapshot of the volume [logical/volume/path].
If no options are provided, the default snapshot name is
"freezer_backup_snap". The snapshot volume will be mounted automatically on 
/var/lib/snapshot-backup and the backup metadata and segments will be uploaded
in the container freezer_[container-name-for-new-backup] with the name [name-for-new-backup].

System Backup With LVM Snapshot
-------------------------------

Freezer can take full system backup with LVM Snapshot:

.. code:: bash

    sudo freezer-agent --lvm-srcvol [logical/volume/path] \
    --lvm-dirmount /var/snapshot-backup \
    --lvm-volgroup jenkins
    --path-to-backup /var/snapshot-backup \
    --container freezer_jenkins-backup-prod \
    --exclude "\*.lock" \
    --mode fs \
    --backup-name jenkins-ops2
    
MySQL Backup With LVM Snapshot
------------------------------

MySQL backup require a basic configuration file. The following is an example of the config.

Create following config file:

.. code:: bash
    
    sudo vi /root/.freezer/db.conf
    host = [your.mysql.host.ip]
    user = [mysql-user-name]
    password = [mysql-user-password]
    
Execute a MySQL backup using LVM Snapshot:

.. code:: bash
    
    sudo freezer-agent --lvm-srcvol /dev/mysqlvg/mysqlvol \
    --lvm-dirmount /var/snapshot-backup \
    --lvm-volgroup mysqlvg \
    --path-to-backup /var/snapshot-backup
    --mysql-conf /root/.freezer/freezer-mysql.conf \
    --container freezer_mysql-backup-prod \
    --mode mysql \
    --backup-name mysql-ops002

Cinder Backups
--------------

Cinder has its own mechanism for backups, and freezer supports it.
But it also allows creating a glance image from volume and uploading to swift.

To use standard cinder backups please provide --cindernative-vol-id argument.

To make a cinder backup you should provide cinder-vol-id or cindernative-vol-id
parameter in command line arguments. Freezer doesn't do any additional checks
and assumes that making a backup of that image will be sufficient to restore
your data in future.

Execute a cinder backup:

.. code:: bash
    
    freezer-agent --cinder-vol-id [cinder-volume-id]
    
Execute a MySQL backup with cinder:

.. code:: bash
    
    freezer-agent --mysql-conf /root/.freezer/freezer-mysql.conf \
    --container freezer_mysql-backup-prod \
    --mode mysql \
    --backup-name mysql-ops002 \
    --cinder-vol-id [cinder-volume-id]
    
Nova Backups
------------

If you provide nova argument in parameters, freezer assumes that all necessary
data is located on instance disk and it can be successfully stored using nova
snapshot mechanism.

For example if we want to store our mysql located on instance disk, we will
execute the same actions like in the case of lvm or tar snapshots, but we will
invoke nova snapshot instead of lvm or tar.

After that we will place snapshot to swift container as dynamic large object.

container/%instance_id%/%timestamp% <- large object with metadata
container_segments/%instance_id%/%timestamp%/segments...

Restore will create a snapshot from stored data and restore an instance from
this snapshot. Instance will have different id and old instance should be
terminated manually.

To make a nova backup you should provide a nova parameter in the arguments.
Freezer doesn't do any additional checks and assumes that making a backup 
of that instance will be sufficient to restore your data in future.

Execute a nova backup:

.. code:: bash

    freezer-agent --nova-inst-id [nova-instance-id]
    
Execute a MySQL backup with nova:

.. code:: bash

    freezer-agent --mysql-conf /root/.freezer/freezer-mysql.conf \
    --container freezer_mysql-backup-prod \
    --mode mysql \
    --backup-name mysql-ops002
    --nova-inst-id [nova-instance-id]
    
**Note: All the freezer-agent activities are logged into /var/log/freezer.log.**

    
Storage Options
===============

Freezer can use following storage technologies to backup the data:

- OpenStack Swift Object Storage
- Local Directory (Can be NFS mounted directory)
- SSH

Swift Object Storage Backup/Restore
-----------------------------------

Default storage option for Freezer is Swift. If you do not specify
"--storage" option Freezer will use Swift Object Storage.
"--storage swift" option can be specified in order to use Swift.

Backup example:

.. code:: bash
    
    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container freezer-[container] --backup-name [my-backup-name] \
    --storage swift
    
Restore example:

.. code:: bash

    sudo freezer-agent --action restore --restore-abs-path [/data/dir/to/backup]
    --container freezer-[container] [--backup-name my-backup-name]
    --storage swift

Local Storage Backup/Restore
----------------------------

Freezer can use local directory as target backup location. This directory can
be NFS,CIFS,SAMBA or other network file systems mounted directory.

To use local storage "--storage local" must be specified. And  
"--container %path-to-folder-with-backups%" option must be present.

Backup example:

.. code:: bash
    
    sudo freezer-agent --path-to-backup [/data/dir/to/backup]
    --container /tmp/my_backup_path/ [--backup-name my-backup-name]
    --storage local
    
Restore example:

.. code:: bash
    
    sudo freezer-agent --action restore \
    --restore-abs-path [/data/dir/to/backup]
    --container /tmp/my_backup_path/ \
    --backup-name [my-backup-name]
    --storage local

SSH Storage Backup/Restore
--------------------------

Freezer can user ssh to backup the data in fould on remote server. This option
will turn any Linux server to backup storage.

To use ssh storage specify "--storage ssh" And use "--container %path-to-folder-with-backups-on-remote-machine%"
Also you should specify ssh-username, ssh-key and ssh-host parameters. ssh-port is optional parameter, default is 22.

In order to use SSH to backup, "--storage ssh" and
"--container %path-to-folder-with-backups-on-remote-machine%" options must be
spesified. Also ssh-username, ssh-host parameters must be supplied.
ssh-port parameter is optional and Freezer use default 
ssh port 22 if not specified.

Backup example:

.. code:: bash

    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name
    --storage ssh --ssh-username [ssh-user-name] --ssh-key ~/.ssh/id_rsa
    --ssh-host 8.8.8.8
    
Restore example:

.. code:: bash

    sudo freezer-agent  --action restore \
    --restore-abs-pat [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name
    --storage ssh --ssh-username ubuntu --ssh-key ~/.ssh/id_rsa
    --ssh-host 8.8.8.8

Restore
=======

NOTES:

- As a general rule, when you execute a restore, the application that writes
  or reads data should be stopped.
- There are 3 main options that need to be set for data restore

File System Restore
-------------------

Following example shows how to restore backup named "adminui.git":

.. code:: bash
    
    sudo freezer-agent --action restore --container freezer_adminui_git
    --backup-name adminui.git
    --hostname [hostname-of-the-server] \
    --restore-abs-path /home/git/repositories/adminui.git/
    --restore-from-date "2014-05-23T23:23:23"
    
MySQL Restore
-------------

Execute a MySQL restore of the backup name holly-mysql.

Let's stop mysql service first:

.. code:: bash

    sudo service mysql stop
    
Execute restore:

.. code:: bash

    sudo freezer-agent --action restore \
    --container freezer_foobar-container-2 \
    --backup-name mysq-prod --hostname [server-host-name]
    --restore-abs-path /var/lib/mysql \
    --restore-from-date "2014-05-23T23:23:23"
    
Start MySQL:

.. code:: bash
    
    sudo service mysql start
    

MongoDB Restore
---------------

Execute a MongoDB restore of the backup name mongobigdata:

.. code:: bash
    
    sudo freezer-agent --action restore \
    --container freezer_foobar-container-2
    --backup-name mongobigdata \
    --hostname db-HP-DL380-host-001
    --restore-abs-path /var/lib/mongo \
    --restore-from-date "2014-05-23T23:23:23"

Cinder Restore
--------------

Cinder restore currently creates a volume with the contents of the saved one,
but doesn't implement deattach of existing volume and attach of the new
one to the vm.

You should implement these steps manually. To create a new volume from existing
content run next command:

.. code:: bash

    freezer-agent --action restore --cinder-inst-id [cinder-instance-id]
    
    freezer-agent --action restore --cindernative-vol-id [cinder-volume-id]
    
Nova Restore
------------

Nova restore currently creates an instance with the content of saved one,
but the ip address of the vm will be different as well as it's id.

Execute a nova restore:

.. code:: bash

    freezer-agent --action restore --nova-inst-id [nova-instance-id]
    
Local Storage Restore
---------------------

.. code:: bash

    sudo freezer-agent --action restore --container /local_backup_storage/ \
    --backup-name adminui.git \
    --hostname git-HP-DL380-host-001 \
    --restore-abs-path /home/git/repositories/adminui.git/ \
    --restore-from-date "2014-05-23T23:23:23" \
    --storage local

Parallel Backup
===============

Parallel backup can be executed only by config file. In config file
you should create n additional sections that start with "storage:"

Example:

.. code:: bash
    
    [storage:my_storage1], [storage:ssh], [storage:storage3]

Each storage section should have 'container' argument and all parameters
related to the storage.

Example:

.. code:: bash

    ssh-username, ssh-port
    
For swift storage you should provide additional parameter called 'osrc' Osrc
should be a path to file with Openstack Credentials like:

.. code:: bash

    unset OS_DOMAIN_NAME
    export OS_AUTH_URL=http://[keystone_url]:5000/v3
    export OS_PROJECT_NAME=[project_name]
    export OS_USERNAME=[username]
    export OS_PASSWORD=[password]
    export OS_PROJECT_DOMAIN_NAME=Default
    export OS_USER_DOMAIN_NAME=Default
    export OS_IDENTITY_API_VERSION=3
    export OS_AUTH_VERSION=3
    export OS_CACERT=/etc/ssl/certs/ca-certificates.crt
    export OS_ENDPOINT_TYPE=publicURL
    
Example of Config file for two local storages and one swift storage:

.. code:: bash

    [default]
    action = backup
    mode = fs
    path_to_backup = /foo/
    backup_name = mytest6
    always_level = 2
    max_segment_size = 67108864
    container = /tmp/backup/
    storage = local
    
    [storage:first]
    storage=local
    container = /tmp/backup1/
    
    [storage:second]
    storage=local
    container = /tmp/backup2/
    
    [storage:swift]
    storage=swift
    container = test
    osrc = openrc.osrc
    
Freezer Scheduler
=================

The freezer-scheduler is one of the two freezer components which is run on the
client nodes; the other one being the freezer-agent. It has a double role: it
is used both to start the scheduler process, and as a cli-tool which allows
the user to interact with the API.

The freezer-scheduler process can be started/stopped in daemon mode using the
usual positional arguments:

.. code:: bash

    freezer-scheduler start|stop
    
    
It can be also be started as a foreground process using the --no-daemon flag:

.. code:: bash

    freezer-scheduler --no-daemon start
    
This can be useful for testing purposes, when launched in a Docker container,
or by a babysitting process such as systemd.

The cli-tool version is used to manage the jobs in the API. A "job" is
basically a container; a document which contains one or more "actions".
An action contains the instructions for the freezer-agent. They are the same 
parameters that would be passed to the agent on the command line. 
For example: "backup_name", "path_to_backup", "max_level"

To sum it up, a job is a sequence of parameters that the scheduler pulls from 
the API and passes to a newly spawned freezer-agent process at the right time.

The scheduler understands the "scheduling" part of the job document, which it
uses to actually schedule the job, while the rest of the parameters are
substantially opaque.

It may also be useful to use the "-c" parameter to specify the client-id that
the scheduler will use when interacting with the API.

The purpose of the client-id is to associate a job with the scheduler instance
which is supposed to execute that job.

A single openstack user could manage different resources on different nodes
(and actually may even have different freezer-scheduler instances running on
the same node with different local privileges, for example), and the client-id 
allows him to associate the specific scheduler instance with its specific jobs.

When not provided with a custom client-id, the scheduler falls back to the 
default which is composed from the tenant-id and the hostname of the machine 
on which it is running.

The first step to use the scheduler is creating a document with the job:

.. code:: bash

    vi test_job.json

    {
      "job_actions": [
          {
              "freezer_action": {
                  "action": "backup",
                  "mode": "fs",
                  "backup_name": "backup1",
                  "path_to_backup": "/home/me/datadir",
                  "container": "schedule_backups",
                  "log_file": "/home/me/.freezer/freezer.log"
              },
              "max_retries": 3,
              "max_retries_interval": 60
          }
      ],
      "job_schedule": {
          "schedule_interval": "4 hours",
          "schedule_start_date": "2015-08-16T17:58:00"
      },
      "description": "schedule_backups 6"
    }
    
Then upload that job into the API:

.. code:: bash

    freezer-scheduler -c node12 job-create --file test_job.json
    
The newly created job can be found with:

.. code:: bash

    freezer-scheduler -c node12 job-list
    
Its content can be read with:

.. code:: bash

    freezer-scheduler -c node12 job-get -j [job_id]
    
The scheduler can be started on the target node with:

.. code:: bash

    freezer-scheduler -c node12 -i 15 -f ~/job_dir start
    
The scheduler could have already been started. As soon as the freezer-scheduler
contacts the API, it fetches the job and schedules it.

Freezer Agent Options
=====================

Available Options
-----------------

.. code:: bash

    usage: freezer-agent [-h] [--action ACTION] [--always-level ALWAYS_LEVEL]
                 [--backup-name BACKUP_NAME]
                 [--cinder-vol-id CINDER_VOL_ID]
                 [--cindernative-vol-id CINDERNATIVE_VOL_ID]
                 [--command COMMAND] [--compression COMPRESSION]
                 [--config CONFIG] [--config-dir DIR] [--config-file PATH]
                 [--container CONTAINER] [--debug]
                 [--dereference-symlink DEREFERENCE_SYMLINK]
                 [--download-limit DOWNLOAD_LIMIT] [--dry-run]
                 [--encrypt-pass-file ENCRYPT_PASS_FILE]
                 [--exclude EXCLUDE] [--hostname HOSTNAME] [--insecure]
                 [--log-config-append PATH]
                 [--log-date-format DATE_FORMAT] [--log-dir LOG_DIR]
                 [--log-file PATH] [--log-format FORMAT]
                 [--lvm-auto-snap LVM_AUTO_SNAP]
                 [--lvm-dirmount LVM_DIRMOUNT]
                 [--lvm-snap-perm LVM_SNAPPERM]
                 [--lvm-snapname LVM_SNAPNAME]
                 [--lvm-snapsize LVM_SNAPSIZE] [--lvm-srcvol LVM_SRCVOL]
                 [--lvm-volgroup LVM_VOLGROUP] [--max-level MAX_LEVEL]
                 [--max-priority MAX_PRIORITY]
                 [--max-segment-size MAX_SEGMENT_SIZE]
                 [--metadata-out METADATA_OUT] [--mode MODE]
                 [--mysql-conf MYSQL_CONF]
                 [--no-incremental NO_INCREMENTAL] [--nodebug]
                 [--nodry-run] [--noinsecure] [--nooverwrite] [--noquiet]
                 [--nouse-syslog] [--nouse-syslog-rfc-format]
                 [--nova-inst-id NOVA_INST_ID] [--noverbose]
                 [--nowatch-log-file]
                 [--os-identity-api-version OS_IDENTITY_API_VERSION]
                 [--overwrite] [--path-to-backup PATH_TO_BACKUP]
                 [--proxy PROXY] [--quiet]
                 [--remove-from-date REMOVE_FROM_DATE]
                 [--remove-older-than REMOVE_OLDER_THAN]
                 [--restart-always-level RESTART_ALWAYS_LEVEL]
                 [--restore-abs-path RESTORE_ABS_PATH]
                 [--restore-from-date RESTORE_FROM_DATE]
                 [--snapshot SNAPSHOT] [--sql-server-conf SQL_SERVER_CONF]
                 [--ssh-host SSH_HOST] [--ssh-key SSH_KEY]
                 [--ssh-port SSH_PORT] [--ssh-username SSH_USERNAME]
                 [--storage STORAGE]
                 [--syslog-log-facility SYSLOG_LOG_FACILITY]
                 [--upload-limit UPLOAD_LIMIT] [--use-syslog]
                 [--use-syslog-rfc-format] [--verbose] [--version]
                 [--watch-log-file]
                 
Optional Arguments
------------------

  -h, --help            show this help message and exit
  --action ACTION       Set the action to be taken. backup and restore are
                        self explanatory, info is used to retrieve info from
                        the storage media, exec is used to execute a script,
                        while admin is used to delete old backups and other
                        admin actions. Default backup.
  --always-level ALWAYS_LEVEL
                        Set backup maximum level used with tar to implement
                        incremental backup. If a level 3 is specified, the
                        backup will be executed from level 0 to level 3 and to
                        that point always a backup level 3 will be executed.
                        It will not restart from level 0. This option has
                        precedence over --max-backup-level. Default False
                        (Disabled)
  --backup-name BACKUP_NAME, -N BACKUP_NAME
                        The backup name you want to use to identify your
                        backup on Swift
  --cinder-vol-id CINDER_VOL_ID
                        Id of cinder volume for backup
  --cindernative-vol-id CINDERNATIVE_VOL_ID
                        Id of cinder volume for native backup
  --command COMMAND     Command executed by exec action
  --compression COMPRESSION
                        compression algorithm to use. gzip is default
                        algorithm
  --config CONFIG       Config file abs path. Option arguments are provided
                        from config file. When config file is used any option
                        from command line provided take precedence.
  --config-dir DIR      Path to a config directory to pull *.conf files from.
                        This file set is sorted, so as to provide a
                        predictable parse order if individual options are
                        over-ridden. The set is parsed after the file(s)
                        specified via previous --config-file, arguments hence
                        over-ridden options in the directory take precedence.
  --config-file PATH    Path to a config file to use. Multiple config files
                        can be specified, with values in later files taking
                        precedence. Defaults to None.
  --container CONTAINER, -C CONTAINER
                        The Swift container (or path to local storage) used to
                        upload files to
  --debug, -d           If set to true, the logging level will be set to DEBUG
                        instead of the default INFO level.
  --dereference-symlink DEREFERENCE_SYMLINK
                        Follow hard and soft links and archive and dump the
                        files they refer to. Default False.
  --download-limit DOWNLOAD_LIMIT
                        Download bandwidth limit in Bytes per sec. Can be
                        invoked with dimensions (10K, 120M, 10G).
  --dry-run             Do everything except writing or removing objects
  --encrypt-pass-file ENCRYPT_PASS_FILE
                        Passing a private key to this option, allow you to
                        encrypt the files before to be uploaded in Swift.
                        Default do not encrypt.
  --exclude EXCLUDE     Exclude files,given as a PATTERN.Ex: --exclude '*.log'
                        will exclude any file with name ending with .log.
                        Default no exclude
  --hostname HOSTNAME, --restore_from_host HOSTNAME
                        Set hostname to execute actions. If you are executing
                        freezer from one host but you want to delete objects
                        belonging to another host then you can set this option
                        that hostname and execute appropriate actions. Default
                        current node hostname.
  --insecure            Allow to access swift servers without checking SSL
                        certs.
  --log-config-append PATH, --log_config PATH
                        The name of a logging configuration file. This file is
                        appended to any existing logging configuration files.
                        For details about logging configuration files, see the
                        Python logging module documentation. Note that when
                        logging configuration files are used all logging
                        configuration is defined in the configuration file and
                        other logging configuration options are ignored (for
                        example, log_format).
  --log-date-format DATE_FORMAT
                        Defines the format string for %(asctime)s in log
                        records. Default: None . This option is ignored if
                        log_config_append is set.
  --log-dir LOG_DIR, --logdir LOG_DIR
                        (Optional) The base directory used for relative
                        log_file paths. This option is ignored if
                        log_config_append is set.
  --log-file PATH, --logfile PATH
                        (Optional) Name of log file to send logging output to.
                        If no default is set, logging will go to stderr as
                        defined by use_stderr. This option is ignored if
                        log_config_append is set.
  --log-format FORMAT   DEPRECATED. A logging.Formatter log message format
                        string which may use any of the available
                        logging.LogRecord attributes. This option is
                        deprecated. Please use logging_context_format_string
                        and logging_default_format_string instead. This option
                        is ignored if log_config_append is set.
  --lvm-auto-snap LVM_AUTO_SNAP
                        Automatically guess the volume group and volume name
                        for given PATH.
  --lvm-dirmount LVM_DIRMOUNT
                        Set the directory you want to mount the lvm snapshot
                        to. If not provided, a unique name will be generated
                        with thebasename /var/lib/freezer
  --lvm-snap-perm LVM_SNAPPERM
                        Set the lvm snapshot permission to use. If the
                        permission is set to ro The snapshot will be immutable
                        - read only -. If the permission is set to rw it will
                        be mutable
  --lvm-snapname LVM_SNAPNAME
                        Set the name of the snapshot that will be created. If
                        not provided, a unique name will be generated.
  --lvm-snapsize LVM_SNAPSIZE
                        Set the lvm snapshot size when creating a new
                        snapshot. Please add G for Gigabytes or M for
                        Megabytes, i.e. 500M or 8G. It is also possible to use
                        percentages as with the -l option of lvm, i.e. 80%FREE
                        Default 1G.
  --lvm-srcvol LVM_SRCVOL
                        Set the lvm volume you want to take a snaphost from.
                        Default no volume
  --lvm-volgroup LVM_VOLGROUP
                        Specify the volume group of your logical volume. This
                        is important to mount your snapshot volume. Default
                        not set
  --max-level MAX_LEVEL
                        Set the backup level used with tar to implement
                        incremental backup. If a level 1 is specified but no
                        level 0 is already available, a level 0 will be done
                        and subsequently backs to level 1. Default 0 (No
                        Incremental)
  --max-priority MAX_PRIORITY
                        Set the cpu process to the highest priority (i.e. -20
                        on Linux) and real-time for I/O. The process priority
                        will be set only if nice and ionice are installed
                        Default disabled. Use with caution.
  --max-segment-size MAX_SEGMENT_SIZE, -M MAX_SEGMENT_SIZE
                        Set the maximum file chunk size in bytes to upload to
                        swift Default 33554432 bytes (32MB)
  --metadata-out METADATA_OUT
                        Set the filename to which write the metadata regarding
                        the backup metrics. Use '-' to output to standard
                        output.
  --mode MODE, -m MODE  Set the technology to back from. Options are, fs
                        (filesystem),mongo (MongoDB), mysql (MySQL), sqlserver
                        (SQL Server) Default set to fs
  --mysql-conf MYSQL_CONF
                        Set the MySQL configuration file where freezer
                        retrieve important information as db_name, user,
                        password, host, port. Following is an example of
                        config file: # backup_mysql_confhost = <db-host>user =
                        <mysqluser>password = <mysqlpass>port = <db-port>
  --no-incremental NO_INCREMENTAL
                        Disable incremental feature. By default freezer build
                        the meta data even for level 0 backup. By setting this
                        option incremental meta data is not created at all.
                        Default disabled
  --nodebug             The inverse of --debug
  --nodry-run           The inverse of --dry-run
  --noinsecure          The inverse of --insecure
  --nooverwrite         The inverse of --overwrite
  --noquiet             The inverse of --quiet
  --nouse-syslog        The inverse of --use-syslog
  --nouse-syslog-rfc-format
                        The inverse of --use-syslog-rfc-format
  --nova-inst-id NOVA_INST_ID
                        Id of nova instance for backup
  --noverbose           The inverse of --verbose
  --nowatch-log-file    The inverse of --watch-log-file
  --os-identity-api-version OS_IDENTITY_API_VERSION, --os_auth_ver OS_IDENTITY_API_VERSION
                        Openstack identity api version, can be 1, 2, 2.0 or 3
  --overwrite           With overwrite removes files from restore path before
                        restore.
  --path-to-backup PATH_TO_BACKUP, -F PATH_TO_BACKUP
                        The file or directory you want to back up to Swift
  --proxy PROXY         Enforce proxy that alters system HTTP_PROXY and
                        HTTPS_PROXY, use '' to eliminate all system proxies
  --quiet, -q           Suppress error messages
  --remove-from-date REMOVE_FROM_DATE
                        Checks the specified container and removes objects
                        older than the provided datetime in the form 'YYYY-MM-
                        DDThh:mm:ss' i.e. '1974-03-25T23:23:23'. Make sure the
                        'T' is between date and time
  --remove-older-than REMOVE_OLDER_THAN, -R REMOVE_OLDER_THAN
                        Checks in the specified container for object older
                        than the specified days. If i.e. 30 is specified, it
                        will remove the remote object older than 30 days.
                        Default False (Disabled) The option --remove-older-
                        then is deprecated and will be removed soon
  --restart-always-level RESTART_ALWAYS_LEVEL
                        Restart the backup from level 0 after n days. Valid
                        only if --always-level option if set. If --always-
                        level is used together with --remove-older-then, there
                        might be the chance where the initial level 0 will be
                        removed. Default False (Disabled)
  --restore-abs-path RESTORE_ABS_PATH
                        Set the absolute path where you want your data
                        restored. Default False.
  --restore-from-date RESTORE_FROM_DATE
                        Set the date of the backup from which you want to
                        restore.This will select the most recent backup
                        previous to the specified date (included). Example: if
                        the last backup was created at '2016-03-22T14:29:01'
                        and restore-from-date is set to '2016-03-22T14:29:01',
                        the backup will be restored successfully. The same for
                        any date after that, even if the provided date is in
                        the future. However if restore-from-date is set to
                        '2016-03-22T14:29:00' or before, that backup will not
                        be found. Please provide datetime in format 'YYYY-MM-
                        DDThh:mm:ss' i.e. '1979-10-03T23:23:23'. Make sure the
                        'T' is between date and time Default None.
  --snapshot SNAPSHOT, -s SNAPSHOT
                        Create a snapshot of the fs containing the resource to
                        backup. When used, the lvm parameters will be guessed
                        and/or the default values will be used, on windows it
                        will invoke vssadmin
  --sql-server-conf SQL_SERVER_CONF
                        Set the SQL Server configuration file where freezer
                        retrieve the sql server instance. Following is an
                        example of config file: instance = <db-instance>
  --ssh-host SSH_HOST   Remote host for ssh storage only
  --ssh-key SSH_KEY     Path to ssh-key for ssh storage only
  --ssh-port SSH_PORT   Remote port for ssh storage only (default 22)
  --ssh-username SSH_USERNAME
                        Remote username for ssh storage only
  --storage STORAGE     Storage for backups. Can be Swift or Local now. Swift
                        is default storage now. Local stores backups on the
                        same defined path and swift will store files in
                        container.
  --syslog-log-facility SYSLOG_LOG_FACILITY
                        Syslog facility to receive log lines. This option is
                        ignored if log_config_append is set.
  --upload-limit UPLOAD_LIMIT
                        Upload bandwidth limit in Bytes per sec. Can be
                        invoked with dimensions (10K, 120M, 10G).
  --use-syslog          Use syslog for logging. Existing syslog format is
                        DEPRECATED and will be changed later to honor RFC5424.
                        This option is ignored if log_config_append is set.
  --use-syslog-rfc-format
                        Enables or disables syslog rfc5424 format for logging.
                        If enabled, prefixes the MSG part of the syslog
                        message with APP-NAME (RFC5424). This option is
                        ignored if log_config_append is set.
  --verbose, -v         If set to false, the logging level will be set to
                        WARNING instead of the default INFO level.
  --version             show program's version number and exit
  --watch-log-file      Uses logging handler designed to watch file system.
                        When log file is moved or removed this handler will
                        open a new log file with specified path
                        instantaneously. It makes sense only if log_file
                        option is specified and Linux platform is used. This
                        option is ignored if log_config_append is set.
                        
MISC
====

Scheduler
---------

To get an updated sample of freezer-scheduler configuration you the following command:

.. code:: bash

    oslo-config-generator --config-file config-generator/scheduler.conf
    
Update sample file will be generated in etc/scheduler.conf.sample

Agent
-----

To list options available in freezer-agent use the following command:

.. code:: bash

    oslo-config-generator --namespace freezer --namespace oslo.log
    
this will print all options to the screen you direct the output to a file if you want:

.. code:: bash

    oslo-config-generator --namespace freezer --namespace oslo.log --output-file etc/agent.conf.sample

Dependencies Notes
------------------

In stable/kilo and stable/liberty the module peppep3134daemon is imported from
local path rather than pip. This generated many issues as the package is not 
in the global-requirements.txt of kilo and liberty. Also pbr in the kilo
release does not support env markers which further complicated the installation.

Copyright
---------

The Freezer logo is released under the licence Attribution 3.0 Unported (CC BY3.0).