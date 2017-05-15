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
LOG = log.getLogger(__name__)


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
        return StopState.stop(job, doc)

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
        job.scheduler.update_job(job.id, job.job_doc)
        return Job.ABORTED_RESULT

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

    TIME_NULL = -1

    @staticmethod
    def create(scheduler, executable, job_doc):
        job = Job(scheduler, executable, job_doc)
        if job.job_doc_status in ['running', 'scheduled']:
            LOG.warning('Resetting {0} status from job {1}'
                        .format(job.job_doc_status, job.id))
        if job.job_doc_status == 'stop' and not job.event:
            LOG.info('Job {0} was stopped.'.format(job.id))
            job.event = Job.STOP_EVENT
        elif not job.event:
            LOG.info('Autostart Job {0}'.format(job.id))
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
            LOG.info('REMOVE job {0}'.format(self.id))
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
    def schedule_start_date(self):
        return self.job_doc['job_schedule'].get('schedule_start_date', '')

    @property
    def schedule_end_date(self):
        return self.job_doc['job_schedule'].get('schedule_end_date', '')

    @property
    def schedule_cron_fields(self):
        cron_fields = ['year', 'month', 'day', 'week', 'day_of_week',
                       'hour', 'minute', 'second']
        cron_schedule = {}
        for cron in self.job_doc['job_schedule'].keys():
            if cron.startswith('schedule_'):
                cron_key = cron.split('_', 1)[1]
                cron_schedule.update({
                    cron_key: self.job_doc['job_schedule'][cron]})
        return {key: value
                for key, value in cron_schedule.items()
                if key in cron_fields}

    @property
    def scheduled(self):
        return self.scheduler.is_scheduled(self.id)

    def get_schedule_args(self):
        def get_start_date(date):
            # start_date format "%Y-%m-%dT%H:%M:%S"
            now = datetime.datetime.now()
            start_date = now + datetime.timedelta(0, 2, 0)
            if (utils.date_to_timestamp(date) >
                    utils.date_to_timestamp(now.isoformat().split('.')[0])):
                start_date = datetime.datetime.strptime(
                    date, "%Y-%m-%dT%H:%M:%S")
            return start_date

        def get_end_date(start, end):
            # start end format "%Y-%m-%dT%H:%M:%S"
            end_date = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
            if (utils.date_to_timestamp(start) > utils.date_to_timestamp(end)):
                end_date = None
            return end_date
        kwargs_date = {}
        if self.schedule_start_date:
            kwargs_date.update({
                'start_date': get_start_date(self.schedule_start_date)
            })
            if self.schedule_end_date:
                end_date = get_end_date(self.schedule_start_date,
                                        self.schedule_end_date)
                kwargs_date.update({
                    'end_date': end_date
                })

        if self.schedule_date:
            return {'trigger': 'date',
                    'run_date': self.schedule_date}
        elif self.schedule_interval:
            kwargs = {'trigger': 'interval'}
            kwargs.update(kwargs_date)
            if self.schedule_interval == 'continuous':
                kwargs.update({'seconds': 1})
            else:
                val, unit = self.schedule_interval.split(' ')
                kwargs.update({unit: int(val)})
            return kwargs
        elif self.schedule_cron_fields:
            kwargs = {'trigger': 'cron'}
            kwargs.update(kwargs_date)
            cron_fields = self.schedule_cron_fields
            kwargs.update(cron_fields)
            return kwargs
        else:
            # no scheduling information, schedule to start within a few seconds
            return {'trigger': 'date',
                    'run_date': datetime.datetime.now() +
                    datetime.timedelta(0, 2, 0)}

    def process_event(self, job_doc):
        with self.scheduler.lock:
            next_event = job_doc['job_schedule'].get('event', '')
            while next_event:
                if next_event == Job.STOP_EVENT:
                    if isinstance(self.state(), StopState):
                        LOG.info('JOB {0} event: STOP'.format(self.id))
                    next_event = self.state.stop(self, job_doc)
                elif next_event == Job.START_EVENT:
                    LOG.info('JOB {0} event: START'.format(self.id))
                    next_event = self.state.start(self, job_doc)
                elif next_event == Job.ABORT_EVENT:
                    LOG.info('JOB {0} event: ABORT'.format(self.id))
                    next_event = self.state.abort(self, job_doc)
                elif next_event == Job.ABORTED_RESULT:
                    LOG.info('JOB {0} aborted.'.format(self.id))
                    break

    def upload_metadata(self, metadata_string):
        try:
            metadata = json.loads(metadata_string)
            if metadata:
                metadata['job_id'] = self.id
                self.scheduler.upload_metadata(metadata)
                LOG.info("Job {0}, freezer action metadata uploaded"
                         .format(self.id))
        except Exception as e:
            LOG.error('metrics upload error: {0}'.format(e))

    def execute_job_action(self, job_action):
        max_tries = (job_action.get('max_retries', 0) + 1)
        tries = max_tries
        freezer_action = job_action.get('freezer_action', {})
        max_retries_interval = job_action.get('max_retries_interval', 60)
        action_name = freezer_action.get('action', '')
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

                # store the pid for this process in the api
                try:
                    self.job_doc['job_schedule']['current_pid'] = \
                        self.process.pid

                    self.scheduler.update_job(self.job_doc['job_id'],
                                              self.job_doc)
                except Exception as error:
                    LOG.error("Error saving the process id {}".format(error))

                output, error = self.process.communicate()
                # ensure the tempfile gets deleted
                utils.delete_file(config_file_name)

            if error:
                LOG.error("Freezer client error: {0}".format(error))
            elif output:
                self.upload_metadata(output)

            if self.process.returncode == -15:
                # This means the job action was aborted by the scheduler
                LOG.warning('Freezer-agent was killed by the scheduler. '
                            'Cleanup should be done manually: container, '
                            'mountpoint and lvm snapshots.')
                return Job.ABORTED_RESULT

            elif self.process.returncode:
                # ERROR
                tries -= 1
                if tries:
                    LOG.warning('Job {0} failed {1} action,'
                                ' retrying in {2} seconds'
                                .format(self.id, action_name,
                                        max_retries_interval))
                    time.sleep(max_retries_interval)
            else:
                # SUCCESS
                LOG.info('Job {0} action {1}'
                         ' returned success exit code'.
                         format(self.id, action_name))
                return Job.SUCCESS_RESULT
        LOG.error('Job {0} action {1} failed after {2} tries'
                  .format(self.id, action_name, max_tries))

        return Job.FAIL_RESULT

    def contains_exec(self):
        jobs = self.job_doc.get('job_actions')
        for job in jobs:
            freezer_action = job.get('freezer_action')
            action = freezer_action.get('action')
            if action == 'exec':
                return True
        return False

    def update_job_schedule_doc(self, **kwargs):
        """
        Updates the job_schedule section of the job doc with the
        provided keyword args. No checks about accepted key/values
        are being made here since they may vary in the future.

        :param kwargs: keyword args to add
        :return: None
        """
        job_schedule = self.job_doc['job_schedule']
        job_schedule.update(kwargs)

    def execute(self):
        result = Job.SUCCESS_RESULT
        with self.scheduler.lock:
            LOG.info('job {0} running'.format(self.id))
            self.state = RunningState
            self.update_job_schedule_doc(status=Job.RUNNING_STATUS,
                                         result="",
                                         time_started=int(time.time()),
                                         time_ended=Job.TIME_NULL)
            self.scheduler.update_job_schedule(
                self.id,
                self.job_doc['job_schedule'])

        self.start_session()
        # if the job contains exec action and the scheduler passes the
        # parameter --disable-exec job execution should fail
        if self.contains_exec() and CONF.disable_exec:
            LOG.info("Job {0} failed because it contains exec action "
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

                if action_result == Job.ABORTED_RESULT:
                    result = Job.ABORTED_RESULT
            else:
                freezer_action = job_action.get('freezer_action', {})
                action_name = freezer_action.get('action', '')
                LOG.warning("skipping {0} action".
                            format(action_name))
        self.result = result
        self.finish()

    def finish(self):
        self.update_job_schedule_doc(time_ended=int(time.time()))
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
                self.scheduler.update_job_schedule(
                    self.id,
                    self.job_doc['job_schedule'])

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
                LOG.error('Error while starting session {0}. {1}'.
                          format(self.session_id, e))
            LOG.warning('Retrying to start session {0}'.
                        format(self.session_id))
            retry -= 1
        LOG.error('Unable to start session {0}'.format(self.session_id))

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
                LOG.error('Error while ending session {0}. {1}'.
                          format(self.session_id, e))
            LOG.warning('Retrying to end session {0}'.
                        format(self.session_id))
            retry -= 1
        LOG.error('Unable to end session {0}'.format(self.session_id))

    def schedule(self):
        try:
            kwargs = self.get_schedule_args()
            self.scheduler.add_job(self.execute, id=self.id,
                                   executor='threadpool',
                                   misfire_grace_time=3600, **kwargs)
        except Exception as e:
            LOG.error("Unable to schedule job {0}: {1}".
                      format(self.id, e))

        LOG.info('scheduler job with parameters {0}'.format(kwargs))

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
