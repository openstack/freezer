This directory contains the Freezer DevStack plugin.

To configure the Freezer scheduler and agent with DevStack, you will need to
enable this plugin by adding one line to the [[local|localrc]]
section of your local.conf file.

To enable the plugin, add a line of the form::

    enable_plugin freezer <GITURL> [GITREF]

where::

    <GITURL> is the URL of a freezer repository
    [GITREF] is an optional git ref (branch/ref/tag).  The default is master.

For example::

    enable_plugin freezer https://git.openstack.org/openstack/freezer.git master


For more information, see:
 http://docs.openstack.org/developer/devstack/plugins.html
