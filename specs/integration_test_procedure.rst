=============
Test Scenario
=============

Summary
=======

    * Intro
    * 1. Setup Devstack machine with swift and elasticsearch
    * 2. Setup the client machine
    * 3. Freezer test scenarios
    * 4. Automated Integration Tests

Intro
=====

Test environment nodes layout:

    1) Server Machine (192.168.20.100)
        * devstack
        * elasticsearch
        * freezer api

    2) Client Machine(s)
        * freezerc
        * freezer-scheduler

Freezer requires Python version 2.7. Using a virtualenv is also recommended
The devstack, elasticsearch and freezer-api services can also be distributed
across different nodes.

In this example the server machine has a (main) interface with ip 192.168.20.100

1. Setup Devstack machine with swift and elasticsearch
======================================================

1.1 devstack
------------
Install devstack with swift support. See http://docs.openstack.org/developer/devstack/
::

  $ cat local.conf

  LOGDAYS=1
  LOGFILE=$DEST/logs/stack.sh.log
  SCREEN_LOGDIR=$DEST/logs/screen
  ADMIN_PASSWORD=quiet
  DATABASE_PASSWORD=$ADMIN_PASSWORD
  RABBIT_PASSWORD=$ADMIN_PASSWORD
  SERVICE_PASSWORD=$ADMIN_PASSWORD
  SERVICE_TOKEN=a682f596-76f3-11e3-b3b2-e716f9080d50
  SWIFT_REPLICAS=1
  SWIFT_DATA_DIR=$DEST/data/swift
  SWIFT_HASH=66a3d6b56c1f479c8b4e70ab5c2000f5
  enable_service s-proxy s-object s-container s-account


1.1.1 OpenStack variables
-------------------------
Quick script to set OS variables:
::

  $ cat > ~/os_variables

  #!/bin/bash
  # optional parameters:
  #  1 - os_tenant_name
  #  2 - os_user_name
  #  3 - os_auth_url
  #
  export OS_TENANT_NAME=${1:-admin}
  export OS_USERNAME=${2:-admin}
  export ADDR=${3:-192.168.20.100}
  export OS_REGION_NAME=RegionOne
  export OS_PASSWORD=quiet
  export OS_AUTH_URL=http://${ADDR}:5000/v2.0
  export OS_TENANT_ID=`openstack project list | awk -v tenant="$OS_TENANT_NAME" '$4==tenant {print $2}'`
  env | grep OS_

1.1.2 register freezer service in keystone
------------------------------------------
::

    export my_devstack_machine=192.168.20.100
    openstack user create --password FREEZER_PWD freezer
    openstack role add --user freezer --project service admin

    openstack service create --name freezer \
      --description "Freezer Backup Service" backup

    openstack endpoint create --region regionOne \
      --publicurl http://${my_devstack_machine}:9090 \
      --internalurl http://${my_devstack_machine}:9090 \
      --adminurl http://${my_devstack_machine}:9090 backup

1.1.3 add a user for the tests in keystone
------------------------------------------
::

  source os_variables
  openstack project create --description "Testing project for Freezer" fproject
  openstack user create --password quiet fuser
  openstack role add --project fproject --user fuser Member
  openstack role add --project fproject --user fuser admin


1.2 Elasticsearch
-----------------
visit https://www.elastic.co for installation instruction

Relevant lines in /etc/elasticsearch/elasticsearch.yml
::

  cluster.name: elasticfreezer  # choose you own
  network.host: 192.168.20.100


1.3 Python Virtualenv
---------------------
Not required, but recommended
::

  apt-get install virtualenv
  virtualenv ~/.venv
  source ~/.venv/bin/activate


1.4 Freezer Service
-------------------

1.4.1 Freezer API installation steps and requirements
-----------------------------------------------------
::

  cd ~ && source ~/.venv/bin/activate
  git clone https://github.com/openstack/freezer.git
  cd freezer/freezer_api
  pip install -r requirements.txt
  python setup.py install

1.4.2 Freezer API Configuration
-------------------------------
::

  $ cat /etc/freezer-api.conf

  [DEFAULT]
  verbose = false
  logging_file = freezer-api.log

  [keystone_authtoken]
  identity_uri = http://192.168.20.100:35357/
  auth_uri = http://192.168.20.100:5000/
  admin_user = freezer
  admin_password = FREEZER_PWD
  admin_tenant_name = service
  include_service_catalog = False
  delay_auth_decision = False
  insecure=true

  [storage]
  db=elasticsearch
  endpoint=http://192.168.20.100:9200

If you plan to use a devstack installation on a different machine, update with the
correct URIs in the [keystone_authtoken] section

