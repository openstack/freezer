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

Freezer restore modes related functions
"""

import json
import os
import time

from oslo_config import cfg
from oslo_log import log

from freezer.utils import utils

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class RestoreOs(object):
    def __init__(self, client_manager, container, storage):
        self.client_manager = client_manager
        self.container = container
        self.storage = storage

    def _get_backups(self, path, restore_from_timestamp):
        """
        :param path:
        :type path: str
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :return:
        """
        if self.storage.type == "swift":
            swift = self.client_manager.get_swift()
            path = "{0}_segments/{1}/".format(self.container, path)
            container_name, path = self.get_storage_info(path)
            info, backups = swift.get_container(container_name, prefix=path)
            backups = sorted(
                map(lambda x: int(x["name"].rsplit("/", 1)[-1]), backups))
        elif self.storage.type == "s3":
            bucket_name, path = self.get_storage_info(path)
            backups = self.storage.list_all_objects(
                bucket_name=bucket_name,
                prefix=path
            )
            backups = sorted(
                map(lambda x: int(x['Key'].split("/", 2)[1]), backups))
        elif self.storage.type == "local":
            path = "{0}/{1}".format(self.container, path)
            backups = os.listdir(os.path.abspath(path))
        elif self.storage.type == "ssh":
            path = "{0}/{1}".format(self.container, path)
            backups = self.storage.listdir(path)
        else:
            msg = ("{} storage type is not supported at the moment."
                   " Try local, swift or ssh".format(self.storage.type))
            print(msg)
            raise BaseException(msg)
        backups = list(filter(lambda x: x >= restore_from_timestamp, backups))
        if not backups:
            msg = "Cannot find backups for path: %s" % path
            LOG.error(msg)
            raise BaseException(msg)
        return backups[-1]

    def get_storage_info(self, path):
        storage_info = self.container.split('/', 1)
        container_name = storage_info[0]
        object_prefix = storage_info[1] if '/' in self.container else ''
        if object_prefix != '':
            path = "{0}/{1}".format(object_prefix, path)
        return container_name, path

    def _create_image(self, path, restore_from_timestamp):
        """
        :param path:
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :return:
        """
        backup = self._get_backups(path, restore_from_timestamp)
        if self.storage.type == 'swift':
            swift = self.client_manager.get_swift()
            path = "{0}_segments/{1}/{2}".format(self.container, path, backup)
            stream = swift.get_object(self.container,
                                      "{}/{}".format(path, backup),
                                      resp_chunk_size=10000000)
            length = int(stream[0]["x-object-meta-length"])
            data = utils.ReSizeStream(stream[1], length, 1)
            info = stream[0]
            image = self.client_manager.create_image(
                name="restore_{}".format(path),
                container_format="bare",
                disk_format="raw",
                data=data)
            return info, image
        elif self.storage.type == 's3':
            if self.storage.get_object_prefix() != '':
                base_path = "{0}/{1}/{2}".format(
                    self.storage.get_object_prefix(),
                    path,
                    backup
                )
            else:
                base_path = "{0}/{1}".format(path, backup)
            image_file = "{0}/{1}".format(base_path, path)
            s3_object = self.storage.get_object(
                bucket_name=self.storage.get_bucket_name(),
                key=image_file
            )
            stream = utils.S3ResponseStream(data=s3_object['Body'],
                                            chunk_size=10000000)
            data = utils.ReSizeStream(
                stream,
                s3_object['ContentLength'],
                1
            )
            metadata = "{0}/metadata".format(base_path)
            metadata_object = self.storage.get_object(
                bucket_name=self.storage.get_bucket_name(),
                key=metadata
            )
            info = json.load(metadata_object['Body'])

            image = self.client_manager.create_image(
                name="restore_{}".format(path),
                container_format="bare",
                disk_format="raw",
                data=data)
            return info, image
        elif self.storage.type == 'local':
            image_file = "{0}/{1}/{2}/{3}".format(self.container, path,
                                                  backup, path)
            metadata_file = "{0}/{1}/{2}/metadata".format(self.container,
                                                          path, backup)
            try:
                data = open(image_file, 'rb')
            except Exception:
                msg = "Failed to open image file {}".format(image_file)
                LOG.error(msg)
                raise BaseException(msg)
            info = json.load(file(metadata_file))
            image = self.client_manager.create_image(
                name="restore_{}".format(path),
                container_format="bare",
                disk_format="raw",
                data=data)
            return info, image
        elif self.storage.type == 'ssh':
            image_file = "{0}/{1}/{2}/{3}".format(self.container, path,
                                                  backup, path)
            metadata_file = "{0}/{1}/{2}/metadata".format(self.container,
                                                          path, backup)
            try:
                data = self.storage.open(image_file, 'rb')
            except Exception:
                msg = "Failed to open remote image file {}".format(image_file)
                LOG.error(msg)
                raise BaseException(msg)
            info = json.loads(self.storage.read_metadata_file(metadata_file))
            image = self.client_manager.create_image(
                name="restore_{}".format(path),
                container_format="bare",
                disk_format="raw",
                data=data)
            return info, image
        else:
            return {}

    def restore_cinder(self, volume_id=None,
                       backup_id=None,
                       restore_from_timestamp=None):
        """
        Restoring cinder backup using
        :param volume_id:
        :param backup_id:
        :param restore_from_timestamp:
        :return:
        """
        cinder = self.client_manager.get_cinder()
        search_opts = {
            'volume_id': volume_id,
            'status': 'available',
        }
        if not backup_id:
            backups = cinder.backups.list(search_opts=search_opts)

            def get_backups_from_timestamp(backups, restore_from_timestamp):
                for backup in backups:
                    backup_created_date = backup.created_at.split('.')[0]
                    backup_created_timestamp = (
                        utils.date_to_timestamp(backup_created_date))
                    if backup_created_timestamp >= restore_from_timestamp:
                        yield backup

            backups_filter = get_backups_from_timestamp(backups,
                                                        restore_from_timestamp)
            if not backups_filter:
                LOG.warning("no available backups for cinder volume,"
                            "restore newest backup")
                backup = max(backups, key=lambda x: x.created_at)
            else:
                backup = min(backups_filter, key=lambda x: x.created_at)
            backup_id = backup.id
        cinder.restores.restore(backup_id=backup_id)

    def restore_cinder_by_glance(self, volume_id, restore_from_timestamp):
        """
        1) Define swift directory
        2) Download and upload to glance
        3) Create volume from glance
        4) Delete
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :param volume_id - id of attached cinder volume
        """
        (info, image) = self._create_image(volume_id, restore_from_timestamp)
        length = int(info["x-object-meta-length"])
        gb = 1073741824
        size = length / gb
        if length % gb > 0:
            size += 1
        LOG.info("Creating volume from image")
        cinder_client = self.client_manager.get_cinder()
        volume = cinder_client.volumes.create(
            size,
            imageRef=image.id,
            name=info.get('volume_name',
                          CONF.get('backup_name',
                                   CONF.get('cinder_vol_id', None)
                                   )
                          )
        )
        while volume.status != "available":
            try:
                LOG.info("Volume copy status: " + volume.status)
                volume = cinder_client.volumes.get(volume.id)
                if volume.status == "error":
                    raise Exception("Volume copy status: error")
                time.sleep(5)
            except Exception as e:
                LOG.exception(e)
                if volume.status != "error":
                    LOG.warn("Exception getting volume status")

        LOG.info("Deleting temporary image {}".format(image.id))
        self.client_manager.get_glance().images.delete(image.id)
