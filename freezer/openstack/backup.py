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
import time

from oslo_log import log

from freezer.utils import utils

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

    def backup_nova(self, instance_id):
        """
        Implement nova backup
        :param instance_id: Id of the instance for backup
        :return:
        """
        instance_id = instance_id
        client_manager = self.client_manager
        nova = client_manager.get_nova()
        instance = nova.servers.get(instance_id)
        glance = client_manager.get_glance()

        if instance.__dict__['OS-EXT-STS:task_state']:
            time.sleep(5)
            instance = nova.servers.get(instance)

        image_id = nova.servers.create_image(instance,
                                             "snapshot_of_%s" % instance_id)

        image = glance.images.get(image_id)
        while image.status != 'active':
            time.sleep(5)
            try:
                image = glance.images.get(image_id)
            except Exception as e:
                LOG.error(e)

        stream = client_manager.download_image(image)
        package = "{0}/{1}".format(instance_id, utils.DateTime.now().timestamp)
        LOG.info("Uploading image to swift")
        headers = {"x-object-meta-name": instance._info['name'],
                   "x-object-meta-flavor-id": instance._info['flavor']['id']}
        self.storage.add_stream(stream, package, headers)
        LOG.info("Deleting temporary image {0}".format(image))
        glance.images.delete(image.id)

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
        image = client_manager.make_glance_image("name", copied_volume)
        LOG.debug("Download temporary glance image {0}".format(image.id))
        stream = client_manager.download_image(image)
        package = "{0}/{1}".format(volume_id, utils.DateTime.now().timestamp)
        LOG.debug("Uploading image to swift")
        headers = {}
        self.storage.add_stream(stream, package, headers=headers)
        LOG.debug("Deleting temporary snapshot")
        client_manager.clean_snapshot(snapshot)
        LOG.debug("Deleting temporary volume")
        cinder.volumes.delete(copied_volume)
        LOG.debug("Deleting temporary image")
        client_manager.get_glance().images.delete(image.id)

    def backup_cinder(self, volume_id, name=None, description=None):
        client_manager = self.client_manager
        cinder = client_manager.get_cinder()
        search_opts = {
            'volume_id': volume_id,
            'status': 'available',
        }
        backups = cinder.backups.list(search_opts=search_opts)
        if len(backups) > 0:
            incremental = True
        else:
            incremental = False

        container = "{0}/{1}/{2}".format(self.container, volume_id,
                                         utils.DateTime.now().timestamp)

        cinder.backups.create(volume_id, container, name, description,
                              incremental=incremental, force=True)
