"""
(c) Copyright 2017 Mirantis, Inc

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
import shutil
import socket
import subprocess
import tempfile

from oslo_config import cfg
from oslo_log import log

from freezer.common import client_manager
from freezer.engine import engine
from freezer.engine.osbrick import client as brick_client
from freezer.engine.tar import tar
from freezer.utils import utils
from freezer.utils import winutils

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class OsbrickEngine(engine.BackupEngine):
    def __init__(self, storage, **kwargs):
        super(OsbrickEngine, self).__init__(storage=storage)
        self.client = client_manager.get_client_manager(CONF)
        self.cinder = self.client.create_cinder()
        self.volume_info = None

        self.compression_algo = kwargs.get('compression')
        self.encrypt_pass_file = kwargs.get('encrypt_key')
        self.dereference_symlink = kwargs.get('symlinks')
        self.exclude = kwargs.get('exclude')
        self.storage = storage
        self.is_windows = winutils.is_windows()
        self.dry_run = kwargs.get('dry_run', False)
        self.max_segment_size = kwargs.get('max_segment_size')

    @property
    def name(self):
        return "osbrick"

    def metadata(self, backup_resource):
        """Construct metadata"""
        return {
            "engine_name": self.name,
            "volume_info": self.volume_info
        }

    @staticmethod
    def is_active(client_manager, id):
        get_res = client_manager.get(id)
        return get_res.status == 'available'

    def backup_data(self, backup_path, manifest_path):
        LOG.info("Starting os-brick engine backup stream")
        volume = self.cinder.volumes.get(backup_path)
        self.volume_info = volume.to_dict()

        snapshot = self.cinder.volume_snapshots.create(backup_path, force=True)
        LOG.info("[*] Creating volume snapshot")
        utils.wait_for(
            OsbrickEngine.is_active,
            1,
            100,
            message="Waiting for volume {0} snapshot to become "
                    "active".format(backup_path),
            kwargs={"client_manager": self.cinder.volume_snapshots,
                        "id": snapshot.id}
        )

        LOG.info("[*] Converting snapshot to volume")
        backup_volume = self.cinder.volumes.create(snapshot.size,
                                                   snapshot_id=snapshot.id)

        utils.wait_for(
            OsbrickEngine.is_active,
            1,
            100,
            message="Waiting for backup volume {0} to become "
                    "active".format(backup_volume.id),
            kwargs={"client_manager": self.cinder.volumes,
                        "id": backup_volume.id}
        )

        try:
            tmpdir = tempfile.mkdtemp()
        except Exception:
            LOG.error("Unable to create a tmp directory")
            raise

        LOG.info("[*] Trying to attach the volume to localhost")
        brickclient = brick_client.Client(volumes_client=self.cinder)

        attach_info = brickclient.attach(backup_volume.id,
                                         socket.gethostname(),
                                         tmpdir)

        if not os.path.ismount(tmpdir):
            subprocess.check_output(['sudo', 'mount', '-t', 'ext4',
                                     attach_info.get('path'), tmpdir])

        cwd = os.getcwd()
        os.chdir(tmpdir)

        tar_engine = tar.TarEngine(self.compression_algo,
                                   self.dereference_symlink,
                                   self.exclude, self.storage,
                                   self.max_segment_size,
                                   self.encrypt_pass_file, self.dry_run)

        for data_chunk in tar_engine.backup_data('.', manifest_path):
            yield data_chunk

        os.chdir(cwd)

        LOG.info("[*] Detaching volume")
        subprocess.check_output(['sudo', 'umount', tmpdir])
        shutil.rmtree(tmpdir)
        brickclient.detach(backup_volume.id)

        utils.wait_for(
            OsbrickEngine.is_active,
            1,
            100,
            message="Waiting for backup volume {0} to become "
                    "active".format(backup_volume.id),
            kwargs={"client_manager": self.cinder.volumes,
                        "id": backup_volume.id}
        )

        LOG.info("[*] Removing backup volume and snapshot")
        self.cinder.volumes.delete(backup_volume.id)
        self.cinder.volume_snapshots.delete(snapshot, force=True)

        LOG.info('Backup process completed')

    def restore_level(self, restore_path, read_pipe, backup, except_queue):
        try:
            LOG.info("Restoring volume {} using os-brick engine".format(
                restore_path))
            new_volume = False
            metadata = backup.metadata()
            volume_info = metadata.get("volume_info")
            try:
                backup_volume = self.cinder.volumes.get(restore_path)
            except Exception:
                new_volume = True
                LOG.info("[*] Volume doesn't exists, creating a new one")
                backup_volume = self.cinder.volumes.create(volume_info['size'])

                utils.wait_for(
                    OsbrickEngine.is_active,
                    1,
                    100,
                    message="Waiting for backup volume {0} to become "
                            "active".format(backup_volume.id),
                    kwargs={"client_manager": self.cinder.volumes,
                                "id": backup_volume.id}
                )

            if backup_volume.attachments:
                LOG.info('Volume is used, creating a copy from snapshot')
                snapshot = self.cinder.volume_snapshots.create(
                    backup_volume.id, force=True)
                utils.wait_for(
                    OsbrickEngine.is_active,
                    1,
                    100,
                    message="Waiting for volume {0} snapshot to become "
                            "active".format(backup_volume.id),
                    kwargs={"client_manager": self.cinder.volume_snapshots,
                                "id": snapshot.id}
                )

                LOG.info("[*] Converting snapshot to volume")
                backup_volume = self.cinder.volumes.create(
                    snapshot.size, snapshot_id=snapshot.id)

                utils.wait_for(
                    OsbrickEngine.is_active,
                    1,
                    100,
                    message="Waiting for backup volume {0} to become "
                            "active".format(backup_volume.id),
                    kwargs={"client_manager": self.cinder.volumes,
                                "id": backup_volume.id}
                )

            backup_volume = self.cinder.volumes.get(backup_volume.id)
            if backup_volume.status != 'available':
                raise RuntimeError('Unable to use volume for restore data')

            try:
                tmpdir = tempfile.mkdtemp()
            except Exception:
                LOG.error("Unable to create a tmp directory")
                raise

            LOG.info("[*] Trying to attach the volume to localhost")
            brickclient = brick_client.Client(volumes_client=self.cinder)
            attach_info = brickclient.attach(backup_volume.id,
                                             socket.gethostname(),
                                             tmpdir)

            if not os.path.ismount(tmpdir):
                if new_volume:
                    subprocess.check_output(['sudo', 'mkfs.ext4',
                                             attach_info.get('path')])

                subprocess.check_output(['sudo', 'mount', '-t', 'ext4',
                                         attach_info.get('path'),
                                         tmpdir])

            tar_engine = tar.TarEngine(self.compression_algo,
                                       self.dereference_symlink,
                                       self.exclude, self.storage,
                                       self.max_segment_size,
                                       self.encrypt_pass_file, self.dry_run)

            tar_engine.restore_level(tmpdir, read_pipe, backup,
                                     except_queue)

            subprocess.check_output(['sudo', 'umount', tmpdir])
            shutil.rmtree(tmpdir)

            LOG.info("[*] Detaching volume")
            brickclient.detach(backup_volume.id)

            utils.wait_for(
                OsbrickEngine.is_active,
                1,
                100,
                message="Waiting for backup volume {0} to become "
                        "active".format(backup_volume.id),
                kwargs={"client_manager": self.cinder.volumes,
                            "id": backup_volume.id}
            )

            LOG.info('Restore process completed')

        except Exception as e:
            LOG.exception(e)
            except_queue.put(e)
            raise
