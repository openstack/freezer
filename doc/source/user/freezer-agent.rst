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
In its most simple form, you can run commands to backup your data to
OpenStack Swift, local directory, remote SSH(SFTP) or S3 compatible storage
or remote FTP or FTPS storage.

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
    --lvm-volgroup jenkins \
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
    --path-to-backup /var/snapshot-backup \
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

    freezer-agent --mode cinder --cinder-vol-id [cinder-volume-id]

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

    freezer-agent --backup-name [my-backup-name] \
    --mode nova --engine nova \
    --no-incremental True \
    --nova-inst-id [nova-instance-id]

Execute a MySQL backup with nova:

.. code:: bash

    freezer-agent --mysql-conf /root/.freezer/freezer-mysql.conf \
    --container freezer_mysql-backup-prod \
    --mode mysql \
    --backup-name mysql-ops002 \
    --nova-inst-id [nova-instance-id]

**Note: All the freezer-agent activities are logged into /var/log/freezer.log.**


Storage Options
===============

Freezer can use following storage technologies to backup the data:

- OpenStack Swift Object Storage
- Local Directory (Can be NFS mounted directory)
- SSH(SFTP)(Can be mounted without password(ssh-key) or with password)

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

    sudo freezer-agent --action restore --restore-abs-path [/data/dir/to/backup] \
    --container freezer-[container] --backup-name [my-backup-name] \
    --storage swift

Local Storage Backup/Restore
----------------------------

Freezer can use local directory as target backup location. This directory can
be NFS,CIFS,SAMBA or other network file systems mounted directory.

To use local storage "--storage local" must be specified. And
"--container %path-to-folder-with-backups%" option must be present.

Backup example:

.. code:: bash

    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container /tmp/my_backup_path/ --backup-name [my-backup-name] \
    --storage local

Restore example:

.. code:: bash

    sudo freezer-agent --action restore \
    --restore-abs-path [/data/dir/to/backup] \
    --container /tmp/my_backup_path/ \
    --backup-name [my-backup-name] \
    --storage local

SSH(SFTP) Storage Backup/Restore
--------------------------------

Freezer can use SSH(SFTP) to backup the data to remote server. This
option will turn any Linux server to backup storage.

To use SSH(SFTP) storage specify "--storage ssh" And
use "--container %path-to-folder-with-backups-on-remote-machine%"
Also you should specify ssh-username, ssh-key(or ssh-password) and ssh-host
parameters.
ssh-port is an optional parameter, default is 22.

In order to use SSH to backup, "--storage ssh" and
"--container %path-to-folder-with-backups-on-remote-machine%" options must be
specified. Also ssh-username, ssh-host parameters must be supplied.
ssh-port parameter is optional and Freezer use default
ssh port 22 if not specified.

Backup example1 (without password(ssh-key)):

.. code:: bash

    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ssh --ssh-username [ssh-user-name] --ssh-key ~/.ssh/id_rsa \
    --ssh-host 8.8.8.8

Restore example1 (without password(ssh-key)):

.. code:: bash

    sudo freezer-agent  --action restore \
    --restore-abs-path [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ssh --ssh-username ubuntu --ssh-key ~/.ssh/id_rsa \
    --ssh-host 8.8.8.8

Backup example2 (with password):

.. code:: bash

    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ssh --ssh-username [ssh-user-name] --ssh-password passwd_test \
    --ssh-host 8.8.8.8

Restore example2 (with password):

.. code:: bash

    sudo freezer-agent  --action restore \
    --restore-abs-path [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ssh --ssh-username ubuntu --ssh-password passwd_test \
    --ssh-host 8.8.8.8

FTP Storage Backup/Restore
--------------------------

Freezer can use FTP to backup the data to remote server. This option
will turn any FTP server to backup storage.

To use FTP storage specify "--storage ftp" And use "--container %path-to-folder-with-backups-on-remote-machine%"
Also you should specify ftp-username, ftp-password and ftp-host parameters. ftp-port is optional parameter, default is 21.

In order to use FTP to backup, "--storage ftp" and
"--container %path-to-folder-with-backups-on-remote-machine%" options must be
specified. Also ftp-username, ftp-password, ftp-host parameters must be supplied.
ftp-port parameter is optional and Freezer use default
ssh port 21 if not specified.

Backup example:

.. code:: bash

    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ftp --ftp-username [ftp-user-name] \
    --ftp-password [ftp-user-password] \
    --ftp-host 8.8.8.8 \
    --ftp-port 21

Restore example:

.. code:: bash

    sudo freezer-agent  --action restore \
    --restore-abs-pat [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ftp \
    --ftp-username [ftp-user-name] \
    --ftp-password [ftp-user-password] \
    --ftp-host 8.8.8.8
    --ftp-port 21

FTPS Storage Backup/Restore
---------------------------

Freezer can use FTPS to backup the data to remote server. This option
will turn any FTPS server to backup storage.

To use FTPS storage specify "--storage ftps" And use "--container %path-to-folder-with-backups-on-remote-machine%"
Also you should specify ftp-username, ftp-password and ftp-host parameters. ftp-port is optional parameter, default is 21.

In order to use FTPS to backup, "--storage ftps" and
"--container %path-to-folder-with-backups-on-remote-machine%" options must be
specified. Also ftp-username, ftp-password, ftp-host parameters must be supplied.
ftp-port parameter is optional and Freezer use default
ssh port 21 if not specified.

Backup example:

.. code:: bash

    sudo freezer-agent --path-to-backup [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ftps \
    --ftp-username [ftp-user-name] \
    --ftp-password [ftp-user-password] \
    --ftp-host 8.8.8.8 \
    --ftp-port 21

Restore example:

.. code:: bash

    sudo freezer-agent  --action restore \
    --restore-abs-pat [/data/dir/to/backup] \
    --container /remote-machine-path/ \
    --backup-name my-backup-name \
    --storage ftps \
    --ftp-username [ftp-user-name] \
    --ftp-password [ftp-user-password] \
    --ftp-host 8.8.8.8
    --ftp-port 21

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

    sudo freezer-agent --action restore --container freezer_adminui_git \
    --backup-name adminui.git \
    --hostname [hostname-of-the-server] \
    --restore-abs-path /home/git/repositories/adminui.git/ \
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
    --backup-name mysql-prod --hostname [server-host-name] \
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
    --container freezer_foobar-container-2 \
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

    freezer-agent --action restore --cinder-vol-id [cinder-volume-id]

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
should be a path to file with OpenStack Credentials like:

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

    freezer job-create --client node12 --file test_job.json

The newly created job can be found with:

.. code:: bash

    freezer job-list --client node12

Its content can be read with:

.. code:: bash

    freezer job-get [job_id]

The scheduler can be started on the target node with:

.. code:: bash

    freezer-scheduler -c node12 -i 15 -f ~/job_dir start

The scheduler could have already been started. As soon as the freezer-scheduler
contacts the API, it fetches the job and schedules it.

MISC
====

Scheduler
---------

To get an updated sample of freezer-scheduler configuration you the following command:

.. code:: bash

    oslo-config-generator --config-file etc/config-generator.conf

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
