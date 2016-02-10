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

import json
import os
import six
import utils

from prettytable import PrettyTable

try:
    from betterprint import pprint
except Exception:
    def pprint(doc):
        print(json.dumps(doc, indent=4))

from freezer.utils import create_dir


def do_session_remove_job(client, args):
    """
    remove the job from the session
    """
    if not args.session_id:
        raise Exception("Parameter --session required")
    if not args.job_id:
        raise Exception("Parameter --job required")
    client.sessions.remove_job(args.session_id, args.job_id)


def do_session_add_job(client, args):
    """
    adds a job to the session
    """
    if not args.session_id:
        raise Exception("Parameter --session required")
    if not args.job_id:
        raise Exception("Parameter --job required")
    for job_id in args.job_id.split(','):
        try:
            client.sessions.add_job(args.session_id, job_id)
        except Exception as e:
            print("Error processin job {0}. {1}".format(job_id, e))


def do_session_list_job(client, args):
    """
    prints a list of jobs assigned to the specific session

    :return: None
    """
    if not args.session_id:
        raise Exception("Parameter --session required")
    session_doc = client.sessions.get(args.session_id)
    jobs = session_doc.get('jobs', {})
    table = PrettyTable(["job_id", "status", "result", "client_id"])
    for job_id, job_data in six.iteritems(jobs):
        table.add_row([job_id,
                       job_data['status'],
                       job_data['result'],
                       job_data['client_id']
                       ])
    print(table)


def do_session_delete(client, args):
    if not args.session_id:
        raise Exception("Parameter --session required")
    client.sessions.delete(args.session_id)


def do_session_create(client, args):
    """
    creates a session object loading it from disk

    :return: None
    """
    if not args.fname:
        raise Exception("Parameter --file required")
    session_doc = utils.load_doc_from_json_file(args.fname)
    session_id = client.sessions.create(session_doc)
    print ("Created session {0}".format(session_id))


def do_session_get(client, args):
    """
    gets a specific session object and saves it to file. If file is not
    specified the session obj is printed.
    :return: None
    """
    if not args.session_id:
        raise Exception("Parameter --session required")
    session_doc = client.sessions.get(args.session_id)
    if args.fname:
        utils.save_doc_to_json_file(session_doc, args.fname)
    else:
        pprint(session_doc)


def do_session_list(client, args):
    """
    print a list of all jobs

    :return: None
    """
    table = PrettyTable(["session_id", "tag", "status",
                         "description", "jobs", "last_start"])
    session_docs = client.sessions.list()
    offset = 0
    while session_docs:
        offset += len(session_docs)
        for doc in session_docs:
            table.add_row([doc['session_id'],
                           doc['session_tag'],
                           doc['status'],
                           doc.get('description', ''),
                           len(doc.get('jobs', [])),
                           doc['last_start']])
        session_docs = client.sessions.list(offset=offset)
    print(table)


def do_job_create(client, args):
    if not args.fname:
        raise Exception("Parameter --file required")
    job_doc = utils.load_doc_from_json_file(args.fname)
    job_id = client.jobs.create(job_doc)
    print("Created job {0}".format(job_id))


def do_job_delete(client, args):
    if not args.job_id:
        raise Exception("Parameter --job required")
    client.jobs.delete(args.job_id)


def do_job_get(client, args):
    if not args.job_id:
        raise Exception("Parameter --job required")
    job_doc = client.jobs.get(args.job_id)
    if args.fname:
        args.save_doc_to_file(job_doc, args.fname)
    else:
        pprint(job_doc)


def do_job_start(client, args):
    if not args.job_id:
        raise Exception("Parameter --job required")
    client.jobs.start_job(args.job_id)
    print("Job {0} started".format(args.job_id))


def do_job_stop(client, args):
    if not args.job_id:
        raise Exception("Parameter --job required")
    client.jobs.stop_job(args.job_id)
    print("Job {0} stopped".format(args.job_id))


def do_job_download(client, args):
    create_dir(args.jobs_dir, do_log=True)
    for doc in _job_list(client, args):
        fname = os.path.normpath('{0}/job_{1}.conf'.
                                 format(args.jobs_dir, doc['job_id']))
        try:
            utils.save_doc_to_json_file(doc, fname)
        except Exception:
            print("Unable to write to file {0}".format(fname))


def do_job_upload(client, args):
    for job_doc in utils.get_jobs_from_disk(args.jobs_dir):
        job_id = client.jobs.create(job_doc)
        print("Uploaded job {0}".format(job_id))


def _job_list(client, args):
    search = {}
    if args.active_only:
        search = {"match_not": [{"status": "completed"}]}
    client_docs = client.jobs.list(search=search)
    offset = 0
    while client_docs:
        offset += len(client_docs)
        for doc in client_docs:
            yield doc
        client_docs = client.jobs.list(offset=offset, search=search)
    raise StopIteration


def do_job_list(client, args):
    table = PrettyTable(["job_id", "description", "# actions",
                         "status", "event", "result", "session_id"])
    for doc in _job_list(client, args):
        job_scheduling = doc.get('job_schedule', {})
        job_status = job_scheduling.get('status', '')
        job_event = job_scheduling.get('event', '')
        job_result = job_scheduling.get('result', '')
        table.add_row([doc['job_id'],
                       doc.get('description', ''),
                       len(doc.get('job_actions', [])),
                       job_status,
                       job_event,
                       job_result,
                       doc.get('session_id', '')])
    print(table)


def do_client_list(client, args):
    table = PrettyTable(["client_id", "hostname", "description"])
    l = client.registration.list()
    offset = 0
    while l:
        offset += len(l)
        for doc in l:
            client_doc = doc['client']
            table.add_row([client_doc['client_id'],
                           client_doc.get('hostname', ''),
                           client_doc.get('description', '')])
        l = client.registration.list(offset=offset)
    print(table)
