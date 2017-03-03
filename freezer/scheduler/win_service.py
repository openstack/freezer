# Copyright 2014 Hewlett-Packard
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import servicemanager
import sys
import win32event
import win32service
import win32serviceutil

from freezer.utils import winutils


class PySvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "FreezerService"
    _svc_display_name_ = "Freezer Service"
    _svc_description_ = "Freezer Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # create an event to listen for stop requests on
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.home = r'C:\.freezer'
        self.insecure = False

    def SvcDoRun(self):
        """Run the windows service and start the scheduler in the background
        """
        rc = None

        self.main()

        # if the stop event hasn't been fired keep looping
        while rc != win32event.WAIT_OBJECT_0:
            # block for 5 seconds and listen for a stop event
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)

    def SvcStop(self):
        """Stop the windows service and stop the scheduler instance
        """
        # tell the SCM we're shutting down
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # fire the stop event
        servicemanager.LogInfoMsg("freezer-scheduler stopped")
        win32event.SetEvent(self.hWaitStop)

    def main(self):
        from freezer.scheduler.freezer_scheduler import FreezerScheduler
        from freezerclient.v1.client import Client

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ''))

        winutils.set_environment(self.home)

        if os.environ.get('SERVICE_INSECURE'):
            self.insecure = True

        # Add support for keystone v2 and v3
        credentials = {}
        if os.environ['OS_IDENTITY_API_VERSION'] == 2:
            credentials = {
                'version': 2,
                'username': os.environ['OS_USERNAME'],
                'password': os.environ['OS_PASSWORD'],
                'auth_url': os.environ['OS_AUTH_URL'],
                'endpoint': os.environ['OS_BACKUP_URL'],
                'tenant_name': os.environ['OS_TENANT_NAME'],
                'insecure': self.insecure
            }
        elif os.environ['OS_IDENTITY_API_VERSION'] == 3:
            credentials = {
                'version': 3,
                'username': os.environ['OS_USERNAME'],
                'password': os.environ['OS_PASSWORD'],
                'auth_url': os.environ['OS_AUTH_URL'],
                'endpoint': os.environ['OS_BACKUP_URL'],
                'project_name': os.environ['OS_PROJECT_NAME'],
                'user_domain_name': os.environ['OS_USER_DOMAIN_NAME'],
                'project_domain_name': os.environ['OS_PROJECT_DOMAIN_NAME'],
                'insecure': self.insecure
            }

        client = Client(**credentials)

        scheduler = FreezerScheduler(
            apiclient=client, interval=int(os.environ['SERVICE_INTERVAL']),
            job_path=os.environ['SERVICE_JOB_PATH'],
            concurrent_jobs=int(os.environ['SERVICE_CONCURRENT_JOBS']))

        scheduler.start()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PySvc)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PySvc)
