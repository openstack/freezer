"""
Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

Freezer functions to interact with OpenStack Swift client and server
"""

from cinderclient.v1 import client as ciclient
import time
from glance import ReSizeStream
import logging
from freezer.bandwidth import monkeypatch_socket_bandwidth


def cinder(backup_opt_dict):
    """
    Creates cinder client and attached it ot the dictionary
    :param backup_opt_dict: Dictionary with configuration
    :return: Dictionary with attached cinder client
    """
    options = backup_opt_dict.options

    monkeypatch_socket_bandwidth(backup_opt_dict)

    backup_opt_dict.cinder = ciclient.Client(
        username=options.user_name,
        api_key=options.password,
        project_id=options.tenant_name,
        auth_url=options.auth_url,
        region_name=options.region_name,
        insecure=backup_opt_dict.insecure,
        service_type="volume")
    return backup_opt_dict


def provide_snapshot(backup_dict, volume, snapshot_name):
    """
    Creates snapshot for cinder volume with --force parameter
    :param backup_dict: Dictionary with configuration
    :param volume: volume object for snapshoting
    :param snapshot_name: name of snapshot
    :return: snapshot object
    """
    volume_snapshots = backup_dict.cinder.volume_snapshots
    snapshot = volume_snapshots.create(volume_id=volume.id,
                                       display_name=snapshot_name,
                                       force=True)

    while snapshot.status != "available":
        try:
            logging.info("[*] Snapshot status: " + snapshot.status)
            snapshot = volume_snapshots.get(snapshot.id)
            if snapshot.status == "error":
                logging.error("snapshot have error state")
                exit(1)
            time.sleep(5)
        except Exception as e:
            logging.info(e)
    return snapshot


def do_copy_volume(backup_dict, snapshot):
    """
    Creates new volume from a snapshot
    :param backup_dict: Configuration dictionary
    :param snapshot: provided snapshot
    :return: created volume
    """
    volume = backup_dict.cinder.volumes.create(
        size=snapshot.size,
        snapshot_id=snapshot.id)

    while volume.status != "available":
        try:
            logging.info("[*] Volume copy status: " + volume.status)
            volume = backup_dict.cinder.volumes.get(volume.id)
            time.sleep(5)
        except Exception as e:
            logging.info(e)
            logging.info("[*] Exception getting volume status")
    return volume


def make_glance_image(backup_dict, image_volume_name, copy_volume):
    """
    Creates an glance image from volume
    :param backup_dict: Configuration dictionary
    :param image_volume_name: Name of image
    :param copy_volume: volume to make an image
    :return: Glance image object
    """
    volumes = backup_dict.cinder.volumes
    return volumes.upload_to_image(volume=copy_volume,
                                   force=True,
                                   image_name=image_volume_name,
                                   container_format="bare",
                                   disk_format="raw")


def clean_snapshot(backup_dict, snapshot):
    """
    Deletes snapshot
    :param backup_dict: Configuration dictionary
    :param snapshot: snapshot name
    """
    logging.info("[*] Deleting existed snapshot: " + snapshot.id)
    backup_dict.cinder.volume_snapshots.delete(snapshot)


def download_image(backup_dict, image):
    """
    Creates a stream for image data
    :param backup_dict: Configuration dictionary
    :param image: Image object for downloading
    :return: stream of image data
    """
    stream = backup_dict.glance.images.data(image)
    return ReSizeStream(stream, len(stream), 1000000)
