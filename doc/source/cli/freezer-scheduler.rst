=================
freezer-scheduler
=================

---------------------------------
backup and restore your resources
---------------------------------

:Author: openstack@lists.openstack.org
:Date:   2017-09-19
:Copyright: OpenStack Foundation
:Version: 1.0.0
:Manual section: 1
:Manual group: cloud backup and restore

SYNOPSIS
========

freezer-scheduler <action> [<args>]

DESCRIPTION
===========

freezer-scheduler is being used to schedule backup and restore of different cloud resources, It can also be used to schedule admin operations on your backup like (remove old backups, list backups, ...). More information about OpenStack Freezer is at https://docs.openstack.org/freezer/latest/.

OPTIONS
=======
.. oslo.config:group:: DEFAULT

.. oslo.config:option:: debug

  :Type: boolean
  :Default: ``false``
  :Mutable: This option can be changed without restarting.

  If set to true, the logging level will be set to DEBUG instead of the default INFO level.


.. oslo.config:option:: log_config_append

  :Type: string
  :Default: ``<None>``
  :Mutable: This option can be changed without restarting.

  The name of a logging configuration file. This file is appended to any existing logging configuration files. For details about logging configuration files, see the Python logging module documentation. Note that when logging configuration files are used then all logging configuration is set in the configuration file and other logging configuration options are ignored (for example, logging_context_format_string).

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * log-config
     - * DEFAULT
       * log_config


.. oslo.config:option:: log_date_format

  :Type: string
  :Default: ``%Y-%m-%d %H:%M:%S``

  Defines the format string for %(asctime)s in log records. Default: the value above . This option is ignored if log_config_append is set.


.. oslo.config:option:: log_file

  :Type: string
  :Default: ``<None>``

  (Optional) Name of log file to send logging output to. If no default is set, logging will go to stderr as defined by use_stderr. This option is ignored if log_config_append is set.

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * logfile


.. oslo.config:option:: log_dir

  :Type: string
  :Default: ``<None>``

  (Optional) The base directory used for relative log_file  paths. This option is ignored if log_config_append is set.

  .. list-table:: Deprecated Variations
     :header-rows: 1

     - * Group
       * Name
     - * DEFAULT
       * logdir


.. oslo.config:option:: watch_log_file

  :Type: boolean
  :Default: ``false``

  Uses logging handler designed to watch file system. When log file is moved or removed this handler will open a new log file with specified path instantaneously. It makes sense only if log_file option is specified and Linux platform is used. This option is ignored if log_config_append is set.


.. oslo.config:option:: use_syslog

  :Type: boolean
  :Default: ``false``

  Use syslog for logging. Existing syslog format is DEPRECATED and will be changed later to honor RFC5424. This option is ignored if log_config_append is set.


.. oslo.config:option:: use_journal

  :Type: boolean
  :Default: ``false``

  Enable journald for logging. If running in a systemd environment you may wish to enable journal support. Doing so will use the journal native protocol which includes structured metadata in addition to log messages.This option is ignored if log_config_append is set.


.. oslo.config:option:: syslog_log_facility

  :Type: string
  :Default: ``LOG_USER``

  Syslog facility to receive log lines. This option is ignored if log_config_append is set.


.. oslo.config:option:: use_stderr

  :Type: boolean
  :Default: ``false``

  Log output to standard error. This option is ignored if log_config_append is set.


.. oslo.config:option:: logging_context_format_string

  :Type: string
  :Default: ``%(asctime)s.%(msecs)03d %(process)d %(levelname)s %(name)s [%(request_id)s %(user_identity)s] %(instance)s%(message)s``

  Format string to use for log messages with context.


.. oslo.config:option:: logging_default_format_string

  :Type: string
  :Default: ``%(asctime)s.%(msecs)03d %(process)d %(levelname)s %(name)s [-] %(instance)s%(message)s``

  Format string to use for log messages when context is undefined.


.. oslo.config:option:: logging_debug_format_suffix

  :Type: string
  :Default: ``%(funcName)s %(pathname)s:%(lineno)d``

  Additional data to append to log message when logging level for the message is DEBUG.


