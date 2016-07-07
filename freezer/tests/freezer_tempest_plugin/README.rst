Freezer Tempest Tests
=====================

Integration tests in Freezer are implemented using tempest. This document describes  different approaches to run these tests.

Where to start?

* If you just want to run the tests as quickly as possible, start with `Run tests inside a devstack VM`_.
* If you want to run tests on your local machine (with services running in devstack), start with `Run tests outside a devstack VM`_.

  Alternatively there is a slightly different version that uses nose as a testrunner: `Run tests outside a devstack VM (alternative instructions using nose)`_.

* If you want to run tests on your local machine in PyCharm, start with `Run tests in PyCharm`_.

* If you want to run the tests on Mac OS X, start with `Mac OS X Instructions`_ and continue with one of the options above.

Setting up a devstack VM
------------------------

Install devstack with swift and the freezer [1]_ as well as the freezer-api [2]_ plugins by adding the following lines to you `local.conf`:

::  

    enable_plugin freezer https://git.openstack.org/openstack/freezer master
    enable_plugin freezer-api https://git.openstack.org/openstack/freezer-api master
    enable_service s-proxy s-object s-container s-account

.. [1] https://github.com/openstack/freezer/blob/master/devstack/README.rst
.. [2] https://github.com/openstack/freezer-api/blob/master/devstack/README.rst

Run tests inside a devstack VM
-------------------------------

#. Create a devstack VM as described in `Setting up a devstack VM`_

#. Inside your devstack VM, navigate to `/opt/stack/tempest`.

#. Run `ostestr -r freezer`

Debugging tests inside a devstack VM
------------------------------------

Often a devstack VM is used via SSH without graphical interface. Python has multiple command line debuggers. The out-of-the-box pdb works fine but I recommend pudb [3]_ which looks a bit like the old Turbo-Pascal/C IDE. The following steps are necessary to get it running:

#. Follow the steps in `Run tests inside a devstack VM`_.

#. Log into the devstack VM

#. Install pudb:

   :: 

     pip install pudb

#. Open the test file were you want to set the first breakpoint (more breakpoints can be set interactively later) and add the following line

   ::

     import pudb;pu.db

#. Navigate to `/opt/stack/tempest`.

#. `ostestr` runs tests in parallel which causes issues with debuggers. To work around that you need to run the relevant test directly. E.g.:

   ::

     python -m unittest freezer.tests.freezer_tempest_plugin.tests.scenario.test_backups.TestFreezerScenario

#. It should drop you into the debugger!

.. [3] https://pypi.python.org/pypi/pudb

Run tests outside a devstack VM
-------------------------------

This section describes how to run the tests outside of a devstack VM (e.g. in PyCharm) while using services (keystone, swift, ...) inside a VM.

#. Create a devstack VM as described in `Setting up a devstack VM`_.

#. Create and activate a virtual environment for Tempest:
   ::

      virtualenv --no-site-packages tempest-venv
      . tempest-venv/bin/activate

#. Clone and install the Tempest project into the virtual environment:
   ::

     git clone https://github.com/openstack/tempest
     pip install tempest/

#. Clone and install the Freezer project into the virtual environment:
   ::

     git clone https://github.com/openstack/freezer
     pip install -e freezer/

#. Clone and install the Freezer API project into the virtual environment:
   ::

     git clone https://github.com/openstack/freezer-api
     pip install -e freezer-api/

#. Initialise a Tempest working directory:
   ::

     mkdir tempest-working
     cd tempest-working
     tempest init .
     
#. Configure `tempest-working/etc/tempest.conf`. The easiest way to do this is to just copy the config from `/opt/stack/tempest/etc/tempest.conf` inside the devstack VM.

#. Run the freezer test inside the tempest working directory:
   ::

     cd tempest-working
     ostestr -r freezer

Run tests outside a devstack VM (alternative instructions using nose)
---------------------------------------------------------------------

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

Run tests in PyCharm
--------------------

#. Set up the test environment as described in `Run tests outside a devstack VM`_.

#. Start PyCharm and open a new project pointing to the cloned freezer directory.

#. Click `File > Settings > Project: freezer > Project Interpreter`.

#. Click the gear-wheel icon next to `Project Interpreter` and choose `Add Local`.

#. Navigate to your virtual environment and select the Python interpreter under `bin/python` and confirm with `OK`

#. In the left pane, navigate to one of the test scripts in `freezer/tests/freezer_tempest_plugin/tests/[api or scenario]/*.py`.

#. Right-click the file and choose `Run 'Unittests in [..]'`

#. This test run will most likely fail because it is started from the wrong directory. To fix this, open the dropdown box next to the run button in the top-right corner. Choose `Edit Configurations ..`

#. Point `Working directory:` to your tempest working directory.

#. Run the test again, this time it should work!



Troubleshooting
---------------

If tests fail these are good places to check:

* freezer-api log: `/var/log/apache2/freezer-api.log`
* freezer-agent log: `$HOME/.freezer/freezer.log`
