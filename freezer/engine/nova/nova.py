"""
(c) Copyright 2016 Hewlett-Packard Development Enterprise, L.P.

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
from concurrent import futures
import os

from oslo_config import cfg
from oslo_log import log

from freezer.common import client_manager
from freezer.engine import engine
from freezer.utils import utils

import json

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class NovaEngine(engine.BackupEngine):

    def __init__(self, storage, **kwargs):
        super(NovaEngine, self).__init__(storage=storage)
        self.client = client_manager.get_client_manager(CONF)
        self.nova = self.client.create_nova()
        self.glance = self.client.create_glance()
        self.cinder = self.client.create_cinder()
        self.neutron = self.client.create_neutron()
        self.server_info = None

    @property
    def name(self):
        return "nova"

    def stream_image(self, pipe):
        """Reading bytes from a pipe and converting it to a stream-like"""
        try:
            while True:
                chunk = pipe.recv_bytes()
                yield chunk
        except EOFError:
            pass

    def get_nova_tenant(self, project_id):
        # Load info about tenant instances
        if self.storage._type == 'swift':
            swift_connection = self.client.create_swift()
            headers, data = swift_connection.get_object(
                self.storage.storage_path,
                "project_" + project_id)
        elif self.storage._type == 's3':
            bucket_name, object_name = self.get_storage_info(project_id)
            data = self.storage.get_object(
                bucket_name=bucket_name,
                key=object_name
            )['Body'].read()
        elif self.storage._type in ['local', 'ssh']:
            backup_basepath = os.path.join(self.storage.storage_path,
                                           'project_' + project_id)
            with self.storage.open(backup_basepath, 'rb') as backup_file:
                data = backup_file.readline()

        return json.loads(data)

    def restore_nova_tenant(self, project_id, hostname_backup_name,
                            overwrite, recent_to_date):

        instance_ids = self.get_nova_tenant(project_id)
        for instance_id in instance_ids:
            LOG.info("Restore nova instance ID: {0} from container {1}".
                     format(instance_id, self.storage.storage_path))
            backup_name = os.path.join(hostname_backup_name,
                                       instance_id)
            self.restore(
                hostname_backup_name=backup_name,
                restore_resource=instance_id,
                overwrite=overwrite,
                recent_to_date=recent_to_date)

    def restore_level(self, restore_resource, read_pipe, backup, except_queue):
        try:
            metadata = backup.metadata()
            engine_metadata = backup.engine_metadata()
            server_info = metadata.get('server', {})
            length = int(engine_metadata.get('length'))
            available_networks = server_info.get('addresses')
            nova_networks = self.neutron.list_networks()['networks']

            net_names = [network for network, _ in
                         available_networks.iteritems()]
            match_networks = [{"net-id": network.get('id')} for network in
                              nova_networks
                              if network.get('name') in net_names]

            stream = self.stream_image(read_pipe)
            data = utils.ReSizeStream(stream, length, 1)
            image = self.client.create_image(
                "Restore: {0}".format(
                    server_info.get('name', server_info.get('id', None))
                ),
                'bare',
                'raw',
                data=data
            )

            utils.wait_for(
                NovaEngine.image_active,
                1,
                CONF.timeout,
                message="Waiting for image to finish uploading {0} and become"
                        " active".format(image.id),
                kwargs={"glance_client": self.glance, "image_id": image.id}
            )
            server = self.nova.servers.create(
                name=server_info.get('name'),
                flavor=server_info['flavor']['id'],
                image=image.id,
                nics=match_networks
            )
            return server
        except Exception as e:
            LOG.exception(e)
            except_queue.put(e)
            raise

    def backup_nova_tenant(self, project_id, hostname_backup_name,
                           no_incremental, max_level, always_level,
                           restart_always_level):
        instance_ids = [server.id for server in
                        self.nova.servers.list(detailed=False)]
        data = json.dumps(instance_ids)
        LOG.info("Saving information about instances {0}".format(data))

        if self.storage._type == 'swift':
            swift_connection = self.client.create_swift()
            swift_connection.put_object(self.storage.storage_path,
                                        "project_{0}".format(project_id),
                                        data)
        elif self.storage._type == 's3':
            bucket_name, object_name = self.get_storage_info(project_id)
            self.storage.put_object(
                bucket_name=bucket_name,
                key=object_name,
                data=data
            )
        elif self.storage._type in ['local', 'ssh']:
            backup_basepath = os.path.join(self.storage.storage_path,
                                           "project_" + project_id)
            with self.storage.open(backup_basepath, 'wb') as backup_file:
                backup_file.write(data)

        executor = futures.ThreadPoolExecutor(
            max_workers=len(instance_ids))
        futures_list = []
        for instance_id in instance_ids:
            LOG.info("Backup nova instance ID: {0} to container {1}".
                     format(instance_id, self.storage.storage_path))
            backup_name = os.path.join(hostname_backup_name,
                                       instance_id)

            futures_list.append(executor.submit(
                self.backup,
                backup_resource=instance_id,
                hostname_backup_name=backup_name,
                no_incremental=no_incremental,
                max_level=max_level,
                always_level=always_level,
                restart_always_level=restart_always_level))

        futures.wait(futures_list, CONF.timeout)

    def get_storage_info(self, project_id):
        if self.storage.get_object_prefix() != '':
            object_name = "{0}/project_{1}".format(
                self.storage.get_object_prefix(),
                project_id
            )
        else:
            object_name = "project_{0}".format(project_id)
        return self.storage.get_bucket_name(), object_name

    def backup_data(self, backup_resource, manifest_path):
        server = self.nova.servers.get(backup_resource)
        if not server:
            raise Exception("Server not found {0}".format(backup_resource))

        def instance_finish_task():
            server = self.nova.servers.get(backup_resource)
            return not server.__dict__['OS-EXT-STS:task_state']

        utils.wait_for(
            instance_finish_task, 1, CONF.timeout,
            message="Waiting for instance {0} to finish {1} to start the "
                    "snapshot process".format(
                        backup_resource,
                        server.__dict__['OS-EXT-STS:task_state']
                    )
        )
        image_id = self.nova.servers.create_image(
            server,
            "snapshot_of_{0}".format(backup_resource)
        )
        image = self.glance.images.get(image_id)
        if not image:
            raise Exception(
                "Image {0} is not created or can't be found.".format(image_id)
            )
        # wait a bit for the snapshot to be taken and completely uploaded
        # to glance.
        utils.wait_for(
            NovaEngine.image_active,
            1,
            100,
            message="Waiting for instnace {0} snapshot to become "
                    "active".format(backup_resource),
            kwargs={"glance_client": self.glance, "image_id": image_id}
        )

        image = self.glance.images.get(image_id)
        image_temporary_snapshot_id = None
        copied_volume = None
        image_info = getattr(server, "image", None)
        if image_info is not None and isinstance(image_info, dict):
            LOG.info('Image type instance backup')
            boot_device_type = "image"
            stream = self.client.download_image(image)
        else:
            LOG.info('Volume or snapshot type instance backup')
            boot_device_type = "volume"
            image_block_mapping_info = image.get("block_device_mapping")
            image_block_mapping = json.loads(image_block_mapping_info) \
                if image_block_mapping_info else None
            image_temporary_snapshot_id = \
                image_block_mapping[0]['snapshot_id'] \
                if image_block_mapping else None
            copied_volume = self.client.do_copy_volume(
                self.cinder.volume_snapshots.get(
                    image_temporary_snapshot_id))
            LOG.debug("Deleting temporary glance image "
                      "generated by snapshot")
            self.glance.images.delete(image.id)
            LOG.debug("Creation temporary glance image")
            image = self.client.make_glance_image(
                copied_volume.id, copied_volume)
            LOG.debug("Download temporary glance image {0}".format(image.id))
            stream = self.client.download_image(image)

        LOG.info("Uploading image to storage path")
        headers = {"server_name": server.name,
                   "flavour_id": str(server.flavor.get('id')),
                   'length': str(len(stream)),
                   "boot_device_type": boot_device_type}
        self.set_tenant_meta(manifest_path, headers)
        for chunk in stream:
            yield chunk

        if image_temporary_snapshot_id is not None:
            LOG.info("Deleting temporary snapshot {0}"
                     .format(image_temporary_snapshot_id))
            self.cinder.volume_snapshots.delete(image_temporary_snapshot_id)
        if copied_volume is not None:
            LOG.info("Deleting temporary copied volume {0}"
                     .format(copied_volume.id))
            self.cinder.volumes.delete(copied_volume)

        LOG.info("Deleting temporary image {0}".format(image.id))
        self.glance.images.delete(image.id)

    @staticmethod
    def image_active(glance_client, image_id):
        """Check if the image is in the active state or not"""
        image = glance_client.images.get(image_id)
        return image.status == 'active'

    def metadata(self, backup_resource):
        """Construct metadata"""
        server_info = self.nova.servers.get(backup_resource).to_dict()

        return {
            "engine_name": self.name,
            "server": server_info,
        }

    def set_tenant_meta(self, path, metadata):
        """push data to the manifest file"""
        with open(path, 'wb') as fb:
            fb.writelines(json.dumps(metadata))

    def get_tenant_meta(self, path):
        with open(path, 'rb') as fb:
            json.loads(fb.read())
