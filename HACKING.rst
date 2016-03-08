Freezer Style Commandments
===========================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/
- Step 2: Read on

Freezer Specific Commandments
------------------------------


Logging
-------

Use the common logging module, and ensure you ``getLogger``::

    from oslo_log import log

    LOG = log.getLogger(__name__)

    LOG.debug('Foobar')


oslo.config
-----------

- All configuration options for freezer-scheduler should be in the following file ::

    freezer/scheduler/arguments.py

- After adding new options to freezer-scheduler please use the following command to update the sample configuration file::

    oslo-config-generator --config-file config-generator/scheduler.conf

- If you added support for a new oslo library, you have to edit the following file adding a new namespace for the new oslo library:
for example adding oslo.db::

    # edit config-generator/scheduler.conf
    [DEFAULT]
    output_file = etc/scheduler.conf.sample
    wrap_width = 79
    namespace = scheduler
    namespace = oslo.log
    namespace = oslo.db

This will add oslo.db options to your configuration file.

Agent Options
-------------
- All configuration options for freezer-agent should be in the following file ::

    freezer/common/config.py

- To list options available in freezer-agent use the following command::

    oslo-config-generator --namespace freezer --namespace oslo.log
