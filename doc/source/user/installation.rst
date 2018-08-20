Freezer Agent Installation
==========================

Before Installation
-------------------
- Freezer contains two component: Freezer Agent
  (freezer-agent) and Freezer Scheduler (freezer-scheduler).
- Install Freezer Agent from source (It is not hard).
- Chose correct version of Freezer Agent that corresponds other Freezer
  components and your OpenStack version.
- Freezer Scheduler stable/Liberty and stable/Kilo releases only works with
  Keystone API 2.0.


Requirements
------------
Freezer Agent require following packages to be installed:

- python
- python-dev
- GNU Tar >= 1.26
- gzip, bzip2, xz
- OpenSSL
- python-swiftclient
- python-keystoneclient
- pymongo
- PyMySQL
- libmysqlclient-dev
- sync
- At least 128 MB of memory reserved for Freezer

Ubuntu / Debian Installation
----------------------------

**Follow these instructions for Ubuntu or Debian bases Linux distros**

Install required packages first:

.. code:: bash

    sudo apt-get install python-dev python-pip git openssl gcc make automake

For python3:

.. code:: bash

    sudo apt-get install python3-dev git openssl openssl-devel gcc make automake

Clone proper branch of Freezer Client with git:

.. code:: bash

    git clone -b [branch] https://github.com/openstack/freezer.git

Install requirements with pip:

.. code:: bash

    cd freezer/

    sudo pip install -r requirements.txt

Install freezer from source:

.. code:: bash

    sudo python setup.py install

Create ENV file:

.. code:: bash

    sudo nano ~/freezer.env

    # tenant user name
    OS_TENANT_NAME='[tenant_name]'

    # project name
    OS_PROJECT_NAME='[project_name]'

    # tenan user name
    OS_USERNAME='[user_name]'

    #tenant user password
    OS_PASSWORD='[user_password]'

    # API version v2.0 is very important
    # freezer does not work with API version 3
    OS_AUTH_URL='http://[keystone_uri]:[keystone_port]/v2.0'

    # API endpoint type. this is usually 'publicURL'
    OS_ENDPOINT_TYPE='publicURL'

Source the newly created ENV file:

.. code:: bash

    . ~/freezer.env

Check if you have successfully authenticated by Keystone:

.. code:: bash

    freezer-agent --action info

If you do not see any error messages, you have
successfully installed Freezer Agent

RHEL / Centos Installation
--------------------------

**Follow these instructions for RHEL or Centos bases Linux distros**

Install required packages first:

.. code:: bash

    sudo yum install python-devel python-pip git openssl \
    openssl-devel gcc make automake

For python3:

.. code:: bash

    sudo apt-get install python3-devel git openssl \
    openssl-devel gcc make automake

Clone proper branch of Freezer Client with git:

.. code:: bash

    git clone -b [branch] https://github.com/openstack/freezer.git

Install requirements with pip:

.. code:: bash

    cd freezer/

    sudo pip install -r requirements.txt

Install freezer from source:

.. code:: bash

    sudo python setup.py install


Create ENV file:

.. code:: bash

    sudo vi ~/freezer.env

    # tenant user name
    OS_TENANT_NAME='[tenant_name]'

    # project name
    OS_PROJECT_NAME='[project_name]'

    # tenan user name
    OS_USERNAME='[user_name]'

    #tenant user password
    OS_PASSWORD='[user_password]'

    # API version v2.0 is very important
    # freezer does not work with API version 3
    OS_AUTH_URL='http://[keystone_uri]:[keystone_port]/v2.0'

    # API endpoint type. this is usually 'publicURL'
    OS_ENDPOINT_TYPE='publicURL'

Source the newly created ENV file:

.. code:: bash

    . ~/freezer.env

Check if you have successfully authenticated by Keystone:

.. code:: bash

    freezer-agent --action info

If you do not see any error messages, you have
successfully installed Freezer Agent

Windows Installation
--------------------

**Only following components supported for Windows OS Platform:**

- freezer-agent
- freezer-scheduler

**For windows following software must be installed
prior to Freezer Agent installation**

- Python 2.7
- GNU Tar binaries (we recommend to follow [this guide]
  (https://github.com/openstack-freezer-utils/freezer-windows-binaries#windows-binaries-for-freezer) to install them)
- [OpenSSL pre-compiled for windows]
  (https://wiki.openssl.org/index.php/Binaries) or
  [direct download](https://indy.fulgan.com/SSL/openssl-1.0.1-i386-win32.zip)
- [Sync] (https://technet.microsoft.com/en-us/sysinternals/bb897438.aspx)
- [Microsoft Visual C++ Compiler for Python 2.7] (http://aka.ms/vcpython27)
- [PyWin32 for python 2.7]
  (https://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/)

After you have installed required packages install pip:

*Do not forget to ppen "cmd" as Administrator*

.. code:: bash

    easy_install -U pip
    pip install freezer

Freezer scheduler on windows run as a windows service and it needs to be installed as a user service:

*Do not forget to ppen "cmd" as Administrator*

.. code:: bash

    whoami

    cd C:\Python27\Lib\site-packages\freezer\scheduler

    python win_service.py --username {whoami} --password {pc-password} install

Unofficial Installer for Windows
--------------------------------

There is a unofficial Windows installation script. The script is developed
and supported by community.

Windows Installer:
https://github.com/openstack-freezer-utils/freezer-windows-installer#windows-freezer-installer
