===
FAQ
===

1)  **What is freezer?**
    Is a tool to automate data backup and restore
    process using OpenStack Swift and/or other media storage.

2)  **Does freezer support incremental backup?**
    Yes. Incremental backup are done using GNU tar incremental features.

3)  **Does freezer check the file contents to establish if a file was modified?**
    Freezer check for changes at mtime and ctime in
    every file inode to evaluate if a file changed or not.

4)  **Why GNU tar rather than rsync?**
    Both approaches are good. Rsync check
    the file content, while tar check the file inode. In our
    environment, we need to backup directories with size > 400GB and
    hundreds of thousands of files. Rsync approach is effective but slow.
    Tar is fast as it needs to check only the file inodes, rather than
    the full file content. Rsync backup type will be added pretty soon.

5)  *Does freezer support encrypted backup?*
    Yes. Freezer encrypt data using OpenSSL (AES-256-CFB).

6)  **Does freezer execute point-in-time backup?**
    Yes. For point in time backup LVM snapshot feature used.

7)  **Can I use freezer on OSX or other OS where GNU Tar is not installed
    by default?**
    Yes. For OSX and \*BSD, just install gtar and freezer
    automatically will use gtar to execute backup. OS other then Linux,
    OSX and \*BSD are currently not supported.

8)  **What Application backup does freezer support currently?**
    MongoDB, MySQL to have a higher level of data consistency, while
    any application is supported for crash consistent data integrity.

9)  **How does the MongoDB backup happens?**
    Freezer required journal enabled in Mongo and lvm volume to execute backup.
    It checks if the Mongo instance is the master and create lvm snapshot to have
    consistent data.

10) **Does freezer manage sparse files efficiently?**
    Yes. Zeroed/null data is not backed up. So less space and bandwidth will be used.

11) **Does freezer remove automatically backup after some time?**
    Yes. From command line the option --remove-older-than (days) can be used to
    remove objects older then (days).

12) **Does freezer support MySQL Backup?**
    Yes.

13) **What storage media are currently supported?**
    Current support media storage are:
    a. Swift
    b. Store files on a remote host file system using ssh
    c. Directory in the local host (i.e. NFS/CIFS mounted volumes)

14) **Does freezer has any Web UI or API?**
    Yes. Freezer has REST API and a Web UI integrated with Horizon.

15) **Does Freezer detect removed files between incremental executions?**
    Yes.

16) **Will Freezer be included as official project in OpenStack?**
    We hope so, as soon as we can.

17) **Does freezer support Windows?**
    Yes. The freezer agent and scheduler can be executed on Windows.

18) **What is being used on Windows to execute file system snapshots?**
    Currently VSS are used to support point in time snapshots.

19) **What applications are supported in Windows for  consistent backups?**
    SQL Server (--mode sqlserver).

20) **Are there examples of OpenStack projects that use Freezer that I can look at?**
    Not currently.

21) **My service has it's own task scheduler. What is the recommended way to schedule Freezer runs?**
    If you want to use the freezer-api and freezer-web-ui in horizon, you need to use the
    freezer-scheduler.
    If you do not need the api and web ui, you can just execute the freezer-agent from crontab or
    any other scheduler.

22) **What are the benefits of using the API and Web UI?**
    - You can start backup and restore jobs on any node from the Web UI
    - Backup jobs can be synchronized across multiple nodes
    - The UI provides metrics and other info

23) **How can I run user-defined scripts before and after a backup run?**
    A simple solution is to implement your own script locally and execute
    freezer-agent from it.
    We recommend instead creating "exec"-type jobs in the UI and set up job
    dependencies.

24) **What are the options for backing up MySQL/Percona?**
    a. Make use of filesystem snapshots (LVM) using the "--mode mysql" option.  It's supported
    natively by Freezer and suitable for large databases.
        This instructs freezer to execute the following steps:
        - flush tables and lock the DB
        - take an LVM snapshot
        - release the DB (so it's usable again very quiclky)
        - backup the consistent DB image from the snapshot
        - release the snapshot
    b. Manual process - It does not require LVM and provides incremental backup.
        - manually flush tables and lock the DB: "flush tables with read lock"
        - backup the DB folder, usually /var/lib/mysql (--mode fs --path-to-backup /var/lib/mysql --max-level 14)
        - manually unlock the DB
    Using mysqldump is not recommended for speed and reliability reasons.
