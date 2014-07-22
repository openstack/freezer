FAQ
===

1)  What is freezer? Is a tool to automate data backup and restore
    process using OpenStack Swift.

2)  Does freezer support incremental backup? Yes. Incremental backup are
    done using GNU tar incremental features

3)  Does freezer check the file contents to establish if a file was
    modified or not? No. Freezer check for changes at mtime and ctime in
    every file inode to evaluate if a file changed or not.

4)  Why GNU tar rather then rsync? Both approaches are good. Rsync check
    the file content, while tar check the file inode. In our
    environment, we need to backup directories with size > 300GB and
    tens of thousands of files. Rsync approach is effective but slow.
    Tar is fast as it needs to check only the file inodes, rather then
    the full file content.

5)  Does feezer support encrypted backup? Yes. Freezer encrypt data
    using OpenSSL (AES-256-CFB).

6)  Does freezer execute point-in-time backup? Yes. For point in time
    backup LVM snapshot feature used.

7)  Can I use freezer on OSX or other OS where GNU Tar is not installed
    by default? Yes. For OSX and \*BSD, just install gtar and freezer
    automatically will use gtar to execute backup. OS other then Linux,
    OSX and \*BSD are currently not supported.

8)  What Application backup does freezer support currently? MongoDB and
    File system.

9)  How does the MongoDB backup happens? Freezer required journal
    enabled in mongo and lvm volume to execute backup. It checks if the
    mongo instance is the master and create lvm snapshot to have
    consistent data.

10) Does freezer manage sparse files efficiently? Yes. Zeroed/null data
    is not backed up. So less space and bandwidth will be used.

11) Does freezer remove automatically backup after some time? Yes. From
    command line the --remove-older-then option (days) can be used to
    remove objects older then (days).

12) Does freezer support MySQL Backup? MySQL and MariaDB support soon
    will be included.

13) Is there any other storage media supported? Not currently. There's a
    plan to add:

-  Amazon S3
-  Store files on a remote host file system
-  MongoDB object storage.
-  Other directory in the local host (NFS mounted volumes)

14) Does freezer has any UI or API? Not currently. The UI in OpenStack
    Horizon is being currently developed as REST API too.

15) Tar is not capable to detect deleted files between different backup
    levels. Is freezer capable of doing that? Not currently. We are
    writing a set of tar extensions in python to overcome tar
    limitations like this and others.


