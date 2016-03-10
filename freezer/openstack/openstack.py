"""
(c) Copyright 2015,2016 Hewlett-Packard Development Company, L.P.

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
import os


class OpenstackOptions:
    """
    Stores credentials for OpenStack API.
    Can be created using
    >> create_from_env()
    or
    >> create_from_dict(dict)
    """
    def __init__(self, user_name, tenant_name, project_name, auth_url,
                 password, identity_api_version, tenant_id=None,
                 region_name=None, endpoint_type=None, cert=None,
                 insecure=False, verify=True):
        self.user_name = user_name
        self.tenant_name = tenant_name
        self.auth_url = auth_url
        self.password = password
        self.tenant_id = tenant_id
        self.project_name = project_name
        self.identity_api_version = identity_api_version
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.cert = cert
        self.insecure = insecure
        self.verify = verify
        if not (self.password and self.user_name and self.auth_url and
           (self.tenant_name or self.project_name)):
            raise Exception("Please set up in your env:"
                            "OS_USERNAME, OS_TENANT_NAME/OS_PROJECT_NAME,"
                            " OS_AUTH_URL, OS_PASSWORD")

    @property
    def os_options(self):
        """
        :return: The OpenStack options which can have tenant_id,
                 auth_token, service_type, endpoint_type, tenant_name,
                 object_storage_url, region_name
        """
        return {'tenant_id': self.tenant_id,
                'tenant_name': self.tenant_name,
                'project_name': self.project_name,
                'identity_api_version': self.identity_api_version,
                'region_name': self.region_name,
                'endpoint_type': self.endpoint_type}

    @staticmethod
    def create_from_env():
        return OpenstackOptions.create_from_dict(os.environ)

    @staticmethod
    def create_from_dict(src_dict):
        return OpenstackOptions(
            user_name=src_dict.get('OS_USERNAME', None),
            tenant_name=src_dict.get('OS_TENANT_NAME', None),
            project_name=src_dict.get('OS_PROJECT_NAME', None),
            auth_url=src_dict.get('OS_AUTH_URL', None),
            identity_api_version=src_dict.get('OS_IDENTITY_API_VERSION',
                                              '2.0'),
            password=src_dict.get('OS_PASSWORD', None),
            tenant_id=src_dict.get('OS_TENANT_ID', None),
            region_name=src_dict.get('OS_REGION_NAME', None),
            endpoint_type=src_dict.get('OS_ENDPOINT_TYPE', None),
            cert=src_dict.get('OS_CERT', None)
        )
