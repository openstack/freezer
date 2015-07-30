# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
URL patterns for the OpenStack Dashboard.
"""

from django.conf.urls import patterns
from django.conf.urls import url

import rest_api

urlpatterns = patterns(
    '',
    url(r'^api/clients$', rest_api.Clients.as_view(), name="api_clients"),
    url(r'^api/actions/$', rest_api.Actions.as_view(), name="api_actions"),
    url(r'^api/actions/job/(?P<job_id>[^/]+)?$',
        rest_api.ActionsInJob.as_view(), name="api_actions_in_job"),
)
