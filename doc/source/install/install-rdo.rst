Install and configure for Red Hat Enterprise Linux and CentOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


This section describes how to install and configure the Backup service
for Red Hat Enterprise Linux 7 and CentOS 7.

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      $ sudo yum install python-dev python-pip

.. include:: common_configure.rst

Finalize installation
---------------------

Start the Backup services and configure them to start when
the system boots:

.. code-block:: console

   $ sudo systemctl enable openstack-freezer-api.service

   $ sudo systemctl start openstack-freezer-api.service
