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

from __future__ import print_function

from cinderclient import exceptions
from os_brick.initiator import connector
from oslo_concurrency import processutils

from freezer.engine.osbrick import brick_utils
from freezer.engine.osbrick import volume_actions as actions


class Client(object):
    version = '1.1.0'

    def __init__(self, volumes_client=None):
        self.volumes_client = volumes_client

    def _brick_get_connector(self, protocol, driver=None,
                             execute=processutils.execute,
                             use_multipath=False,
                             device_scan_attempts=3,
                             *args, **kwargs):
        """Wrapper to get a brick connector object.

        This automatically populates the required protocol as well
        as the root_helper needed to execute commands.
        """
        return connector.InitiatorConnector.factory(
            protocol,
            brick_utils.get_root_helper(),
            driver=driver,
            execute=execute,
            use_multipath=use_multipath,
            device_scan_attempts=device_scan_attempts,
            *args, **kwargs)

    def get_connector(self, multipath=False, enforce_multipath=False):
        conn_prop = connector.get_connector_properties(
            brick_utils.get_root_helper(),
            brick_utils.get_my_ip(),
            multipath=multipath,
            enforce_multipath=(enforce_multipath),
            execute=processutils.execute)
        return conn_prop

    def attach(self, volume_id, hostname, mountpoint=None, mode='rw',
               multipath=False, enforce_multipath=False):

        # Check protocol type of storage backend.
        with actions.VerifyProtocol(self.volumes_client, volume_id) as cmd:
            # Retrieve vol-host attribute of volume.
            volume_info = self.volumes_client.volumes.get(volume_id)
            volume_capabilities = self.volumes_client.capabilities.get(
                volume_info.__dict__['os-vol-host-attr:host'])
            # Retrieve storage_protocol from storage backend capabilities.
            protocol = volume_capabilities.storage_protocol.upper()
            cmd.verify(protocol)

        # Reserve volume before attachment
        with actions.Reserve(self.volumes_client, volume_id) as cmd:
            cmd.reserve()

        with actions.InitializeConnection(
                self.volumes_client, volume_id) as cmd:
            connection = cmd.initialize(self, multipath, enforce_multipath)

        with actions.ConnectVolume(self.volumes_client, volume_id) as cmd:
            brick_connector = self._brick_get_connector(
                protocol, do_local_attach=True)
            device_info = cmd.connect(brick_connector,
                                      connection['data'],
                                      mountpoint, mode, hostname)
            return device_info

    def detach(self, volume_id, attachment_uuid=None, multipath=False,
               enforce_multipath=False, device_info=None):

        with actions.BeginDetach(self.volumes_client, volume_id) as cmd:
            cmd.reserve()

        with actions.InitializeConnectionForDetach(
                self.volumes_client, volume_id) as cmd:
            connection = cmd.initialize(self, multipath, enforce_multipath)

        brick_connector = self._brick_get_connector(
            connection['driver_volume_type'], do_local_attach=True)

        with actions.DisconnectVolume(self.volumes_client, volume_id) as cmd:
            cmd.disconnect(brick_connector, connection['data'], device_info)

        with actions.DetachVolume(self.volumes_client, volume_id) as cmd:
            cmd.detach(self, attachment_uuid, multipath, enforce_multipath)

    def get_volume_paths(self, volume_id, use_multipath=False):
        """Gets volume paths on the system for a specific volume."""
        conn_props = self.get_connector(multipath=use_multipath)
        vols = self.volumes_client.volumes.list()
        vol_in_use = False
        vol_found = False
        for vol in vols:
            if (volume_id == vol.id or volume_id == vol.name):
                vol_found = True
                if vol.status == "in-use":
                    vol_in_use = True
                    # Make sure the volume ID is used and not the name
                    volume_id = vol.id
                break

        if not vol_found:
            msg = "No volume with a name or ID of '%s' exists." % volume_id
            raise exceptions.CommandError(msg)

        paths = []
        if vol_in_use:
            conn_info = self.volumes_client.volumes.initialize_connection(
                volume_id, conn_props)
            protocol = conn_info['driver_volume_type']
            conn = self._brick_get_connector(protocol,
                                             use_multipath=use_multipath)
            paths = conn.get_volume_paths(conn_info['data'])

        return paths

    def get_all_volume_paths(self, protocol, use_multipath=False):
        """Gets all volume paths on the system for a given protocol."""
        conn = self._brick_get_connector(protocol, use_multipath=use_multipath)
        paths = conn.get_all_available_volumes()

        return paths
