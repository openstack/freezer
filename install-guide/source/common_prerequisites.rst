Prerequisites
-------------

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``freezer`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt freezer

   * Add the ``admin`` role to the ``freezer`` user:

     .. code-block:: console

        $ openstack role add --project service --user freezer admin

   * Create the freezer service entities:

     .. code-block:: console

        $ openstack service create --name freezer --description "Backup" backup

#. Create the Backup service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        backup public http://controller:9090/
      $ openstack endpoint create --region RegionOne \
        backup internal http://controller:9090/
      $ openstack endpoint create --region RegionOne \
        backup admin http://controller:9090/
