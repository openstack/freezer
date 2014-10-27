========================
Freezer - Horizon Web UI
=======================

Freezer now has basic support for a Web UI integrated with OpenStack Horizon.

In the installation procedure we'll assume your main Horizon dashboard
directory is /opt/stack/horizon/openstack_dashboard/dashboards/.

To install the horizon web ui you need to do the following::

    # git clone https://github.com/stackforge/freezer

    # cd freezer/horizon_web_ui

    # cp -r devfreezer /opt/stack/horizon/openstack_dashboard/dashboards/

    # cp _50_devfreezer.py  /opt/stack/horizon/openstack_dashboard/enabled/
    # cd /opt/stack/horizon/

    # ./run_tests.sh --runserver 0.0.0.0:8878


Now a new Tab is available in the dashboard lists on the left,
called "Backup as a Service" and a sub tab called "Freezer".

