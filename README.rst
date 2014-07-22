=======
Freezer
=======

Freezer is a Python tool that helps you to automate the data backup and
restore process.

The following features are avaialble:

-  Backup your filesystem using snapshot to swift
-  Strong encryption supported: AES-256-CFB
-  Backup your file system tree directly (without volume snapshot)
-  Backup your journaled MongoDB directory tree using lvm snap to swift
-  Backup MySQL DB with lvm snapshot
-  Restore your data automatically from Swift to your file system
-  Low storage consumption as the backup are uploaded as a stream
-  Flexible Incremental backup policy
-  Data is archived in GNU Tar format
-  Data compression with gzip
-  Remove old backup automatically according the provided parameters

Requirements
============

-  OpenStack Swift Account (Auth V2 used)
-  python >= 2.6 (2.7 advised)
-  GNU Tar >= 1.26
-  gzip
-  OpenSSL
-  python-swiftclient >= 2.0.3
-  python-keystoneclient >= 0.8.0
-  pymongo >= 2.6.2 (if MongoDB backups will be executed)
-  At least 128 MB of memory reserved for freezer

Installation & Env Setup
========================

Install required packages
-------------------------

Ubuntu / Debian
---------------

Swift client and Keystone client::

    $ sudo apt-get install -y python-swiftclient python-keystoneclient

MongoDB backup::

    $ sudo apt-get install -y python-pymongo

MySQL backup::

    $ sudo apt-get install -y python-mysqldb

Freezer installation from Python package repo::

    $ sudo pip install freezer 

OR::

    $ sudo easy\_install freezer

The basic Swift account configuration is needed to use freezer. Make
sure python-swiftclient is installed.

Also the following ENV var are needed you can put them in ~/.bashrc::

    export OS_REGION_NAME=region-a.geo-1
    export OS_TENANT_ID=<account tenant>
    export OS_PASSWORD=<account password>
    export OS_AUTH_URL=https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0
    export OS_USERNAME=automationbackup
    export OS_TENANT_NAME=automationbackup

    $ source ~/.barshrc

Let's say you have a container called foobar-contaienr, by executing
"swift list" you should see something like::

    $ swift list
    foobar-container-2
    $

These are just use case example using Swift in the HP Cloud.

*Is strongly advised to use execute a backup using LVM snapshot, so
freezer will execute a backup on point-in-time data. This avoid risks of
data inconsistencies and corruption.*

Usage Example
=============

Backup
------

The most simple backup execution is a direct file system backup::

    $ sudo freezerc --file-to-backup /data/dir/to/backup
    --container new-data-backup --backup-name my-backup-name

By default --mode fs is set. The command would generate a compressed tar
gzip file of the directory /data/dir/to/backup. The generated file will
be segmented in stream and uploaded in the swift container called
new-data-backup, with backup name my-backup-name

Now check if your backup is executing correctly looking at
/var/log/freezer.log

Execute a MongoDB backup using lvm snapshot:

We need to check before on which volume group and logical volume our
mongo data is. These information can be obtained as per following::

    $ mount
    [...]

Once we know the volume where our mongo data is mounted on, we can get
the volume group and logical volume info::

    $ sudo vgdisplay
    [...]
    $ sudo lvdisplay
    [...]

We assume our mongo volume is "/dev/mongo/mongolv" and the volume group
is "mongo"::

    $ sudo freezerc --lvm-srcvol /dev/mongo/mongolv --lvm-dirmount /var/lib/snapshot-backup
    --lvm-volgroup mongo --file-to-backup /var/lib/snapshot-backup/mongod_ops2
    --container mongodb-backup-prod --exclude "*.lock" --mode mongo --backup-name mongod-ops2

Now freezerc create a lvm snapshot of the volume /dev/mongo/mongolv. If
no options are provided, default snapshot name is freezer\_backup\_snap.
The snap vol will be mounted automatically on /var/lib/snapshot-backup
and the backup meta and segments will be upload in the container
mongodb-backup-prod with the namemongod-ops2.

Execute a file system backup using lvm snapshot::

    $ sudo freezerc --lvm-srcvol /dev/jenkins/jenkins-home --lvm-dirmount
    /var/snapshot-backup --lvm-volgroup jenkins
    --file-to-backup /var/snapshot-backup --container jenkins-backup-prod
    --exclude "\*.lock" --mode fs --backup-name jenkins-ops2

