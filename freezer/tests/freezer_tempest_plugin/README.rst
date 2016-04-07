===============================================
Tempest Integration of Freezer
===============================================

This directory contains Tempest tests to cover the freezer project.


Instructions for Running/Developing Tempest Tests with Freezer Project

1. Need Devstack or other Environment for running Keystone

2. Clone the Tempest Repo

3. Create virtual env for Tempest

4. Activate the Tempest virtual env
	run 'source ~/virtualenvs/tempest-freezer/bin/activate'

5. Make sure you have latest pip installed
	run 'pip install --upgrade pip'

6. install Tempest requirements.txt and test-requirements.txt in the Tempest
virtual env
	run 'pip install -r requirements.txt -r test-requirements.txt'

7. Install Tempest project into virtual env
	run ‘python setup.py develop’

8. Create logging.conf in Tempest Repo home dir/etc

	Make a copy of logging.conf.sample as logging.conf

	In logging configuration

	You will see this error on Mac OS X

	socket.error: [Errno 2] No such file or directory
	Edit logging.conf

	Change ‘/dev/log/ to '/var/run/syslog’ in logging.conf

	see: https://github.com/baremetal/python-backoff/issues/1

9. Create tempest.conf in Tempest Repo home dir/etc

	run 'oslo-config-generator --config-file etc/config-generator.tempest.conf --output-file etc/tempest.conf'

	Add the following sections to tempest.conf

        [identity]

        username = freezer
        password = secretservice
        tenant_name = service
        domain_name = default
        admin_username = admin
        admin_password = secretadmin
        admin_domain_name = default
        admin_tenant_name = admin
        alt_username = admin
        alt_password = secretadmin
        alt_tenant_name = admin
        use_ssl = False
        auth_version = v3
        uri = http://10.10.10.6:5000/v2.0/
        uri_v3 = http://10.10.10.6:35357/v3/

        [auth]

        allow_tenant_isolation = true
        tempest_roles = admin

    Modify the uri and the uri_v3 to point to the host where Keystone is
    running

10. Clone freezer Repo

11. Set virtualenv to the Tempest virtual env
	run 'source ~/virtualenvs/tempest-freezer/bin/activate'

12. pip install freezer requirements.txt and test-requirements.txt in
Tempest virtualenv
	run 'pip install -r requirements.txt -r test-requirements.txt'

13. Install nose in virtual env
	run 'pip install nose'

14. Install freezer project into virtual env
	run ‘python setup.py develop’ in Tempest virtual env

15. Set project interpreter (pycharm) to Tempest virtual env

16. Create test config using Tempest virtual env as python interpreter
