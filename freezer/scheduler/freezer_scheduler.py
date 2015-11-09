#!/usr/bin/env python
"""
Copyright 2015 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import logging
import os
import sys
import threading
from distutils import spawn

from apscheduler.schedulers.blocking import BlockingScheduler

from freezer.apiclient import client

import arguments
import shell
import utils

from daemon import Daemon, NoDaemon
from scheduler_job import Job


class FreezerScheduler(object):
    def __init__(self, apiclient, interval, job_path):
        # config_manager
        self.client = apiclient
        self.freezerc_executable = spawn.find_executable('freezerc')
        if self.freezerc_executable is None:
            # Needed in the case of a non-activated virtualenv
            self.freezerc_executable = spawn.find_executable(
                'freezerc', path=':'.join(sys.path))
        self.job_path = job_path
        self._client = None
        self.lock = threading.Lock()
        self.execution_lock = threading.Lock()
        job_defaults = {
            'coalesce': True,
            'max_instances': 1
        }
        self.scheduler = BlockingScheduler(job_defaults=job_defaults)
        if self.client:
            self.scheduler.add_job(self.poll, 'interval',
                                   seconds=interval, id='api_poll')

        self.add_job = self.scheduler.add_job
        self.remove_job = self.scheduler.remove_job
        self.jobs = {}

    def get_jobs(self):
        if self.client:
            job_doc_list = utils.get_active_jobs_from_api(self.client)
            try:
                utils.save_jobs_to_disk(job_doc_list, self.job_path)
            except Exception as e:
                logging.error('Unable to save jobs to {0}. '
                              '{1}'.format(self.job_path, e))
            return job_doc_list
        else:
            return utils.get_jobs_from_disk(self.job_path)

    def start_session(self, session_id, job_id, session_tag):
        if self.client:
            return self.client.sessions.start_session(session_id,
                                                      job_id,
                                                      session_tag)
        else:
            raise Exception("Unable to start session: api not in use.")

    def end_session(self, session_id, job_id, session_tag, result):
        if self.client:
            return self.client.sessions.end_session(session_id,
                                                    job_id,
                                                    session_tag,
                                                    result)
        else:
            raise Exception("Unable to end session: api not in use.")

    def upload_metadata(self, metadata_doc):
        if self.client:
            self.client.backups.create(metadata_doc)

    def start(self):
        utils.do_register(self.client)
        self.poll()
        self.scheduler.start()

    def update_job(self, job_id, job_doc):
        if self.client:
            try:
                return self.client.jobs.update(job_id, job_doc)
            except Exception as e:
                logging.error("[*] Job update error: {0}".format(e))

    def update_job_status(self, job_id, status):
        doc = {'job_schedule': {'status': status}}
        self.update_job(job_id, doc)

    def is_scheduled(self, job_id):
        return self.scheduler.get_job(job_id) is not None

    def create_job(self, job_doc):
        job = Job.create(self, self.freezerc_executable, job_doc)
        if job:
            self.jobs[job.id] = job
            logging.info("Created job {0}".format(job.id))
        return job

    def poll(self):
        try:
            work_job_doc_list = self.get_jobs()
        except Exception as e:
            logging.error("[*] Unable to get jobs: {0}".format(e))
            return

        work_job_id_list = []

        # create job if necessary, then let it process its events
        for job_doc in work_job_doc_list:
            job_id = job_doc['job_id']
            work_job_id_list.append(job_id)
            job = self.jobs.get(job_id, None) or self.create_job(job_doc)
            if job:
                job.process_event(job_doc)

        # request removal of any job that has been removed in the api
        for job_id, job in self.jobs.iteritems():
            if job_id not in work_job_id_list:
                job.remove()

        remove_list = [job_id for job_id, job in self.jobs.items()
                       if job.can_be_removed()]

        for k in remove_list:
            self.jobs.pop(k)

    def stop(self):
        try:
            self.scheduler.shutdown(wait=False)
        except:
            pass

    def reload(self):
        logging.warning("reload not supported")


def _get_doers(module):
    doers = {}
    for attr in (a for a in dir(module) if a.startswith('do_')):
        command = attr[3:].replace('_', '-')
        callback = getattr(module, attr)
        doers[command] = callback
    return doers


def main():
    doers = _get_doers(shell)
    doers.update(_get_doers(utils))

    possible_actions = doers.keys() + ['start', 'stop', 'status']

    args = arguments.get_args(possible_actions)

    if args.action is None:
        print ('No action')
        return os.EX_DATAERR

    apiclient = None

    if args.no_api is False:
        apiclient = client.Client(opts=args)
        if args.client_id:
            apiclient.client_id = args.client_id

    if args.action in doers:
        try:
            return doers[args.action](apiclient, args)
        except Exception as e:
            print ('ERROR {0}'.format(e))
            return os.EX_SOFTWARE

    freezer_scheduler = FreezerScheduler(apiclient=apiclient,
                                         interval=int(args.interval),
                                         job_path=args.jobs_dir)

    if args.no_daemon:
        print ('Freezer Scheduler running in no-daemon mode')
        daemon = NoDaemon(daemonizable=freezer_scheduler)
    else:
        daemon = Daemon(daemonizable=freezer_scheduler)

    if args.action == 'start':
        daemon.start(log_file=args.log_file)
    elif args.action == 'stop':
        daemon.stop()
    elif args.action == 'reload':
        daemon.reload()
    elif args.action == 'status':
        daemon.status()

    return os.EX_OK


if __name__ == '__main__':
    sys.exit(main())