MySQL backup require a basic configuration file. The following is an
example of the config::

    $ sudo cat /root/.freezer/db.conf
    host = your.mysql.host.ip
    user = backup 
    password = userpassword

Every listed option is mandatory. There's no need to stop the mysql
service before the backup execution.

Execute a MySQL backup using lvm snapshot::

    $ sudo freezerc --lvm-srcvol /dev/mysqlvg/mysqlvol 
    --lvm-dirmount /var/snapshot-backup
    --lvm-volgroup mysqlvg --file-to-backup /var/snapshot-backup
    --mysql-conf /root/.freezer/freezer-mysql.conf--container
    mysql-backup-prod --mode mysql --backup-name mysql-ops002

All the freezerc activities are logged into /var/log/freezer.log.

Restore
-------

As a general rule, when you execute a restore, the application that
write or read data should be stopped.

There are 3 main options that need to be set for data restore

File System Restore:

Execute a file system restore of the backup name
adminui.git::

    $ sudo freezerc --container foobar-container-2
    --backup-name adminui.git
    --restore-from-host git-HP-DL380-host-001 --restore-abs-path
    /home/git/repositories/adminui.git/
    --restore-from-date "23-05-2014T23:23:23"

MySQL restore:

Execute a MySQL restore of the backup name holly-mysql.
Let's stop mysql service first::

    $ sudo service mysql stop

Execute Restore::

    $ sudo freezerc --container foobar-container-2
    --backup-name mysq-prod --restore-from-host db-HP-DL380-host-001
    --restore-abs-path /var/lib/mysql --restore-from-date "23-05-2014T23:23:23"

And finally restart mysql::

    $ sudo service mysql start

Execute a MongoDB restore of the backup name mongobigdata::

    $ sudo freezerc --container foobar-container-2 --backup-name mongobigdata
     --restore-from-host db-HP-DL380-host-001 --restore-abs-path
    /var/lib/mongo --restore-from-date "23-05-2014T23:23:23"

Architecture
============

Freezer architecture is simple. The components are:

-  OpenStack Swift (the storage)
-  freezer client running on the node you want to execute the backups or
   restore

Frezeer use GNU Tar under the hood to execute incremental backup and
restore. When a key is provided, it uses OpenSSL to encrypt data
(AES-256-CFB)

Low resources requirement
-------------------------

Freezer is designed to reduce at the minimum I/O, CPU and Memory Usage.
This is achieved by generating a data stream from tar (for archiving)
and gzip (for compressing). Freezer segment the stream in a configurable
chunk size (with the option --max-seg-size). The default segment size is
128MB, so it can be safely stored in memory, encrypted if the key is
provided, and uploaded to Swift as segment.

Multiple segments are sequentially uploaded using the Swift Manifest.
All the segments are uploaded first, and then the Manifest file is
uploaded too, so the data segments cannot be accessed directly. This
ensue data consistency.

By keeping small segments in memory, I/O usage is reduced. Also as
there's no need to store locally the final compressed archive
(tar-gziped), no additional or dedicated storage is required for the
backup execution. The only additional storage needed is the LVM snapshot
size (set by default at 5GB). The lvm snapshot size can be set with the
option --lvm-snapsize. It is important to not specify a too small snap
size, because in case a quantity of data is being wrote to the source
volume and consequently the lvm snapshot is filled up, then the data is
corrupted.

If the more memory is available for the backup process, the maximum
segment size can be increased, this will speed up the process. Please
note, the segments must be smaller then 5GB, is that is the maximum
object size in the Swift server.

Au contraire, if a server have small memory availability, the
--max-seg-size option can be set to lower values. The unit of this
option is in bytes.

How the incremental works
-------------------------

The incremental backups is one of the most crucial feature. The
following basic logic happens when Freezer execute:

1) Freezer start the execution and check if the provided backup name for
   the current node already exist in Swift

2) If the backup exists, the Manifest file is retrieved. This is
   important as the Manifest file contains the information of the
   previous Freezer execution.

