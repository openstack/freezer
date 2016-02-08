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

import datetime
import json
import os
import subprocess
import tempfile
import time

from freezer.utils import utils
from oslo_config import cfg
from oslo_log import log
from six.moves import configparser


CONF = cfg.CONF
logging = log.getLogger(__name__)


class StopState(object):

    @staticmethod
    def stop(job, doc):
        job.job_doc = doc
        job.event = Job.NO_EVENT
        job.job_doc_status = Job.STOP_STATUS
        job.scheduler.update_job(job.id, job.job_doc)
        return Job.NO_EVENT

    @staticmethod
    def abort(job, doc):
        return StopState.stop(job, doc)

    @staticmethod
    def start(job, doc):
        job.job_doc = doc
        job.event = Job.NO_EVENT
        job.job_doc_status = Job.STOP_STATUS
        job.schedule()
        job.scheduler.update_job(job.id, job.job_doc)
        return Job.NO_EVENT

    @staticmethod
    def remove(job):
        job.unschedule()
        job.job_doc_status = Job.REMOVED_STATUS
        return Job.NO_EVENT


class ScheduledState(object):

    @staticmethod
    def stop(job, doc):
        job.unschedule()
        job.scheduler.update_job(job.id, job.job_doc)
        return Job.STOP_EVENT

    @staticmethod
    def abort(job, doc):
        return ScheduledState.stop(job, doc)

    @staticmethod
    def start(job, doc):
        job.event = Job.NO_EVENT
        job.scheduler.update_job(job.id, job.job_doc)
        return Job.NO_EVENT

    @staticmethod
    def remove(job):
        job.unschedule()
        job.job_doc_status = Job.REMOVED_STATUS
        return Job.NO_EVENT


class RunningState(object):

    @staticmethod
    def stop(job, doc):
        job.event = Job.STOP_EVENT
        return Job.NO_EVENT

    @staticmethod
    def abort(job, doc):
        job.event = Job.ABORT_EVENT
        return Job.NO_EVENT

    @staticmethod
    def start(job, doc):
        job.event = Job.NO_EVENT
        job.scheduler.update_job(job.id, job.job_doc)
        return Job.NO_EVENT

    @staticmethod
    def remove(job):
        job.event = Job.REMOVE_EVENT
        return Job.NO_EVENT


