.. _install:

Install and configure
~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the
Backup service, code-named freezer-api, on the controller node.

This section assumes that you already have a working OpenStack
environment with at least the following components installed:
.. Keystone

Note that installation and configuration vary by distribution.

.. toctree::
   :maxdepth: 2

   db-install.rst
   install-obs.rst
   install-rdo.rst
   install-ubuntu.rst

.. code-block:: bash

  # git clone https://git.openstack.org/openstack/freezer-api.git
  # cd freezer-api
  # pip install ./

edit config file
----------------

.. code-block:: bash

  # sudo cp etc/freezer/freezer-api.conf /etc/freezer/freezer-api.conf
  # sudo cp etc/freezer/freezer-paste.ini /etc/freezer/freezer-paste.ini
  # sudo vi /etc/freezer/freezer-api.conf
  # sudo vi /etc/freezer/freezer-paste.ini

setup/configure the db
----------------------

The currently supported db is Elasticsearch. In case you are using a dedicated instance
of the server, you'll need to start it. Depending on the OS flavor it might be a:

.. code-block:: bash

  # service elasticsearch start

or, on systemd

.. code-block:: bash

  # systemctl start elasticsearch

Elasticsearch needs to know what type of data each document's field contains.
This information is contained in the `mapping`, or schema definition.
Elasticsearch will use dynamic mapping to try to guess the field type from
the basic datatypes available in JSON, but some field's properties have to be
explicitly declared to tune the indexing engine.
To do that, use the freezer-manage command:
::

  # freezer-manage db sync

You should have updated your configuration files before doing this step.
freezer-manage has the following options:

* To create the db mappings use the following command::

  # freezer-manage db sync

* To update the db mappings using the following command. Update means that you
  might have some mappings and you want to update it with a more recent ones
  ::

  # freezer-manage db update

* To remove the db mappings using the following command ::

  # freezer-manage db remove

* To print the db mappings using the following command ::

  # freezer-manage db show

* To update your settings (number of replicas) all what you need to do is to
  change its value in the configuration file and then run the following command ::

  # freezer-manage db update-settings

If you provided an invalid number of replicas that will cause problems later on,
so it's highly recommended to make sure that you are using the correct number
of replicas. For more info click here `Elasticsearch_Replicas_instructions <https://www.elastic.co/guide/en/elasticsearch/guide/current/replica-shards.html>`_

* To get information about optional additional parameters::

  # freezer-manage -h

* If you want to add any additional parameter like --yes or --erase, they should
  be before the db option. Check the following examples:

Wrong Example::

   # freezer-manage db sync -y -e

Correct Example::

   # freezer-manage -y -e db sync

run simple instance
-------------------

.. code-block:: bash

  # freezer-api

examples running using uwsgi
----------------------------

.. code-block:: bash

  # uwsgi --http :9090 --need-app --master --module freezer_api.cmd.wsgi:application

  # uwsgi --https :9090,foobar.crt,foobar.key --need-app --master --module freezer_api.cmd.wsgi:application


example running freezer-api with apache2
----------------------------------------

.. code-block:: none

    # sudo vi /etc/apache2/sites-enabled/freezer-api.conf

    <VirtualHost ...>
        WSGIDaemonProcess freezer-api processes=2 threads=2 user=freezer display-name=%{GROUP}
        WSGIProcessGroup freezer-api
        WSGIApplicationGroup freezer-api
        WSGIScriptAlias / /opt/stack/freezer_api/cmd/wsgi.py

        <IfVersion >= 2.4>
          ErrorLogFormat "%M"
        </IfVersion>
        ErrorLog /var/log/%APACHE_NAME%/freezer-api.log
        LogLevel warn
        CustomLog /var/log/freezer-api/freezer-api_access.log combined

        <Directory /opt/stack/freezer_api>
          Options Indexes FollowSymLinks MultiViews
          Require all granted
          AllowOverride None
          Order allow,deny
          allow from all
          LimitRequestBody 102400
        </Directory>
    </VirtualHost>


API registration
================

.. code-block:: bash

    # openstack user create --domain default --password-prompt freezer
    # openstack role add --project service --user freezer admin

    # openstack service create --name freezer --description "Freezer Backup Service" backup

    # openstack endpoint create --region RegionOne backup public http://freezer_api_publicurl:port
    # openstack endpoint create --region RegionOne backup internal http://freezer_api_internalurl:port
    # openstack endpoint create --region RegionOne backup admin http://freezer_api_adminurl:port


.. toctree::

   devstack_plugin.rst