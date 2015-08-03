===
FAQ
===

1)  **What is freezer**?
    Is a tool to automate data backup and restore
    procedure, it uses OpenStack Swift as the default sorage but local mounted nfs filesystems and ssh upload are also supported

2)  **Does freezer support incremental backup?**
    Two incremental approach has choosen:
    1) Using GNU tar incremental features
    2) An rsync like pure python implementation

3)  **Does freezer check the file contents to establish if a file was modified?**
    Using the tar approach, Freezer check for changes at mtime and ctime in
    every file inode to evaluate if a file has changed or not.
    Using the rsync approach the content of the files are checked

4)  **Why GNU tar rather then rsync?**
    Both approaches are good. Rsync check
    the file content, while tar check the file inode. In our
    environment, we need to backup directories with size > 400GB and
    hundreds of thousands of files. Rsync approach is effective but slow.
    Tar is fast as it needs to check only the file inodes, rather then
    the full file content. Rsync backup type will be added pretty soon

5)  *Does freezer support encrypted backup?*
    Yes. Freezer encrypt data using OpenSSL (AES-256-CFB).

6)  **Does freezer execute point-in-time backup?**
    Yes. For point in time backup LVM snapshot feature used.

7)  **Can I use freezer on OSX or other OS where GNU Tar is not installed
    by default?**
    Yes. For OSX and \*BSD, just install gtar and freezer
    automatically will use gtar to execute backup. OS other then Linux,
    OSX, \*BSD and Windows are currently not supported.

8)  **What Application backup does freezer support currently?**
    MongoDB, MySQL, MS-SQL to have a higher level of data consistency, while
    any appplication is supported for crash consistent data integrity.

9)  **How does the MongoDB backup happens?**
    Freezer required journal enabled in Mongo and lvm volume to execute backup.
    It checks if the Mongo instance is the master and create lvm snapshot to have
    consistent data.

10) **Does freezer manage sparse files efficiently?**
    Yes. Zeroed/null data is not backed up. So less space and bandwidth will be used.

11) **Does freezer remove automatically backup after some time?**
    Yes. From command line the option --remove-older-then (days) can be used to
    remove objects older then (days).

12) **Does freezer support MySQL Backup?**
    Yes.

13) **What storage media are currently supported?**
    Current support media storage are:
    a. Swift
    b. Store files on a remote host file system using ssh
    c. Directory in the local host (i.e. NFS/CIFS mounted volumes)

14) **Does freezer has any Web UI or API?**
    Yes. Freezer has REST API and a Web UI integrated with Horizon

15) **Does Freezer detect removed files between incremental executions?**
    Yes.

16) **Will Freezer be included as official project in OpenStack?**
    We hope so, as soon as we can.

17) **Does freezer support Windows?**
    Yes. The freezer agent and scheduler can be executed on Windows

18) **What is being used on Windows to execute file system snapshots?**
    Curretnly VSS are used to support point in time snapshots

19) **What applications are supported in Windows for  consisten backups?**
    SQL Server (--mode sqlserver)

