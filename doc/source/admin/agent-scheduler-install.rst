Installation
============

Before Installation
-------------------

- You will be required to install Freezer Agent before installing Freezer API
  or Freezer Web UI
- Install Freezer Agent from source. Do not use pip!
- Use this guide to install Freezer Agent to OpenStack Controller node
  (Where you have installed Horizon and Keystone)
- Use corresponding release to your OpenStack version. For example;
  If your OpenStack version is Liberty, user stable/Liberty branch.

Requirements
------------

- python
- python-dev
- git
- Development Tools (gcc)
- libffi
- GNU Tar >= 1.26
- gzip, bzip2, xz
- OpenSSL
- OpenSSL Development
- python-swiftclient
- python-keystoneclient
- libmysqlclient-dev
- sync

You can check up to date required packages from "requirements.txt"

Ubuntu / Debian Installation
----------------------------

**Follow these instructions if your OpenStack controller nodes are installed
on Ubuntu or Debian based Linux distros**

Install required packages first:

.. code:: bash

    sudo apt-get install python-dev python-pip git openssl gcc make automake

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
