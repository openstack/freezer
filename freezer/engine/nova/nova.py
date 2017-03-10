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

from oslo_config import cfg
from oslo_log import log

from freezer.common import client_manager
from freezer.engine import engine
from freezer.utils import utils

import json

LOG = log.getLogger(__name__)
CONF = cfg.CONF

_NOVABBKK_TIMEOUT = 100


class NovaEngine(engine.BackupEngine):

    def __init__(self, storage, **kwargs):
        super(NovaEngine, self).__init__(storage=storage)
        self.client = client_manager.get_client_manager(CONF)
        self.nova = self.client.create_nova()
        self.glance = self.client.create_glance()
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

    def restore_level(self, restore_resource, read_pipe, backup, except_queue):
        try:
            metadata = backup.metadata()
            server_info = metadata.get('server', {})
            length = int(server_info.get('length'))
            available_networks = server_info.get('addresses')
            nova_networks = self.nova.networks.findall()

            net_names = [network for network, _ in
                         available_networks.iteritems()]
            match_networks = [{"net-id": network.id} for network in
                              nova_networks
                              if network.to_dict().get('label') in net_names]

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
                _NOVABBKK_TIMEOUT,
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

    def backup_data(self, backup_resource, manifest_path):
        server = self.nova.servers.get(backup_resource)
        if not server:
            raise Exception("Server not found {0}".format(backup_resource))

        def instance_finish_task():
            server = self.nova.servers.get(backup_resource)
            return not server.__dict__['OS-EXT-STS:task_state']

        utils.wait_for(
            instance_finish_task, 1, _NOVABBKK_TIMEOUT,
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
        # to glance. @todo szaher add a timeout option.
        utils.wait_for(
            NovaEngine.image_active,
            1,
            100,
            message="Waiting for instnace {0} snapshot to become "
                    "active".format(backup_resource),
            kwargs={"glance_client": self.glance, "image_id": image_id}
        )

        image = self.glance.images.get(image_id)
        stream = self.client.download_image(image)
        LOG.info("Uploading image to swift")
        headers = {"server_name": server.name,
                   "flavour_id": str(server.flavor.get('id')),
                   'length': str(len(stream))}
        self.set_tenant_meta(manifest_path, headers)
        for chunk in stream:
            yield chunk

        LOG.info("Deleting temporary image {0}".format(image.id))
        self.glance.images.delete(image.id)
        self.server_info = server.to_dict()
        self.server_info['length'] = len(stream)

    @staticmethod
    def image_active(glance_client, image_id):
        """Check if the image is in the active state or not"""
        image = glance_client.images.get(image_id)
        return image.status == 'active'

    def metadata(self):
        """Construct metadata"""
        return {
            "engine_name": self.name,
            "server": self.server_info
        }

    def set_tenant_meta(self, path, metadata):
        """push data to the manifest file"""
        with open(path, 'wb') as fb:
            fb.writelines(json.dumps(metadata))