Same for the elasticsearch endpoint in the [storage] section

1.4.3 Start API service
-----------------------
Quick start the api for test:
::

  $ freezer-api 192.168.20.100


2. Setup the client machine
===========================
::

  git clone https://github.com/openstack/freezer.git
  cd freezer
  pip install -r requirements.txt
  python setup.py install


3. Freezer test scenarios
=========================
While executing the freezer script it can be useful to monitor the logs:
::

  tail -f /var/log/freezer.log /var/log/freezer-scheduler.log

3.1 File system tree backup/restore (no snapshot involved)
----------------------------------------------------------
  * backup mode: fs
  * directory
  * local storage
  * no lvm

3.1.1 Setup
-----------
::

  mkdir -p ~/test/data_dir ~/test/data_dir/subdir1 ~/test/data_dir/subdir2 ~/test/data_dir_restore ~/test/storage
  echo 'alpha bravo' > ~/test/data_dir/file01.txt
  echo 'charlie delta' > ~/test/data_dir/subdir1/file11.txt
  ln -s ~/test/data_dir/subdir1/file01.txt  ~/test/data_dir/subdir2/link_file01.txt

3.1.2 Backup
------------
::

  freezerc --path-to-backup ~/test/data_dir --container ~/test/storage --backup-name my_test_backup --max-level 3 --storage local
  # add a file
  echo 'echo foxtrot' > ~/test/data_dir/subdir2/file21.txt
  # take another backup, level will be 1
  freezerc --path-to-backup ~/test/data_dir --container ~/test/storage --backup-name my_test_backup --max-level 3 --storage local

3.1.3 restore
-------------
::

  freezerc --action restore --restore-abs-path ~/test/data_dir_restore --container ~/test/storage --backup-name copia_dati_fondamentali --storage local


3.2 Backup apache folder using lvm snapshot and restore on a different machine
------------------------------------------------------------------------------
  * backup mode: fs
  * directory
  * swift storage
  * lvm snapshot

The commands need to be executed with superuser privileges, because of
file access rights and also lvm-snapshot creation.

We also need the hostname of the source machine to restore on a
different machine.

::

  $ hostname
  test_machine_1

since we're going to use swift, we also need to source the env vars containing our os credentials

3.2.1 check available space for the lvm snapshot
------------------------------------------------
::

  # sudo vgdisplay
    --- Volume group ---
    VG Name               freezer1-vg
    System ID
    Format                lvm2
    Metadata Areas        1
    Metadata Sequence No  13
    VG Access             read/write
    VG Status             resizable
    MAX LV                0
    Cur LV                2
    Open LV               2
    Max PV                0
    Cur PV                1
    Act PV                1
    VG Size               49.76 GiB
    PE Size               4.00 MiB
    Total PE              12738
    Alloc PE / Size       11159 / 43.59 GiB
    Free  PE / Size       1579 / 6.17 GiB
    VG UUID               Ns35jE-eTAT-dy1j-ArWw-8ztM-Wvw2-3nTJOn

Here we have 6.17 GB available for lvm snapshots

3.2.2 Backup
------------
Source the env variable containing the OS credentials. The simple script above accepts
the OS_tenant and OS_user as parameters

::

  sudo -s
  source ~/.venv/bin/activate
  source os_variables fproject fuser

  freezerc --action backup --container freezer_test_backups --backup-name apache_backup \
  --max-level 3 --max-segment-size 67108864 \
  --lvm-auto-snap /etc/apache2 \
  --lvm-dirmount /var/freezer/freezer-apache2 \
  --lvm-snapsize 1G \
  --lvm-snapname freezer-apache2-snap \
  --path-to-backup /var/freezer/freezer-apache2/etc/apache2


3.2.3 Restore on a different machine
------------------------------------
We need to use the --restore-from-host parameter because we are restoring on
another machine

::

  sudo -s
  source ~/.venv/bin/activate
  source os_variables fproject fuser

  freezerc --action restore --container freezer_test_backups --backup-name apache_backup \
  --restore-abs-path /etc/apache2 \
  --restore-from-host test_machine_1


3.3 Use a INI config file to backup directory /etc/ssl
------------------------------------------------------

3.3.1 Execute a backup using a config file
------------------------------------------
::

  cat > backup_apache.ini

  [job]
  action=backup
  container=freezer_test_backups
  backup+name=apache_backup
  max_level=3
  max_segment_size=67108864
  lvm_auto-snap=/etc/apache2
  lvm_dirmount=/var/freezer/freezer-apache2
  lvm_snapsize=1G
  lvm_snapname=freezer-apache2-snap
  path_to_backup=/var/freezer/freezer-apache2/etc/apache2

  freezerc --config backup_apache.ini

