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

Freezer Backup modes related functions
"""

from oslo_config import cfg
from oslo_log import log

from freezer.utils import utils

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class BackupOs(object):

    def __init__(self, client_manager, container, storage):
        """

        :param client_manager:
        :param container:
        :param storage:
        :type storage: freezer.swift.SwiftStorage
        :return:
        """
        self.client_manager = client_manager
        self.container = container
        self.storage = storage

    def backup_cinder_by_glance(self, volume_id):
        """
        Implements cinder backup:
            1) Gets a stream of the image from glance
            2) Stores resulted image to the swift as multipart object

        :param volume_id: id of volume for backup
        """
        client_manager = self.client_manager
        cinder = client_manager.get_cinder()

        volume = cinder.volumes.get(volume_id)
        LOG.debug("Creation temporary snapshot")
        snapshot = client_manager.provide_snapshot(
            volume, "backup_snapshot_for_volume_%s" % volume_id)
        LOG.debug("Creation temporary volume")
        copied_volume = client_manager.do_copy_volume(snapshot)
        LOG.debug("Creation temporary glance image")
        image = client_manager.make_glance_image(copied_volume.id,
                                                 copied_volume)
        LOG.debug("Download temporary glance image {0}".format(image.id))
        stream = client_manager.download_image(image)
        package = "{0}/{1}".format(volume_id, utils.DateTime.now().timestamp)
        LOG.debug("Saving image to {0}".format(self.storage.type))
        if volume.name is None:
            name = volume_id
        else:
            name = volume.name
        headers = {'x-object-meta-length': str(len(stream)),
                   'volume_name': name,
                   'availability_zone': volume.availability_zone
                   }
        attachments = volume._info['attachments']
        if attachments:
            headers['server'] = attachments[0]['server_id']
        self.storage.add_stream(stream, package, headers=headers)
        LOG.debug("Deleting temporary snapshot")
        client_manager.clean_snapshot(snapshot)
        LOG.debug("Deleting temporary volume")
        cinder.volumes.delete(copied_volume)
        LOG.debug("Deleting temporary image")
        client_manager.get_glance().images.delete(image.id)

    def backup_cinder(self, volume_id, name=None, description=None,
                      incremental=False):
        client_manager = self.client_manager
        cinder = client_manager.get_cinder()
        container = "{0}/{1}/{2}".format(self.container, volume_id,
                                         utils.DateTime.now().timestamp)
        if incremental:
            search_opts = {
                'volume_id': volume_id,
                'status': 'available'
            }
            backups = cinder.backups.list(search_opts=search_opts)
            if len(backups) <= 0:
                msg = ("Backup volume %s is failed."
                       "Do a full backup before incremental  backup"
                       % volume_id)
                raise Exception(msg)
            else:
                cinder.backups.create(volume_id, container, name, description,
                                      incremental=incremental, force=True)
        else:
            cinder.backups.create(volume_id, container, name, description,
                                  incremental=incremental, force=True)
