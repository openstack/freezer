# (c) Copyright 2019 ZTE Corporation..
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from concurrent import futures
import os

from oslo_config import cfg
from oslo_log import log
from oslo_serialization import jsonutils as json

from freezer.common import client_manager
from freezer.engine import engine
from freezer.engine.tar import tar
from freezer.utils import utils

import tempfile

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class GlanceEngine(engine.BackupEngine):

    def __init__(self, storage, **kwargs):
        super(GlanceEngine, self).__init__(storage=storage)
        self.client = client_manager.get_client_manager(CONF)
        self.glance = self.client.create_glance()
        self.encrypt_pass_file = kwargs.get('encrypt_key')
        self.exclude = kwargs.get('exclude')
        self.server_info = None
        self.openssl_path = None
        self.compression_algo = 'gzip'
        self.is_windows = None
        self.dry_run = kwargs.get('dry_run', False)
        self.max_segment_size = kwargs.get('max_segment_size')
        self.storage = storage
        self.dereference_symlink = kwargs.get('symlinks')

    @property
    def name(self):
        return "glance"

    def stream_image(self, pipe):
        """Reading bytes from a pipe and converting it to a stream-like"""
        try:
            while True:
                chunk = pipe.recv_bytes()
                yield chunk
        except EOFError:
            pass

    def get_glance_tenant(self, project_id):
        # Load info about tenant images
        if self.storage._type == 'swift':
            swift_connection = self.client.create_swift()
            headers, data = swift_connection.get_object(
                self.storage.storage_path,
                "project_glance_" + project_id)
        elif self.storage._type == 's3':
            bucket_name, object_name = self.get_storage_info(project_id)
            data = self.storage.get_object(
                bucket_name=bucket_name,
                key=object_name
            )['Body'].read()
        elif self.storage._type in ['local', 'ssh', 'ftp', 'ftps']:
            backup_basepath = os.path.join(self.storage.storage_path,
                                           'project_glance_' + project_id)
            with self.storage.open(backup_basepath, 'rb') as backup_file:
                data = backup_file.readline()
        elif self.storage._type in ['ftp', 'ftps']:
            backup_basepath = os.path.join(self.storage.storage_path,
                                           'project_glance_' + project_id)
            file = tempfile.NamedTemporaryFile('wb', delete=True)
            self.storage.get_file(backup_basepath, file.name)
            with open(file.name) as f:
                data = f.readline()
            LOG.info("get_glance_tenant download {0}".format(data))

        return json.loads(data)

    def restore_glance_tenant(self, project_id, hostname_backup_name,
                              overwrite, recent_to_date):

        image_ids = self.get_glance_tenant(project_id)
        for image_id in image_ids:
            LOG.info("Restore glance image ID: {0} from container {1}".
                     format(image_id, self.storage.storage_path))
            backup_name = os.path.join(hostname_backup_name,
                                       image_id)
            self.restore(
                hostname_backup_name=backup_name,
                restore_resource=image_id,
                overwrite=overwrite,
                recent_to_date=recent_to_date)

    def restore_level(self, restore_resource, read_pipe, backup, except_queue):
        try:
            metadata = backup.metadata()
            if (not self.encrypt_pass_file and
                    metadata.get("encryption", False)):
                raise Exception("Cannot restore encrypted backup without key")
            engine_metadata = backup.engine_metadata()
            image_info = metadata.get('image', {})
            container_format = image_info.get('container_format', 'bare')
            disk_format = image_info.get('disk_format', 'raw')

            length = int(engine_metadata.get('length'))

            stream = self.stream_image(read_pipe)
            data = utils.ReSizeStream(stream, length, 1)
            image = self.client.create_image(
                "Restore: {0}".format(
                    image_info.get('name', image_info.get('id', None))
                ),
                container_format,
                disk_format,
                data=data
            )

            if self.encrypt_pass_file:
                try:
                    tmpdir = tempfile.mkdtemp()
                except Exception:
                    LOG.error("Unable to create a tmp directory")
                    raise

                tar_engine = tar.TarEngine(self.compression_algo,
                                           self.dereference_symlink,
                                           self.exclude, self.storage,
                                           self.max_segment_size,
                                           self.encrypt_pass_file,
                                           self.dry_run)

                tar_engine.restore_level(tmpdir, read_pipe, backup,
                                         except_queue)

            utils.wait_for(
                GlanceEngine.image_active,
                1,
                CONF.timeout,
                message="Waiting for image to finish uploading {0} and become"
                        " active".format(image.id),
                kwargs={"glance_client": self.glance, "image_id": image.id}
            )
            return image
        except Exception as e:
            LOG.exception(e)
            except_queue.put(e)
            raise

    def backup_glance_tenant(self, project_id, hostname_backup_name,
                             no_incremental, max_level, always_level,
                             restart_always_level):
        # import pdb;pdb.set_trace()
        image_ids = [image.id for image in
                     self.glance.images.list(detailed=False)]
        data = json.dumps(image_ids)
        LOG.info("Saving information about image {0}".format(data))

        if self.storage._type == 'swift':
            swift_connection = self.client.create_swift()
            swift_connection.put_object(self.storage.storage_path,
                                        "project_glance_{0}".
                                        format(project_id),
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
                                           "project_glance_" + project_id)
            with self.storage.open(backup_basepath, 'wb') as backup_file:
                backup_file.write(data)
        elif self.storage._type in ['ftp', 'ftps']:
            backup_basepath = os.path.join(self.storage.storage_path,
                                           'project_glance_' + project_id)
            file = tempfile.NamedTemporaryFile('wb', delete=True)
            with open(file.name, 'wb') as f:
                f.write(data)
            LOG.info("backup_glance_tenant data={0}".format(data))
            self.storage.put_file(file.name, backup_basepath)

        executor = futures.ThreadPoolExecutor(
            max_workers=len(image_ids))
        futures_list = []
        for image_id in image_ids:
            LOG.info("Backup glance image ID: {0} to container {1}".
                     format(image_id, self.storage.storage_path))
            backup_name = os.path.join(hostname_backup_name,
                                       image_id)

            futures_list.append(executor.submit(
                self.backup,
                backup_resource=image_id,
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
        # import pdb;pdb.set_trace()
        image = self.glance.images.get(backup_resource)
        if not image:
            raise Exception(
                "Image {0} can't be found.".format(backup_resource)
            )
        LOG.info('Image backup')
        stream = self.client.download_image(image)

        LOG.info("Uploading image to storage path")

        headers = {"image_name": image.name,
                   "image_id": image.get('id'),
                   "disk_format": image.get('disk_format'),
                   "container_format": image.get('container_format'),
                   "visibility": image.get('visibility'),
                   'length': str(len(stream)),
                   "protected": image.protected}
        self.set_tenant_meta(manifest_path, headers)
        for chunk in stream:
            yield chunk

        if self.encrypt_pass_file:
            tar_engine = tar.TarEngine(self.compression_algo,
                                       self.dereference_symlink,
                                       self.exclude, self.storage,
                                       self.max_segment_size,
                                       self.encrypt_pass_file, self.dry_run)

            for data_chunk in tar_engine.backup_data('.', manifest_path):
                yield data_chunk

    @staticmethod
    def image_active(glance_client, image_id):
        """Check if the image is in the active state or not"""
        image = glance_client.images.get(image_id)
        return image.status == 'active'

    def metadata(self, backup_resource):
        """Construct metadata"""
        # import pdb;pdb.set_trace()
        image_info = self.glance.images.get(backup_resource)
        return {
            "engine_name": self.name,
            "image": image_info,
            "encryption": bool(self.encrypt_pass_file)
        }

    def set_tenant_meta(self, path, metadata):
        """push data to the manifest file"""
        with open(path, 'wb') as fb:
            fb.writelines(json.dumps(metadata))

    def get_tenant_meta(self, path):
        with open(path, 'rb') as fb:
            json.loads(fb.read())
