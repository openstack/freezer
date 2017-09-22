Install and configure for openSUSE and SUSE Linux Enterprise
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Backup service
for openSUSE Leap 42.1 and SUSE Linux Enterprise Server 12 SP1.

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      zypper --quiet --non-interactive install python-dev python-pip

.. include:: common_configure.rst


Finalize installation
---------------------

Start the Backup services and configure them to start when
the system boots:

.. code-block:: console

   # systemctl enable openstack-freezer-api.service

   # systemctl start openstack-freezer-api.service