3.3.2 Execute a restore using a config file
-------------------------------------------
::

  cat > restore_apache.ini

  [job]
  action=restore
  container=freezer_test_backups
  backup_name=apache_backup
  restore_abs_path=/etc/apache2
  restore_from_host=test_machine_1

  freezerc --config restore_apache.ini


3.4 Incremental backup and restore of mysql using the freezer-scheduler
-----------------------------------------------------------------------
We want to push jobs to be executed on the test machine. For that we need
to know what is the client_id of the machine we want to execute the jobs on.
When not provided with a client_id parameter, the scheduler uses the default value
::

  client_id = <tenant_id>_<hostname>

For example, if the tenant_id is 03a81f73595c46b38e0cabf047cb0206 and the host running
the scheduler is "pluto" the default client_id will be 03a81f73595c46b38e0cabf047cb0206_pluto:
::

  # openstack project list
  +----------------------------------+--------------------+
  | ID                               | Name               |
  +----------------------------------+--------------------+
  | 03a81f73595c46b38e0cabf047cb0206 | fproject           |
  .....

  # hostname
  pluto

  # freezer-scheduler client-list
  +-------------------------------------------+----------------------------+-------------+
  |                 client_id                 |          hostname          | description |
  +-------------------------------------------+----------------------------+-------------+
  | 03a81f73595c46b38e0cabf047cb0206_pluto    |            pluto           |             |
  .....

We are going to use "client_node_1" as a client_id. We are therefore going to start the
scheduler using the parameter
::

  -c client_node_1

We also use that parameter when using the freezer-scheduler to interact with the api.

3.4.1 Start the freezer scheduler on the target client machine
--------------------------------------------------------------
Start the scheduler with the custom client_id.
The scheduler connects to the freezer api service registered in keystone.
If there's no api service registered you need to specify it using
the command line option --os-endpoint
Since this is a demo, we want the freezer-scheduler to poll the api every 10 seconds
instead of the default 60 seconds, so we use the parameter "-i 10".
::

  sudo -s
  source ~/.venv/bin/activate
  source os_variables fproject fuser
  freezer-scheduler -c client_node_1 -i 10 start

You can check that the demo in running with:
::

  # freezer-scheduler status
  Running with pid: 9972

