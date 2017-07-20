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

For more information, see:
 https://docs.openstack.org/devstack/latest/plugins.html
