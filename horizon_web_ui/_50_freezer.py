# The name of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'freezer_ui'

# If set to True, this dashboard will not be added to the settings.
DISABLED = False

# Until there is a more elegant SYSPATH var scheme...
import sys
sys.path.append('/opt/stack/freezer')

# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = [
    'horizon_web_ui.freezer_ui',
]

