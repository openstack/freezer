"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

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
from oslo_log import log

LOG = log.getLogger(__name__)


class ApiClientException(Exception):
    @staticmethod
    def get_message_from_api_response(r):
        """
        returns a message based on information from a api-formatted response
        if available, otherwise None
        api-formatted response should be:
            {
                title: "error title string",
                description: "error description string"
            }

        :param r: response object
        :return: string with error message or None if it fails
        """
        try:
            body = json.loads(r.text)
            message = "Error {0}: {1}".format(
                r.status_code,
                body['description'])
        except Exception:
            message = None
        return message

    @staticmethod
    def get_message_from_response(r):
        """
        composes the error message using information eventually present
        in the response (http error code and the http response body)

        :param r: response object
        :return: string with error message or None if it fails
        """
        try:
            message = "Error {0}: {1}".format(
                r.status_code,
                r.text)
        except Exception:
            message = None
        return message

    def __init__(self, r):
        message = self.get_message_from_api_response(r) or \
            self.get_message_from_response(r) or \
            str(r)
        try:
            self.status_code = r.status_code
        except Exception:
            self.status_code = None
        super(ApiClientException, self).__init__(message)
