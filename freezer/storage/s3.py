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

import botocore
import botocore.session
import logging
import requests

from oslo_log import log
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from freezer.storage import physical
from freezer.utils import utils

LOG = log.getLogger(__name__)
logging.getLogger('botocore').setLevel(logging.WARNING)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class S3Storage(physical.PhysicalStorage):

    _type = 's3'

    def __init__(self, access_key, secret_key, endpoint, container,
                 max_segment_size, skip_prepare=False):
        """
        :type container: str
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint
        super(S3Storage, self).__init__(
            storage_path=container,
            max_segment_size=max_segment_size,
            skip_prepare=skip_prepare)
        self.container = container
        storage_info = self.get_storage_info()
        self._bucket_name = storage_info[0]
        self._object_prefix = storage_info[1]

    def get_storage_info(self):
        storage_info = self.storage_path.split('/', 1)
        bucket_name = storage_info[0]
        object_prefix = storage_info[1] if '/' in self.storage_path else ''
        return bucket_name, object_prefix

    def rmtree(self, path):
        split = path.split('/', 1)
        all_s3_objects = self.list_all_objects(
            bucket_name=split[0],
            prefix=split[1]
        )
        for s3_object in all_s3_objects:
            self.get_s3_connection().delete_object(
                Bucket=split[0],
                Key=s3_object['Key']
            )

    def put_file(self, from_path, to_path):
        split = to_path.split('/', 1)
        self.get_s3_connection().put_object(
            Bucket=split[0],
            Key=split[1],
            Body=open(from_path, 'r')
        )

    def get_s3_connection(self):
        """
        :rtype: s3client.Connection
        :return:
        """
        return botocore.session.get_session().create_client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint
        )

    def prepare(self):
        """
        Check if the provided bucket is already available on S3
        compatible storage. The verification is done by exact matching
        between the provided bucket name and the whole list of bucket
        available for the S3 account.
        """
        bucket_list = \
            [c['Name'] for c in self.get_s3_connection()
                .list_buckets()['Buckets']]
        split = self.storage_path.split('/', 1)
        if split[0] not in bucket_list:
            self.get_s3_connection().create_bucket(Bucket=split[0])

    def info(self):
        # S3 standard interface do not have stats query function
        buckets = self.get_s3_connection().list_buckets()['Buckets']
        ordered_buckets = []
        for bucket in buckets:
            ordered_bucket = {
                'container_name': bucket['Name'],
                'size': '{0} MB'.format(0),
                'objects_count': 0
            }
            ordered_buckets.append(ordered_bucket)
        return ordered_buckets

    def get_file(self, from_path, to_path):
        split = from_path.split('/', 1)
        with open(to_path, 'ab') as obj_fd:
            s3_object = self.get_s3_connection().get_object(
                Bucket=split[0],
                Key=split[1])['Body']
            while True:
                object_trunk = s3_object.read(self.max_segment_size)
                if len(object_trunk) == 0:
                    break
                obj_fd.write(object_trunk)

    def add_stream(self, stream, package_name, headers=None):

        split = package_name.rsplit('/', 1)
        backup_basedir = package_name \
            if self.get_object_prefix() == '' \
            else "{0}/{1}".format(self.get_object_prefix(), package_name)

        backup_basepath = "{0}/{1}".format(backup_basedir, split[0])
        backup_meta_data = "{0}/metadata".format(backup_basedir)

        self.upload_stream(backup_basepath, stream)

        self.get_s3_connection().put_object(
            Bucket=self.get_bucket_name(),
            Body=json.dumps(headers),
            Key=backup_meta_data
        )

    def upload_stream(self, backup_basepath, stream):
        upload_id = self.get_s3_connection().create_multipart_upload(
            Bucket=self.get_bucket_name(),
            Key=backup_basepath
        )['UploadId']
        upload_part_index = 1
        uploaded_parts = []
        try:
            for el in stream:
                response = self.get_s3_connection().upload_part(
                    Body=el,
                    Bucket=self.get_bucket_name(),
                    Key=backup_basepath,
                    PartNumber=upload_part_index,
                    UploadId=upload_id
                )
                uploaded_parts.append({
                    'PartNumber': upload_part_index,
                    'ETag': response['ETag']
                })
                upload_part_index += 1
            # Complete the upload, which requires info on all of the parts
            part_info = {
                'Parts': uploaded_parts
            }

            if not uploaded_parts:
                # currently, not support volume boot instance
                LOG.error(
                    "No part uploaded(not support volume boot instance)"
                )
                raise RuntimeError(
                    'No part uploaded(not support volume boot instance)'
                )

            self.get_s3_connection().complete_multipart_upload(
                Bucket=self.get_bucket_name(),
                Key=backup_basepath,
                MultipartUpload=part_info,
                UploadId=upload_id
            )
        except Exception as e:
            LOG.error("Upload stream to S3 error, so abort it. "
                      "Exception: {0}".format(e))
            self.get_s3_connection().abort_multipart_upload(
                Bucket=self.get_bucket_name(),
                Key=backup_basepath,
                UploadId=upload_id
            )

    def backup_blocks(self, backup):
        """
        :param backup:
        :type backup: freezer.storage.base.Backup
        :return:
        """
        split = backup.data_path.split('/', 1)
        s3_object = self.get_s3_connection().get_object(
            Bucket=split[0],
            Key=split[1]
        )

        return utils.S3ResponseStream(
            data=s3_object['Body'],
            chunk_size=self.max_segment_size
        )

    def write_backup(self, rich_queue, backup):
        """
        Upload object to the remote S3 compatible storage server
        :type rich_queue: freezer.streaming.RichQueue
        :type backup: freezer.storage.base.Backup
        """
        backup = backup.copy(storage=self)
        path = backup.data_path.split('/', 1)[1]
        self.upload_stream(path, rich_queue.get_messages())

    def listdir(self, path):
        """
        :type path: str
        :param path:
        :rtype: collections.Iterable[str]
        """
        try:
            files = set()
            split = path.split('/', 1)
            all_s3_objects = self.list_all_objects(
                bucket_name=split[0],
                prefix=split[1]
            )
            for s3_object in all_s3_objects:
                files.add(s3_object['Key'][len(split[1]):].split('/', 2)[1])
            return files
        except Exception as e:
            LOG.error(e)
            return []

    def create_dirs(self, folder_list):
        pass

    def get_bucket_name(self):
        return self._bucket_name

    def get_object_prefix(self):
        return self._object_prefix

    def get_object(self, bucket_name, key):
        return self.get_s3_connection().get_object(
            Bucket=bucket_name,
            Key=key
        )

    def list_all_objects(self, bucket_name, prefix):
        all_objects = []
        is_truncated = True
        marker = ''
        while is_truncated:
            response = self.get_s3_connection().list_objects(
                Bucket=bucket_name,
                Marker=marker,
                Prefix=prefix
            )

            if 'Contents' not in response:
                break

            all_objects.extend(response['Contents'])
            is_truncated = response['IsTruncated']
            marker = response['Contents'][-1]['Key']
        return all_objects

    def put_object(self, bucket_name, key, data):
        self.get_s3_connection().put_object(
            Bucket=bucket_name,
            Key=key,
            Body=data
        )
