This section describes how to install and configure freezer-scheduler and
freezer-agent, on any node in the cloud or any vm inside the cloud.

This section assumes that you already have a working OpenStack
environment with at least the following components installed:
.. Keystone
.. Swift

.. code-block:: bash

  git clone https://git.openstack.org/openstack/freezer.git
  cd freezer
  pip install ./


Configure the scheduler
-----------------------

1. Copy the configuration files to ``/etc/freezer/``:


.. code-block:: console

   $ sudo cp etc/scheduler.conf.sample /etc/freezer/scheduler.conf


2. Edit the ``/etc/freezer/scheduler.conf`` file and complete the following
   actions:

   * In the ``[DEFAULT]`` section, configure database access:

   The ``client_id`` has to be set to the hostname of the machine. It will be
   used as an identifier for this node to fetch its scheduled backups

     .. code-block:: ini

        [DEFAULT]
        ...
        client_id = hostname_of_machine
        jobs_dir = /etc/freezer/scheduler/conf.d


3. Start ``freezer-scheduler``


.. code-block:: console

   $ sudo freezer-scheduler --config-file /etc/freezer/scheduler.conf start
