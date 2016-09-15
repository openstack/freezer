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

import time

from oslo_log import log

from freezer.utils import utils

LOG = log.getLogger(__name__)


class RestoreOs(object):
    def __init__(self, client_manager, container):
        self.client_manager = client_manager
        self.container = container

    def _get_backups(self, path, restore_from_timestamp):
        """
        :param path:
        :type path: str
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :return:
        """
        swift = self.client_manager.get_swift()
        path = "{0}_segments/{1}/".format(self.container, path)
        info, backups = swift.get_container(self.container, prefix=path)
        backups = sorted(
            map(lambda x: int(x["name"].rsplit("/", 1)[-1]), backups))
        backups = list(filter(lambda x: x >= restore_from_timestamp, backups))
        if not backups:
            msg = "Cannot find backups for path: %s" % path
            LOG.error(msg)
            raise BaseException(msg)
        return backups[-1]

    def _create_image(self, path, restore_from_timestamp):
        """
        :param path:
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :return:
        """
        swift = self.client_manager.get_swift()
        glance = self.client_manager.get_glance()
        backup = self._get_backups(path, restore_from_timestamp)
        path = "{0}_segments/{1}/{2}".format(self.container, path, backup)

        stream = swift.get_object(self.container, "%s/%s" % (path, backup),
                                  resp_chunk_size=10000000)
        length = int(stream[0]["x-object-meta-length"])
        LOG.info("Creation glance image")
        image = glance.images.create(
            container_format="bare", disk_format="raw")
        glance.images.upload(image.id,
                             utils.ReSizeStream(stream[1], length, 1))
        return stream[0], image

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
        backup = None
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
        self.client_manager.get_cinder().volumes.create(size,
                                                        imageRef=image.id)
        LOG.info("Deleting temporary image")
        self.client_manager.get_glance().images.delete(image)

    def restore_nova(self, instance_id, restore_from_timestamp,
                     nova_network=None):
        """
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :param instance_id: id of attached nova instance
        :param nova_network: id of network
        :return:
        """
        nova = self.client_manager.get_nova()
        network_list = nova.networks.findall()
        if len(network_list) > 1 and (nova_network is None):
            raise Exception("The parameter --nova-restore-network is required")
        get_nova_network = nova.networks.get(nova_network)
        if nova_network and (get_nova_network not in network_list):
            raise Exception("The network %s is invalid" % nova_network)
        (info, image) = self._create_image(instance_id, restore_from_timestamp)
        flavor = nova.flavors.get(info['x-object-meta-flavor-id'])
        LOG.info("Creating an instance")
        instance = None
        if nova_network is None:
            instance = nova.servers.create(info['x-object-meta-name'], image,
                                           flavor)
        else:
            instance = nova.servers.create(info['x-object-meta-name'], image,
                                           flavor,
                                           nics=[{'net-id': nova_network}])
        # loop and wait till the server is up then remove the image
        # let's wait 100 second
        LOG.info('Delete instance image from glance {0}'.format(image))
        for i in range(0, 360):
            time.sleep(10)
            instance = nova.servers.get(instance)
            if not instance.__dict__['OS-EXT-STS:task_state']:
                glance = self.client_manager.create_glance()
                glance.images.delete(image.id)
                return
