# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from os_brick import exception
from os_brick.initiator import connector


class VolumeAction(object):
    def __init__(self, volumes_client, volume_id):
        self.volumes_client = volumes_client
        self.volume_id = volume_id

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if traceback:
            self.volumes_client.volumes.unreserve(self.volume_id)
            return False
        return True


class Reserve(VolumeAction):
    def reserve(self):
        self.volumes_client.volumes.reserve(self.volume_id)


class InitializeConnection(VolumeAction):
    def initialize(self, brick_client, multipath, enforce_multipath):
        conn_prop = brick_client.get_connector(multipath, enforce_multipath)
        return self.volumes_client.volumes.initialize_connection(
            self.volume_id, conn_prop)


class VerifyProtocol(VolumeAction):
    # NOTE(e0ne): Only iSCSI and RBD based drivers are supported. NFS doesn't
    # work. Drivers with other protocols are not tested yet.
    SUPPORTED_PROCOTOLS = [connector.ISCSI, connector.RBD]

    def verify(self, protocol):
        protocol = protocol.upper()

        # NOTE(e0ne): iSCSI drivers works without issues, RBD and NFS don't
        # work. Drivers with other protocols are not tested yet.
        if protocol not in VerifyProtocol.SUPPORTED_PROCOTOLS:
            raise exception.ProtocolNotSupported(protocol=protocol)


class ConnectVolume(VolumeAction):
    def connect(self, brick_connector, connection_data,
                mountpoint, mode, hostname):
        device_info = brick_connector.connect_volume(connection_data)

        self.volumes_client.volumes.attach(self.volume_id, instance_uuid=None,
                                           mountpoint=mountpoint,
                                           mode=mode,
                                           host_name=hostname)
        return device_info


class VolumeDetachAction(VolumeAction):
    def __exit__(self, type, value, traceback):
        if traceback:
            self.volumes_client.volumes.roll_detaching(self.volume_id)
            return False
        return True


class BeginDetach(VolumeDetachAction):
    def reserve(self):
        self.volumes_client.volumes.begin_detaching(self.volume_id)


class InitializeConnectionForDetach(InitializeConnection, VolumeDetachAction):
    pass


class DisconnectVolume(VolumeDetachAction):
    def disconnect(self, brick_connector, connection_data, device_info):
        device_info = device_info or {}

        brick_connector.disconnect_volume(connection_data, device_info)


class DetachVolume(VolumeDetachAction):
    def detach(self, brick_client,
               attachment_uuid, multipath, enforce_multipath):
        conn_prop = brick_client.get_connector(multipath, enforce_multipath)

        self.volumes_client.volumes.terminate_connection(self.volume_id,
                                                         conn_prop)
        self.volumes_client.volumes.detach(self.volume_id, attachment_uuid)
