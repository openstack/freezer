Installation
============

This guide will help you install Freezer API framework in one of your OpenStack
controller node. You can install Freeer API in stand alone virtual or bare
metal server but it is strongly suggested install in controller node.

Before Installation
-------------------

- Freezer Agent must be installed
- Use this guide to install Freezer Agent to OpenStack Controller node
  (Where you have installed Horizon and Keystone)
- Use corresponding release to your OpenStack version. For example;
  If your OpenStack version is Liberty, user stable/Liberty branch.
- Do not forget to register Keystone API endpoint and service
- Elasticsearch must be installed

Requirements
------------
- elasticsearch>=1.3.0,<2.0 # Apache-2.0
- falcon>=0.1.6 # Apache-2.0
- jsonschema>=2.0.0,<3.0.0,!=2.5.0 # MIT
- keystonemiddleware>=4.0.0 # Apache-2.0
- oslo.config>=3.2.0 # Apache-2.0
- oslo.i18n>=1.5.0 # Apache-2.0
- six>=1.9.0 # MIT
- Freezer Agent & Scheduler installed from source

Ubuntu / Debian Installation
----------------------------

**Follow these instructions if your OpenStack controller nodes are installed
on Ubuntu or Debian based Linux distros**

Install required packages first:
(If you have installed Freezer Agent from source, following packages are already installed.)

.. code:: bash

    sudo apt-get install python-dev python-pip git openssl gcc make automake

Clone proper branch of Freezer API with git:

.. code:: bash

    git clone -b [branch] https://github.com/openstack/freezer-api.git

Install requirements with pip:

.. code:: bash

    cd freezer-api/

    sudo pip install -r requirements.txt

Install Freezer API from source:

.. code:: bash

    sudo python setup.py install

Copy config file:

.. code:: bash

    sudo cp etc/freezer-api.conf /etc/freezer-api.conf

Edit config file:

.. code:: bash

    sudo nano /etc/freezer-api.conf

    # change log file location
    log_file = /var/log/freezer-api.log

    # configure Keystone authentication

    [keystone_authtoken]
    auth_protocol = http
    auth_host = [keystone_host_ip_or_hostname]
    auth_port = 5000
    admin_user = [freezer admin user] # admin or user with admin priviliges
    admin_password = [admin password]
    admin_tenant_name = [admin tenan] # usually admin
    include_service_catalog = False
    delay_auth_decision = False

    [storage]
    # supported db engine. currently elasticsearch only
    db=elasticsearch
    hosts='http://[elasticsearch host address]:9200'
    # freezer-manage db sync/update uses the following parameter to set the number of replicas
    number_of_replicas=1


Follow this instructions to install Elasticsearch 1.7.5:

.. code:: bash

    https://goo.gl/bwDcNK

    service elasticsearch start

***You must install Elasticsearch 1.7.5 for Freezer API to work correctly***

Elasticsearch needs to know what type of data each document's field contains.
This information is contained in the "mapping", or schema definition.

Elasticsearch will use dynamic mapping to try to guess the field type from the
basic datatypes available in JSON, but some field's properties have to be
explicitly declared to tune the indexing engine.

Let's initialize database:

.. code:: bash

    freezer-manage db sync

Run Freezer API:

.. code:: bash

    freezer-api 0.0.0.0

There is not any Freezer API Deamon. If you need to run Freezer API in
backgroun, user following commend:

.. code:: bash

    freezer-api 0.0.0.0 >/dev/null 2>&1

Keystone API v2.0 endpoint registration:

.. code:: bash

    keystone service-create --name freezer --type backup \
    --description "Freezer Backup Service"

    # use public IP address or hostname because Freezer Scheduler must be able
    to reach API from public IP or hostname.

    # default port is 9090. If you have changed in freezer-api.conf you must
    change it here too.

    keystone endpoint-create \
    --service-id $(keystone service-list | awk '/ backup / {print $2}') \
    --publicurl http://[freezer_api_publicurl]:[port] \
    --internalurl http://[freezer_api_internalurl]:[port] \
    --adminurl http://[freezer_api_adminurl]:[port] \
    --region regionOne

Keystone API v3 endpoint registration:

.. code:: bash

    # With OpenStack Liberty, Keystone API v2.0 is depreciated and you will not
    able to use "keystone-client" commend instead user "openstack" commend

    openstack service create --name freezer \
    --description "Freezer Backup Service" backup

    # use public IP address or hostname because Freezer Scheduler must be able
    to reach API from public IP or hostname.

    # default port is 9090. If you have changed in freezer-api.conf you must
    change it here too.

    openstack endpoint create   --publicurl http://176.53.94.101:9090 \
    --internalurl http://192.168.0.4:9090 \
    --adminurl http://176.53.94.101:9090 \
    --region RegionOne backup
