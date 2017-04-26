Prerequisites
-------------

Before you install and configure the Backup service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p

   * Create the ``freezer`` database:

     .. code-block:: console

        CREATE DATABASE freezer;

   * Grant proper access to the ``freezer`` database:

     .. code-block:: console

        GRANT ALL PRIVILEGES ON freezer-api.* TO 'freezer'@'localhost' \
          IDENTIFIED BY 'FREEZER_DBPASS';
        GRANT ALL PRIVILEGES ON freezer.* TO 'freezer'@'%' \
          IDENTIFIED BY 'FREEZER_DBPASS';

     Replace ``FREEZER_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: console

        exit;

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
        backup public http://controller:9090/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        backup internal http://controller:9090/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        backup admin http://controller:9090/vY/%\(tenant_id\)s
