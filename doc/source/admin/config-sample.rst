.. _freezer-config-file:

-------------------------------------------
Freezer Scheduler Sample Configuration File
-------------------------------------------

Configure Freezer Scheduler by editing
/etc/freezer/scheduler.conf

No config file is provided with the source code, it will be created during
the installation. In case where no configuration file was installed, one
can be easily created by running:

.. code-block:: console

    tox -e genconfig


To see configuration options available, please refer to :ref:`freezer-config-reference`.

.. only:: html

   The following is a sample monitors configuration for adaptation and use.

   .. literalinclude:: ../_static/freezer.conf.sample