The following is what the Swift Manifest looks like::

    {
        'X-Object-Meta-Encrypt-Data': 'Yes',
        'X-Object-Meta-Segments-Size-Bytes': '134217728',
        'X-Object-Meta-Backup-Created-Timestamp': '1395734461',
        'X-Object-Meta-Remove-Backup-Older-Than-Days': '',
        'X-Object-Meta-Src-File-To-Backup': '/var/lib/snapshot-backup/mongod_dev-mongo-s1',
        'X-Object-Meta-Maximum-Backup-level': '0',
        'X-Object-Meta-Always-Backup-Level': '',
        'X-Object-Manifest': u'socorro-backup-dev_segments/dev-mongo-s1-r1_mongod_dev-mongo-s1_1395734461_0',
        'X-Object-Meta-Providers-List': 'HP',
        'X-Object-Meta-Backup-Current-Level': '0',
        'X-Object-Meta-Abs-File-Path': '',
        'X-Object-Meta-Backup-Name': 'mongod_dev-mongo-s1',
        'X-Object-Meta-Tar-Meta-Obj-Name': 'tar_metadata_dev-mongo-s1-r1_mongod_dev-mongo-s1_1395734461_0',
        'X-Object-Meta-Hostname': 'dev-mongo-s1-r1',
        'X-Object-Meta-Container-Segments': 'socorro-backup-dev_segments'
    }

3) The most relevant data taken in consideration for incremental are:

-  'X-Object-Meta-Maximum-Backup-level': '7'

Value set by the option: --max-level int

Assuming we are executing the backup daily, let's say managed from the
crontab, the first backup will start from Level 0, that is, a full
backup. At every daily execution, the current backup level will be
incremented by 1. Then current backup level is equal to the maximum
backup level, then the backup restart to level 0. That is, every week a
full backup will be executed.

-  'X-Object-Meta-Always-Backup-Level': ''

Value set by the option: --always-level int

When current level is equal to 'Always-Backup-Level', every next backup
will be executed to the specified level. Let's say --always-level is set
to 1, the first backup will be a level 0 (complete backup) and every
next execution will backup the data exactly from the where the level 0
ended. The main difference between Always-Backup-Level and
Maximum-Backup-level is that the counter level doesn't restart from
level 0

-  'X-Object-Manifest':
   u'socorro-backup-dev/dev-mongo-s1-r1\_mongod\_dev-mongo-s1\_1395734461\_0'

Through this meta data, we can identify the exact Manifest name of the
provided backup name. The syntax is:
container\_name/hostname\_backup\_name\_timestamp\_initiallevel

-  'X-Object-Meta-Providers-List': 'HP'

This option is NOT implemented yet The idea of Freezer is to support
every Cloud provider that provide Object Storage service using OpenStack
Swift. The meta data allows you to specify multiple provider and
therefore store your data in different Geographic location.

-  'X-Object-Meta-Backup-Current-Level': '0'

Record the current backup level. This is important as the value is
incremented by 1 in the next freezer execution.

-  'X-Object-Meta-Backup-Name': 'mongod\_dev-mongo-s1'

Value set by the option: -N BACKUP\_NAME, --backup-name BACKUP\_NAME The
option is used to identify the backup. It is a mandatory option and
fundamental to execute incremental backup. 'Meta-Backup-Name' and
'Meta-Hostname' are used to uniquely identify the current and next
incremental backups

-  'X-Object-Meta-Tar-Meta-Obj-Name':
   'tar\_metadata\_dev-mongo-s1-r1\_mongod\_dev-mongo-s1\_1395734461\_0'

Freezer use tar to execute incremental backup. What tar do is to store
in a meta data file the inode information of every file archived. Thus,
on the next Freezer execution, the tar meta data file is retrieved and
download from swift and it is used to generate the next backup level.
After the next level backup execution is terminated, the file update tar
meta data file will be uploaded and recorded in the Manifest file. The
naming convention used for this file is:
tar\_metadata\_backupname\_hostname\_timestamp\_backuplevel

-  'X-Object-Meta-Hostname': 'dev-mongo-s1-r1'

The hostname of the node where the Freezer perform the backup. This meta
data is important to identify a backup with a specific node, thus avoid
possible confusion and associate backup to the wrong node.