.. oslo.config:option:: logging_exception_prefix

  :Type: string
  :Default: ``%(asctime)s.%(msecs)03d %(process)d ERROR %(name)s %(instance)s``

  Prefix each line of exception output with this format.


.. oslo.config:option:: logging_user_identity_format

  :Type: string
  :Default: ``%(user)s %(tenant)s %(domain)s %(user_domain)s %(project_domain)s``

  Defines the format string for %(user_identity)s that is used in logging_context_format_string.


.. oslo.config:option:: default_log_levels

  :Type: list
  :Default: ``amqp=WARN,amqplib=WARN,boto=WARN,sqlalchemy=WARN,suds=INFO,oslo.messaging=INFO,oslo_messaging=INFO,iso8601=WARN,requests.packages.urllib3.connectionpool=WARN,urllib3.connectionpool=WARN,websocket=WARN,requests.packages.urllib3.util.retry=WARN,urllib3.util.retry=WARN,keystonemiddleware=WARN,routes.middleware=WARN,stevedore=WARN,taskflow=WARN,keystoneauth=WARN,oslo.cache=INFO,dogpile.core.dogpile=INFO``

  List of package logging levels in logger=LEVEL pairs. This option is ignored if log_config_append is set.


.. oslo.config:option:: publish_errors

  :Type: boolean
  :Default: ``false``

  Enables or disables publication of error events.


.. oslo.config:option:: instance_format

  :Type: string
  :Default: ``"[instance: %(uuid)s] "``

  The format for an instance that is passed with the log message.


.. oslo.config:option:: instance_uuid_format

  :Type: string
  :Default: ``"[instance: %(uuid)s] "``

  The format for an instance UUID that is passed with the log message.


.. oslo.config:option:: rate_limit_interval

  :Type: integer
  :Default: ``0``

  Interval, number of seconds, of log rate limiting.


.. oslo.config:option:: rate_limit_burst

  :Type: integer
  :Default: ``0``

  Maximum number of logged messages per rate_limit_interval.


.. oslo.config:option:: rate_limit_except_level

  :Type: string
  :Default: ``CRITICAL``

  Log level name used by rate limiting: CRITICAL, ERROR, INFO, WARNING, DEBUG or empty string. Logs with level greater or equal to rate_limit_except_level are not filtered. An empty string means that all levels are filtered.


.. oslo.config:option:: fatal_deprecations

  :Type: boolean
  :Default: ``false``

  Enables or disables fatal status of deprecations.


.. oslo.config:option:: client_id

  :Type: string
  :Default: ``<None>``

  Specifies the client_id used when contacting the service.
   If not specified it will be automatically created
   using the tenant-id and the machine hostname.


.. oslo.config:option:: no_api

  :Type: boolean
  :Default: ``false``

  Prevents the scheduler from using the api service


.. oslo.config:option:: jobs_dir

  :Type: string
  :Default: ``/etc/freezer/scheduler/conf.d``

  Used to store/retrieve files on local storage, including those exchanged with the api service. Default value is /etc/freezer/scheduler/conf.d (Env: FREEZER_SCHEDULER_CONF_D)


.. oslo.config:option:: interval

  :Type: integer
  :Default: ``60``

  Specifies the api-polling interval in seconds. Defaults to 60 seconds


.. oslo.config:option:: no_daemon

  :Type: boolean
  :Default: ``false``

  Prevents the scheduler from running in daemon mode


.. oslo.config:option:: insecure

  :Type: boolean
  :Default: ``false``

  Initialize freezer scheduler with insecure mode


.. oslo.config:option:: disable_exec

  :Type: boolean
  :Default: ``false``

  Allow Freezer Scheduler to deny jobs that execute commands for security reasons


.. oslo.config:option:: concurrent_jobs

  :Type: integer
  :Default: ``1``

  Number of jobs that can be executed at the same time


SEE ALSO
========

* `OpenStack Freezer <https://docs.openstack.org/freezer/latest/>`__

BUGS
====

* Freezer bugs are managed at Launchpad `Bugs : Freezer <https://bugs.launchpad.net/freezer>`__


