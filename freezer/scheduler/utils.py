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

import json
import os
import signal
import socket

from freezerclient import exceptions
from oslo_log import log
from oslo_utils import uuidutils
import psutil


LOG = log.getLogger(__name__)

CONFIG_FILE_EXT = '.conf'


def do_register(client, args=None):
    if client:
        client_info = {
            "client_id": client.client_id,
            "hostname": socket.gethostname()
        }
        try:
            client.clients.create(client_info)
        except exceptions.ApiClientException as e:
            if e.status_code == 409:
                print("Client already registered")
            return 73  # os.EX_CANTCREAT
        return 0  # os.EX_OK


def find_config_files(path):
    expanded_path = os.path.expanduser(path)
    if os.path.isfile(expanded_path):
        return [expanded_path]
    file_list = []
    if os.path.isdir(expanded_path):
        for fname in os.walk(expanded_path).next()[2]:
            if CONFIG_FILE_EXT.upper() == os.path.splitext(fname)[1].upper():
                file_list.append('{0}/{1}'.format(expanded_path, fname))
        return file_list
    raise Exception("unable to find job files at the provided path "
                    "{0}".format(path))


def load_doc_from_json_file(fname, debug=False):
    with open(fname, 'rb') as fd:
        try:
            doc = json.load(fd)
        except Exception as e:
            raise Exception("Unable to load conf file. {0}".format(e))
        if debug:
            print("File {0} loaded: ".format(fname))
        return doc


def save_doc_to_json_file(doc, fname, debug=False):
    with open(fname, 'w') as fd:
        json.dump(doc, fd, indent=4)
    if debug:
        print('Saved doc to file: {0}'.format(fname))


def get_jobs_from_disk(path):
    job_doc_list = [
        load_doc_from_json_file(f) for f in find_config_files(path)]
    for job_doc in job_doc_list:
        if job_doc:
            job_doc['job_id'] = job_doc.get('job_id', uuidutils.generate_uuid(
                dashed=False))
    return [x for x in job_doc_list if x]


def save_jobs_to_disk(job_doc_list, path):
    for doc in job_doc_list:
        fname = os.path.normpath('{0}/job_{1}.conf'.
                                 format(path, doc['job_id']))
        save_doc_to_json_file(doc, fname)


def get_active_jobs_from_api(client):
    # might raise
    search = {"match_not": [{"status": "completed"}]}
    job_list, offset = [], 0
    while True:
        jobs = client.jobs.list(limit=10, offset=offset, search=search)
        job_list.extend(jobs)
        if len(jobs) < 10:
            break
        offset += len(jobs)
    return job_list


def terminate_subprocess(pid, name):
    try:
        process = psutil.Process(pid)
        if process.name.startswith(name):
            os.kill(pid, signal.SIGTERM)
        else:
            LOG.warning('The name {} does not match the pid {}'.format(
                name, pid))
    except Exception:
        LOG.debug('Process {} does not exists anymore'.format(pid))
