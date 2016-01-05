..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode

..

==========================================
 Creation of the python-freezerclient repo
==========================================

Include the URL of your launchpad blueprint:

* https://blueprints.launchpad.net/freezer/+spec/freezerclient

Freezer needs to align to the other Openstack projects and have a dedicated
repo/client to communicate with the API and the storage media.

Problem description
===================

Currently the related freezer code to talk to the API and
query the storage media is hosted in the openstack/freezer repo.

We would like to follow the same convention/organization as
other OpenStack projects and place the code on a dedicated repo,
hoping also to reduce complexity and increase readability.

Proposed change
===============

Split the code and placing it in a new dedicated repo. Currently some code related
code (i.e. list backups, registered clients, etc) is located in the scheduler
code in the openstack/freezer repo. The following code most likely needs to be
moved to the new openstack/python-freezerclient repo:

* freezer/freezer/apiclient

* apiclient needs to be renamed to freezerclient

* apiclient is used by the scheduler (freezer/freezer/scheduler) and by the web ui
    We need to make sure the namespace change, module import and dependancies
    are reflected also in the scheduler and the web ui

python-freezerclient responsibilities
-------------------------------------

* Retrieve and display nicely metadata information, metrics and stats, from the freezer-api
* Retrieve and display nicely metadata information, metrics and stats from the storage media (i.e. swift)
* Perform basic maintenance instruction like remove old backups

Projects
========

List the projects that this spec effects. (for now only Freezer) For example:

* openstack/freezer
* openstack/freezer-web-ui
* openstack/freezer-api
* openstack/python-freezerclient

Implementation
==============

Milestones
----------

Target Milestone for completion:
  Mitaka-2

Work Items
----------

1) Create the python-freezerclient repo on openstack-infra/project-config

2) Move freezer/freezer/apiclient to the python-freezerclient repo

3) Change the naming convention and imports from apiclient to freezerclient within the apiclient

4) Change the naming convention, import and deps on the freezer-scheduler and freezer-web-ui

5) Create a pypi packge called python-freezerclient

6) Add the code to extract the information from the object media in case the freezer api are not avaialble (most probably a separated item).

