========================
Freezer - Horizon Web UI
========================

Installation
============

In the installation procedure we'll assume your main Horizon dashboard
directory is /opt/stack/horizon/openstack_dashboard/dashboards/.


To install the horizon web ui you need to do the following::

    # git clone https://github.com/stackforge/freezer

    # cd freezer/horizon_web_ui

    # cp _50_freezer.py  /opt/stack/horizon/openstack_dashboard/local/enabled/
    
    # modify _50_freezer.py (line 9) and point the path to the freezer repo.

    # /opt/stack/horizon/tools/with_venv.sh pip install parsedatetime

    # In horizons local_settings.py add the variable FREEZER_API_URL and set it
      to the url of the freezer api server. Example:

        FREEZER_API_URL = 'http://127.0.0.1:9090'

    # cd /opt/stack/horizon/

    # ./run_tests.sh --runserver 0.0.0.0:8000


Now a new Tab is available in the dashboard lists on the left, called "Backup
Restore DR".

Running the unit tests
======================

1. Create a virtual environment: 
       virtualenv --no-site-packages -p /usr/bin/python2.7 .venv

2. Activate the virtual environment:
       . ./.venv/bin/activate

3. Install the requirements: 
       pip install -r test-requirements.txt

4. Run the tests:
       python manage.py test . --settings=freezer_ui.tests.settings       

Test coverage
-------------

1. Collect coverage information:
       coverage run --source='.' --omit='.venv/*' manage.py test . --settings=freezer_ui.tests.settings

2. View coverage report:
       coverage report
