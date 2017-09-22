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

   db-install
   install-obs
   install-rdo
   install-ubuntu

.. code-block:: console

  $ git clone https://git.openstack.org/openstack/freezer-api.git
  $ cd freezer-api
  $ pip install ./


.. toctree::

   devstack_plugin.rst
