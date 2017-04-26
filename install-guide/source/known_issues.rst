.. _known_issues:

Known Issues
============

Versions of falcon < 0.1.8
--------------------------

Versions of `falcon <https://falconframework.org/>`_ prior to 0.1.8 (to be precise,
before `this commit <https://github.com/falconry/falcon/commit/8805eb400e62f74ef548a39a597a0ac5948cd57e>`_)
do not have support for error handlers, which are used internally by freezer-api
to specify the outcomes of various actions.

The absence of this error handling support means that freezer-api **will not start**
on systems running the following, otherwise supported stable versions of
falcon:

* 0.1.6
* 0.1.7

falcon 0.1.8, which was released on Jan 14, 2014, and all newer versions support
this functionality.