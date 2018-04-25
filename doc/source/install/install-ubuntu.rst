Install and configure for Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Backup
service for Ubuntu 16.04 (LTS).

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      $ sudo apt-get update

      $ sudo apt-get install python-dev python-pip

   .. note:: To list all missing packages needed to install freezer
      in your system use provided ``bindep.txt`` file with `bindep utility.
      <https://docs.openstack.org/infra/bindep/>`_


.. include:: common_configure.rst

Finalize installation
---------------------

Restart the Backup services:

.. code-block:: console

   $ sudo service openstack-freezer-api restart
