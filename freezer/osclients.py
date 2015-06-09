from bandwidth import monkeypatch_bandwidth
from utils import Bunch
import logging
import time
from utils import ReSizeStream


class ClientManager:
    def __init__(self, options, insecure=True,
                 download_bytes_per_sec=-1, upload_bytes_per_sec=-1,
                 swift_auth_version=2, dry_run=False):
        """
        Creates manager of connections to swift, nova, glance and cinder
        :param options: OpenstackOptions
        :param insecure:
        :param download_bytes_per_sec: information about bandwidth throttling
        :param upload_bytes_per_sec: information about bandwidth throttling
        :param swift_auth_version:
        :param dry_run:
        :return:
        """
        self.options = options
        self.download_bytes_per_sec = download_bytes_per_sec
        self.upload_bytes_per_sec = upload_bytes_per_sec
        self.insecure = insecure
        self.swift_auth_version = swift_auth_version
        self.dry_run = dry_run
        self.cinder = None
        self.swift = None
        self.glance = None
        self.nova = None

    def _monkey_patch(self):
        monkeypatch_bandwidth(self.download_bytes_per_sec,
                              self.upload_bytes_per_sec)

    def get_cinder(self):
        if not self.cinder:
            self.create_cinder()
        return self.cinder

    def get_swift(self):
        if not self.swift:
            self.create_swift()
        return self.swift

    def get_glance(self):
        if not self.glance:
            self.create_glance()
        return self.glance

    def get_nova(self):
        if not self.nova:
            self.create_nova()
        return self.nova

    def create_cinder(self):
        """
        Creates client for cinder and caches it
        :return:
        """
        from cinderclient.v1 import client
        self._monkey_patch()
        options = self.options
        logging.info("[*] Creation of cinder client")
        self.cinder = client.Client(
            username=options.user_name,
            api_key=options.password,
            project_id=options.tenant_name,
            auth_url=options.auth_url,
            region_name=options.region_name,
            insecure=self.insecure,
            service_type="volume")
        return self.cinder

    def create_swift(self):
        """
        Creates client for swift and caches it
        :return:
        """
        import swiftclient
        self._monkey_patch()
        options = self.options
        logging.info("[*] Creation of swift client")

        self.swift = swiftclient.client.Connection(
            authurl=options.auth_url,
            user=options.user_name, key=options.password,
            tenant_name=options.tenant_name,
            os_options=options.os_options,
            auth_version=self.swift_auth_version,
            insecure=self.insecure, retries=6)

        if self.dry_run:
            self.swift = DryRunSwiftclientConnectionWrapper(self.swift)
        return self.swift

    def create_glance(self):
        """
        Creates client for glance and caches it
        :return:
        """
        from glanceclient.v1 import client
        from glanceclient.shell import OpenStackImagesShell

        self._monkey_patch()
        options = self.options

        logging.info("[*] Creation of glance client")

        endpoint, token = OpenStackImagesShell()._get_endpoint_and_token(
            Bunch(os_username=options.user_name,
                  os_password=options.password,
                  os_tenant_name=options.tenant_name,
                  os_auth_url=options.auth_url,
                  os_region_name=options.region_name,
                  force_auth=False))

        self.glance = client.Client(endpoint=endpoint, token=token)
        return self.glance

    def create_nova(self):
        """
        Creates client for nova and caches it
        :return:
        """
        from novaclient.v2 import client

        self._monkey_patch()
        options = self.options
        logging.info("[*] Creation of nova client")

        self.nova = client.Client(
            username=options.user_name,
            api_key=options.password,
            project_id=options.tenant_name,
            auth_url=options.auth_url,
            region_name=options.region_name,
            insecure=self.insecure)

        return self.nova

    def provide_snapshot(self, volume, snapshot_name):
        """
        Creates snapshot for cinder volume with --force parameter
        :param volume: volume object for snapshoting
        :param snapshot_name: name of snapshot
        :return: snapshot object
        """
        snapshot = self.get_cinder().volume_snapshots.create(
            volume_id=volume.id,
            display_name=snapshot_name,
            force=True)

        while snapshot.status != "available":
            try:
                logging.info("[*] Snapshot status: " + snapshot.status)
                snapshot = self.get_cinder().volume_snapshots.get(snapshot.id)
                if snapshot.status == "error":
                    logging.error("snapshot have error state")
                    exit(1)
                time.sleep(5)
            except Exception as e:
                logging.info(e)
        return snapshot

    def do_copy_volume(self, snapshot):
        """
        Creates new volume from a snapshot
        :param snapshot: provided snapshot
        :return: created volume
        """
        volume = self.get_cinder().volumes.create(
            size=snapshot.size,
            snapshot_id=snapshot.id)

        while volume.status != "available":
            try:
                logging.info("[*] Volume copy status: " + volume.status)
                volume = self.get_cinder().volumes.get(volume.id)
                time.sleep(5)
            except Exception as e:
                logging.info(e)
                logging.info("[*] Exception getting volume status")
        return volume

    def make_glance_image(self, image_volume_name, copy_volume):
        """
        Creates an glance image from volume
        :param image_volume_name: Name of image
        :param copy_volume: volume to make an image
        :return: Glance image object
        """
        return self.get_cinder().volumes.upload_to_image(
            volume=copy_volume,
            force=True,
            image_name=image_volume_name,
            container_format="bare",
            disk_format="raw")

    def clean_snapshot(self, snapshot):
        """
        Deletes snapshot
        :param snapshot: snapshot name
        """
        logging.info("[*] Deleting existed snapshot: " + snapshot.id)
        self.get_cinder().volume_snapshots.delete(snapshot)

    def download_image(self, image):
        """
        Creates a stream for image data
        :param image: Image object for downloading
        :return: stream of image data
        """
        stream = self.get_glance().images.data(image)
        return ReSizeStream(stream, len(stream), 1000000)


class DryRunSwiftclientConnectionWrapper:
    def __init__(self, sw_connector):
        self.sw_connector = sw_connector
        self.get_object = sw_connector.get_object
        self.get_account = sw_connector.get_account
        self.get_container = sw_connector.get_container
        self.head_object = sw_connector.head_object
        self.put_object = self.dummy
        self.put_container = self.dummy
        self.delete_object = self.dummy

    def dummy(self, *args, **kwargs):
        pass
