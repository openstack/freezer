============================
Enabling Freezer in Devstack
============================

This directory contains the Freezer DevStack plugin.

Download Devstack::

    git clone https://git.openstack.org/openstack-dev/devstack
    cd devstack

To configure the Freezer scheduler and agent with DevStack, you will need to
enable this plugin by adding one line to the [[local|localrc]]
section of your ``local.conf`` file.

To enable the plugin, add a line of the form::

    [[local|localrc]]
    enable_plugin freezer <GITURL> [GITREF]

where::

    <GITURL> is the URL of a freezer repository
    [GITREF] is an optional git ref (branch/ref/tag).  The default is master.

For example::

    enable_plugin freezer https://git.openstack.org/openstack/freezer master

Then run devstack normally::

    cd $DEVICE_DIR
    ./stack.sh

This is a sample ``local.conf`` file for freezer developer::

    [[local|localrc]]
    ADMIN_PASSWORD=stack
    DATABASE_PASSWORD=stack
    RABBIT_PASSWORD=stack
    SERVICE_PASSWORD=$ADMIN_PASSWORD

    DEST=/opt/stack
    LOGFILE=$DEST/logs/stack.sh.log

    # only install keystone/horizon/swift in devstack
    # disable_all_services
    # enable_service key mysql s-proxy s-object s-container s-account horizon

    enable_plugin freezer http://git.openstack.org/openstack/freezer master
    enable_plugin freezer-api http://git.openstack.org/openstack/freezer-api.git master
    enable_plugin freezer-tempest-plugin http://git.openstack.org/openstack/freezer-tempest-plugin.git master
    enable_plugin freezer-web-ui http://git.openstack.org/openstack/freezer-web-ui.git master

    export FREEZER_BACKEND='sqlalchemy'

For more information, see:
 https://docs.openstack.org/devstack/latest/index.html