class Job(object):

    NO_EVENT = ''
    STOP_EVENT = 'stop'
    START_EVENT = 'start'
    ABORT_EVENT = 'abort'
    REMOVE_EVENT = 'remove'

    STOP_STATUS = 'stop'
    SCHEDULED_STATUS = 'scheduled'
    RUNNING_STATUS = 'running'
    REMOVED_STATUS = 'removed'
    COMPLETED_STATUS = 'completed'

    FAIL_RESULT = 'fail'
    SUCCESS_RESULT = 'success'
    ABORTED_RESULT = 'aborted'

    @staticmethod
    def create(scheduler, executable, job_doc):
        job = Job(scheduler, executable, job_doc)
        if job.job_doc_status in ['running', 'scheduled']:
            logging.warning('Resetting {0} status from job {1}'
                            .format(job.job_doc_status, job.id))
        if job.job_doc_status == 'stop' and not job.event:
            logging.info('Job {0} was stopped.'.format(job.id))
            job.event = Job.STOP_EVENT
        elif not job.event:
            logging.info('Autostart Job {0}'.format(job.id))
            job.event = Job.START_EVENT
        return job

    def __init__(self, scheduler, executable, job_doc):
        self.scheduler = scheduler
        self.executable = executable
        self.job_doc = job_doc
        self.process = None
        self.state = StopState

    def remove(self):
        with self.scheduler.lock:
            # delegate to state object
            logging.info('REMOVE job {0}'.format(self.id))
            self.state.remove(self)

    @property
    def id(self):
        return self.job_doc['job_id']

    @property
    def session_id(self):
        return self.job_doc.get('session_id', '')

    @session_id.setter
    def session_id(self, value):
        self.job_doc['session_id'] = value

    @property
    def session_tag(self):
        return self.job_doc.get('session_tag', 0)

    @session_tag.setter
    def session_tag(self, value):
        self.job_doc['session_tag'] = value

    @property
    def event(self):
        return self.job_doc['job_schedule'].get('event', '')

    @event.setter
    def event(self, value):
        self.job_doc['job_schedule']['event'] = value

    @property
    def job_doc_status(self):
        return self.job_doc['job_schedule'].get('status', '')

    @job_doc_status.setter
    def job_doc_status(self, value):
        self.job_doc['job_schedule']['status'] = value

    @property
    def result(self):
        return self.job_doc['job_schedule'].get('result', '')

    @result.setter
    def result(self, value):
        self.job_doc['job_schedule']['result'] = value

    def can_be_removed(self):
        return self.job_doc_status == Job.REMOVED_STATUS

    @staticmethod
    def save_action_to_file(action, f):
        parser = configparser.ConfigParser()
        parser.add_section('action')
        for action_k, action_v in action.items():
            parser.set('action', action_k, action_v)
        parser.write(f)
        f.seek(0)

    @property
    def schedule_date(self):
        return self.job_doc['job_schedule'].get('schedule_date', '')

    @property
    def schedule_interval(self):
        return self.job_doc['job_schedule'].get('schedule_interval', '')

    @property
    def schedule_cron_fields(self):
        cron_fields = ['year', 'month', 'day', 'week', 'day_of_week',
                       'hour', 'minute', 'second']
        return {key: value
                for key, value in self.job_doc['job_schedule'].items()
                if key in cron_fields}

    @property
    def scheduled(self):
        return self.scheduler.is_scheduled(self.id)

    def get_schedule_args(self):
        if self.schedule_date:
            return {'trigger': 'date',
                    'run_date': self.schedule_date}
        elif self.schedule_interval:
            kwargs = {'trigger': 'interval'}
            if not self.schedule_date:
                kwargs.update({
                    'start_date': datetime.datetime.now() +
                    datetime.timedelta(0, 2, 0)})
            if self.schedule_interval == 'continuous':
                kwargs.update({'seconds': 1})
            else:
                val, unit = self.schedule_interval.split(' ')
                kwargs.update({unit: int(val)})
            return kwargs
        else:
            cron_fields = self.schedule_cron_fields
            if cron_fields:
                return {'trigger': 'cron'}.update(cron_fields)
        # no scheduling information, schedule to start within a few seconds
        return {'trigger': 'date',
                'run_date': datetime.datetime.now() +
                datetime.timedelta(0, 2, 0)}

    def process_event(self, job_doc):
        with self.scheduler.lock:
            next_event = job_doc['job_schedule'].get('event', '')
            while next_event:
                if next_event == Job.STOP_EVENT:
                    logging.info('JOB {0} event: STOP'.format(self.id))
                    next_event = self.state.stop(self, job_doc)
                elif next_event == Job.START_EVENT:
                    logging.info('JOB {0} event: START'.format(self.id))
                    next_event = self.state.start(self, job_doc)
                elif next_event == Job.ABORT_EVENT:
                    logging.info('JOB {0} event: ABORT'.format(self.id))
                    next_event = self.state.abort(self, job_doc)

    def upload_metadata(self, metadata_string):
        try:
            metadata = json.loads(metadata_string)
            if metadata:
                metadata['job_id'] = self.id
                self.scheduler.upload_metadata(metadata)
                logging.info("[*] Job {0}, freezer action metadata uploaded"
                             .format(self.id))
        except Exception as e:
            logging.error('[*] metrics upload error: {0}'.format(e))

    def execute_job_action(self, job_action):
        max_retries = job_action.get('max_retries', 1)
        tries = max_retries
        freezer_action = job_action.get('freezer_action', {})
        max_retries_interval = job_action.get('max_retries_interval', 60)
        action_name = freezer_action.get('action', '')
        config_file_name = None
        while tries:

            with tempfile.NamedTemporaryFile(delete=False) as config_file:
                self.save_action_to_file(freezer_action, config_file)
                config_file_name = config_file.name
                freezer_command = '{0} --metadata-out - --config {1}'.\
                    format(self.executable, config_file.name)
                self.process = subprocess.Popen(freezer_command.split(),
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                env=os.environ.copy())
                output, error = self.process.communicate()
                # ensure the tempfile gets deleted
                utils.delete_file(config_file_name)

            if error:
                logging.error("[*] Freezer client error: {0}".format(error))
            elif output:
                self.upload_metadata(output)

            if self.process.returncode:
                # ERROR
                tries -= 1
                if tries:
                    logging.warning('[*] Job {0} failed {1} action,'
                                    ' retrying in {2} seconds'
                                    .format(self.id, action_name,
                                            max_retries_interval))
                    # sleeping with the bloody lock, but we don't want other
                    # actions to mess with our stuff like fs snapshots, do we ?
                    time.sleep(max_retries_interval)
            else:
                # SUCCESS
                logging.info('[*] Job {0} action {1}'
                             ' returned success exit code'.
                             format(self.id, action_name))
                return Job.SUCCESS_RESULT
        logging.error('[*] Job {0} action {1} failed after {2} tries'
                      .format(self.id, action_name, max_retries))

        return Job.FAIL_RESULT

    def contains_exec(self):
        jobs = self.job_doc.get('job_actions')
        for job in jobs:
            freezer_action = job.get('freezer_action')
            action = freezer_action.get('action')
            if action == 'exec':
                return True
        return False

    def execute(self):
        result = Job.SUCCESS_RESULT
        with self.scheduler.execution_lock:
            with self.scheduler.lock:
                logging.info('job {0} running'.format(self.id))
                self.state = RunningState
                self.job_doc_status = Job.RUNNING_STATUS
                self.scheduler.update_job_status(self.id, self.job_doc_status)

            self.start_session()
            # if the job contains exec action and the scheduler passes the
            # parameter --disable-exec job execution should fail
            if self.contains_exec() and CONF.disable_exec:
                logging.info("Job {0} failed because it contains exec action "
                             "and exec actions are disabled by scheduler"
                             .format(self.id))
                self.result = Job.FAIL_RESULT
                self.finish()
                return

            for job_action in self.job_doc.get('job_actions', []):
                if job_action.get('mandatory', False) or\
                        (result == Job.SUCCESS_RESULT):
                    action_result = self.execute_job_action(job_action)
                    if action_result == Job.FAIL_RESULT:
                        result = Job.FAIL_RESULT
                else:
                    freezer_action = job_action.get('freezer_action', {})
                    action_name = freezer_action.get('action', '')
                    logging.warning("[*]skipping {0} action".
                                    format(action_name))
            self.result = result
            self.finish()

    def finish(self):
        self.end_session(self.result)
        with self.scheduler.lock:
            if self.event == Job.REMOVE_EVENT:
                self.unschedule()
                self.job_doc_status = Job.REMOVED_STATUS
                return

            if not self.scheduled:
                self.job_doc_status = Job.COMPLETED_STATUS
                self.state = StopState
                self.scheduler.update_job(self.id, self.job_doc)
                return

            if self.event in [Job.STOP_EVENT, Job.ABORT_EVENT]:
                self.unschedule()
                self.job_doc_status = Job.COMPLETED_STATUS
                self.scheduler.update_job(self.id, self.job_doc)
            else:
                self.job_doc_status = Job.SCHEDULED_STATUS
                self.state = ScheduledState
                self.scheduler.update_job_status(self.id, self.job_doc_status)

    def start_session(self):
        if not self.session_id:
            return
        retry = 5
        while retry:
            try:
                resp = self.scheduler.start_session(self.session_id,
                                                    self.id,
                                                    self.session_tag)
                if resp['result'] == 'success':
                    self.session_tag = resp['session_tag']
                    return
            except Exception as e:
                logging.error('[*]Error while starting session {0}. {1}'.
                              format(self.session_id, e))
            logging.warning('[*]Retrying to start session {0}'.
                            format(self.session_id))
            retry -= 1
        logging.error('[*]Unable to start session {0}'.format(self.session_id))

    def end_session(self, result):
        if not self.session_id:
            return
        retry = 5
        while retry:
            try:
                resp = self.scheduler.end_session(self.session_id,
                                                  self.id,
                                                  self.session_tag,
                                                  result)
                if resp['result'] == 'success':
                    return
            except Exception as e:
                logging.error('[*]Error while ending session {0}. {1}'.
                              format(self.session_id, e))
            logging.warning('[*]Retrying to end session {0}'.
                            format(self.session_id))
            retry -= 1
        logging.error('[*]Unable to end session {0}'.format(self.session_id))

    def schedule(self):
        try:
            kwargs = self.get_schedule_args()
            self.scheduler.add_job(self.execute, id=self.id, **kwargs)
        except Exception as e:
            logging.error("[*] Unable to schedule job {0}: {1}".
                          format(self.id, e))

        logging.info('scheduler job with parameters {0}'.format(kwargs))

        if self.scheduled:
            self.job_doc_status = Job.SCHEDULED_STATUS
            self.state = ScheduledState
        else:
            # job not scheduled or already started and waiting for lock
            self.job_doc_status = Job.COMPLETED_STATUS
            self.state = StopState

    def unschedule(self):
        try:
            # already executing job are not present in the apscheduler list
            self.scheduler.remove_job(job_id=self.id)
        except Exception:
            pass
        self.event = Job.NO_EVENT
        self.job_doc_status = Job.STOP_STATUS
        self.state = StopState

    def terminate(self):
        if self.process:
            self.process.terminate()

    def kill(self):
        if self.process:
            self.process.kill()