Then we clean the /var/lib/mysql folder and leave a terminal open with the
freezer-scheduler logs:
::

  rm -rf /var/lib/mysql/*
  tail -f /var/log/freezer-scheduler.log

3.4.2 Create the job configuration and upload it to the api service
-------------------------------------------------------------------
Log in any machine and create the restore job.
Remember to source the OS variables and use the custom client_id
::

  source os_variables fproject fuser
  cat > job-backup-mysql.conf

    {
        "job_actions": [
            {
                "freezer_action": {
                "mode" : "mysql",
                "mysql_conf" : "/etc/mysql/debian.cnf",
                "path_to_backup": "/var/freezer/freezer-db-mysql/var/lib/mysql/",
                "lvm_auto_snap": "/var/lib/mysql",
                "lvm_dirmount": "/var/freezer/freezer-db-mysql",
                "lvm_snapsize": "1G",
                "backup_name": "freezer-db-mysql",
                "max_level": 6,
                "lvm_snapname": "freezer_db-mysql-snap",
                "max_priority": true,
                "remove_older_than": 90,
                "max_segment_size": 67108864,
                "container": "freezer_backup_devstack_1"
            },
            "max_retries": 3,
            "max_retries_interval": 10,
            "mandatory": true
            }
        ],
        "job_schedule" : {
        },
        "description": "mysql backup"
    }

If we want the backup to be executed every day at 3am,
we can specify the following scheduling properties:
::

    "job_schedule" : {
        "schedule_interval": "1 days",
        "schedule_start_date": "2015-06-30T03:00:00"
    },

Upload it into the api using the correct client_id
::

  freezer-scheduler job-create -c client_node_1 --file job-backup-mysql.conf

The status of the jobs can be checked with
::

  freezer-scheduler -c client_node_1 job-list

If no scheduling information is provided, the job will be executed as soon
as possible, so its status will go into "running" state, then "completed".

Information about the scheduling and backup-execution can be found in
/var/log/freezer-scheduler.log and /var/log/freezer.log, respectively.

**NOTE**: Recurring jobs never go into "completed" state, as they go back
into "scheduled" state.

3.4.3 Create a restore job and push it into the api
---------------------------------------------------
If we want to restore on a different node, we need to provide the
restore_from_host parameter.
::

    cat > job-restore-mysql.conf
    {
        "job_actions": [
            {
                "freezer_action": {
                    "action": "restore",
                    "restore_abs_path": "/var/lib/mysql",
                    "restore_from_host": "test_machine_1",
                    "backup_name": "freezer-db-mysql",
                    "container": "freezer_backup_devstack_1"
                },
            "max_retries": 1,
            "max_retries_interval": 10,
            "mandatory": true
            }
        ],
        "description": "mysql test restore"
    }

    freezer-scheduler job-create -c client_node_1 --file job-restore-mysql.conf


3.5 Differential backup and restore
-----------------------------------
The difference is in the use of the parameter "always_level": 1
We also specify a different container, so it's easier to spot
the files created in the swift container:
::

  swift list freezer_backup_devstack_1_alwayslevel


3.5.1 Backup job
----------------
::

    cat > job-backup.conf

    {
        "job_actions": [
            {
                "freezer_action": {
                "mode" : "mysql",
                "mysql_conf" : "/etc/mysql/debian.cnf",
                "path_to_backup": "/var/freezer/freezer-db-mysql/var/lib/mysql/",
                "lvm_auto_snap": "/var/lib/mysql",
                "lvm_dirmount": "/var/freezer/freezer-db-mysql",
                "lvm_snapsize": "1G",
                "backup_name": "freezer-db-mysql",
                "always_level": 1,
                "lvm_snapname": "freezer_db-mysql-snap",
                "max_priority": true,
                "remove_older_than": 90,
                "max_segment_size": 67108864,
                "container": "freezer_backup_devstack_1_alwayslevel"
            },
            "max_retries": 3,
            "max_retries_interval": 10,
            "mandatory": true
            }
        ],
        "job_schedule" : {
        },
        "description": "mysql backup"
    }

    freezer-scheduler job-create -c client_node_1 --file job-backup.conf

3.5.2 Restore job
-----------------
The restore job is the same as in 3.4.3

::

    cat > job-restore.conf
    {
        "job_actions": [
            {
                "freezer_action": {
                    "action": "restore",
                    "restore_abs_path": "/var/lib/mysql",
                    "restore_from_host": "test_machine_1",
                    "backup_name": "freezer-db-mysql",
                    "container": "freezer_backup_devstack_1_alwayslevel"
                },
            "max_retries": 1,
            "max_retries_interval": 10,
            "mandatory": true
            }
        ],
        "description": "mysql test restore"
    }

    freezer-scheduler job-create -c client_node_1 --file job-restore.conf


4. Automated Integration Tests
==============================

Automated integration tests are being provided in the directory

freezer/tests/integration directory

Since they require external resources - such as swift or ssh storage -
they are executed only when some environment variables are defined.

4.1 local storage tests
-----------------------
always executed automatically, using temporary local directories under /tmp
(or whatever temporary path is available)

4.2 ssh storage
---------------
SSH storage need the following environment variables to be defined:
::

     * FREEZER_TEST_SSH_KEY
     * FREEZER_TEST_SSH_USERNAME
     * FREEZER_TEST_SSH_HOST
     * FREEZER_TEST_CONTAINER

For example:
::

  export FREEZER_TEST_SSH_KEY=/home/myuser/.ssh/id_rsa
  export FREEZER_TEST_SSH_USERNAME=myuser
  export FREEZER_TEST_SSH_HOST=127.0.0.1
  export FREEZER_TEST_CONTAINER=/home/myuser/freezer_test_backup_storage_ssh

4.3 swift storage
-----------------
To enable the swift integration tests - besides having a working swift node -
the following variables need to be defined accordingly:
::

     * FREEZER_TEST_OS_TENANT_NAME
     * FREEZER_TEST_OS_USERNAME
     * FREEZER_TEST_OS_REGION_NAME
     * FREEZER_TEST_OS_PASSWORD
     * FREEZER_TEST_OS_AUTH_URL

For example:
::

  export FREEZER_TEST_OS_TENANT_NAME=fproject
  export FREEZER_TEST_OS_USERNAME=fuser
  export FREEZER_TEST_OS_REGION_NAME=RegionOne
  export FREEZER_TEST_OS_PASSWORD=freezer
  export FREEZER_TEST_OS_AUTH_URL=http://192.168.56.223:5000/v2.0

The cloud user/tenant has to be already been created

4.4 LVM and MySQL
-----------------
Some tests, like LVM snapshots and access to privileged files, need
the tests to be executed with superuser privileges.
Tests involving such requirements are not executed when run
with normal-user privileges.
In cases where LVM snapshot capability is not available (for example
the filesystem does not make use of LV or there are not enough space
available) the LVM tests can be skipped by defining the following
env variable:
::

  * FREEZER_TEST_NO_LVM
