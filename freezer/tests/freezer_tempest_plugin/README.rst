==============================
Tempest Integration of Freezer
==============================

This directory contains Tempest tests to cover the freezer project.

Instructions for Running/Developing Tempest Tests with Freezer Project

#. Need to make sure that there is a Devstack or other environment for running Keystone and Swift.

#. Clone the Tempest Repo::

    run 'git clone https://github.com/openstack/tempest.git'

#. Create a virtual environment for Tempest. In these instructions, the Tempest virtual environment is ``~/virtualenvs/tempest-freezer``.

#. Activate the Tempest virtual environment::

    run 'source ~/virtualenvs/tempest-freezer/bin/activate'

#. Make sure you have latest pip installed::

    run 'pip install --upgrade pip'

#. Install Tempest requirements.txt and test-requirements.txt in the Tempest virtual environment::

    run 'pip install -r requirements.txt -r test-requirements.txt'

#. Install Tempest project into the virtual environment in develop mode::

    run ‘python setup.py develop’

#. Create logging.conf in Tempest Repo home dir/etc

    Make a copy of logging.conf.sample as logging.conf

    In logging configuration

    You will see this error on Mac OS X

    socket.error: [Errno 2] No such file or directory

    To fix this, edit logging.conf

    Change ‘/dev/log/ to '/var/run/syslog’ in logging.conf

    see: https://github.com/baremetal/python-backoff/issues/1 for details

#. Create tempest.conf in Tempest Repo home dir/etc::

    run 'oslo-config-generator --config-file etc/config-generator.tempest.conf --output-file etc/tempest.conf'

    Add the following sections to tempest.conf and modify uri and uri_v3 to point to the host where Keystone is running::

    [identity]

    username = freezer
    password = secretservice
    tenant_name = service
    domain_name = default
    admin_username = admin
    admin_password = secretadmin
    admin_domain_name = default
    admin_tenant_name = admin
    alt_username = admin
    alt_password = secretadmin
    alt_tenant_name = admin
    use_ssl = False
    auth_version = v3
    uri = http://10.10.10.6:5000/v2.0/
    uri_v3 = http://10.10.10.6:35357/v3/

    [auth]

    allow_tenant_isolation = true
    tempest_roles = admin


#. Clone freezer Repo::

    run 'git clone https://github.com/openstack/freezer.git'

#. Set the virtual environment to the Tempest virtual environment::

    run 'source ~/virtualenvs/tempest-freezer/bin/activate'

#. pip install freezer requirements.txt and test-requirements.txt in Tempest virtual environment::

    run 'pip install -r requirements.txt -r test-requirements.txt'

#. Install nose in the Temptest virtual environment::

    run 'pip install nose'

#. Install freezer project into the Tempest virtual environment in develop mode::

    run ‘python setup.py develop’

#. Set project interpreter (pycharm) to Tempest virtual environment.

#. Create test config (pycharm) using the Tempest virtual environment as python interpreter::

    Set the environment variable OS_AUTH_URL to the URI where Keystone is running.  For example, OS_AUTH_URL=http://10.10.10.6:5000/v2.0.
    Set the Working Directory to the Tempest home dir. This will allow Tempest to find the etc/tempest.conf file.

#. Run the tests in the api directory in the freezer_tempest_plugin directory.


Mac OS X Instructions
---------------------

For Mac OS X users you will need to install gnu-tar in ``/usr/local/bin`` and make sure that ``/usr/local/bin`` is in the PATH environment variable before any other directories where a different version of tar can be found. Gnu-tar can be installed as ``gtar`` or ``tar``, either name works.

Also, currently for Mac OS X users, the latest version of gnu-tar (1.29) will not allow ``--unlink-first`` and ``--overwrite`` options to be used together. Also, gnu-tar will complain about the ``--unlink-first`` argument. To get around these limitations, you will need to modify ``tar_builders.py`` and remove the ``--unlink-first`` option from the ``UNIX_TEMPLATE`` variable.
