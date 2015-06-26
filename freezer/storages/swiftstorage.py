import logging
import time
from copy import deepcopy
from freezer.storages.storage import AbstractStorage
from freezer.utils import segments_name


class SwiftStorage(AbstractStorage):
    """
    :type client_manager: freezer.osclients.ClientManager
    """

    def __init__(self, client_manager, container):
        """
        :type client_manager: freezer.osclients.ClientManager
        :type container: str
        """
        self.client_manager = client_manager
        self.container = container
        self.segments = segments_name(container)

    def upload_chunk(self, content, path):
        """
        """
        # If for some reason the swift client object is not available anymore
        # an exception is generated and a new client object is initialized/
        # If the exception happens for 10 consecutive times for a total of
        # 1 hour, then the program will exit with an Exception.

        count = 0
        success = False
        while not success:
            try:
                logging.info(
                    '[*] Uploading file chunk index: {0}'.format(path))
                self.client_manager.get_swift().put_object(
                    self.segments, path, content,
                    content_type='application/octet-stream',
                    content_length=len(content))
                logging.info('[*] Data successfully uploaded!')
                success = True
            except Exception as error:
                logging.info(
                    '[*] Retrying to upload file chunk index: {0}'.format(
                        path))
                time.sleep(60)
                self.client_manager.create_swift()
                count += 1
                if count == 10:
                    logging.critical('[*] Error: add_object: {0}'
                                     .format(error))
                    raise Exception("cannot add object to storage")

    def upload_manifest(self, name, manifest_meta_dict):
        """
        Upload Manifest to manage segments in Swift

        :param name: Name of manifest file
        :type name: str
        :param manifest_meta_dict: Dict with metainformation
        :type manifest_meta_dict: dict
        """

        if not manifest_meta_dict:
            raise Exception('Manifest Meta dictionary not available')

        sw = self.client_manager.get_swift()
        self.client_manager.get_nova()
        tmp_manifest_meta = dict()
        for key, value in manifest_meta_dict.items():
            if key.startswith('x-object-meta'):
                tmp_manifest_meta[key] = value
        manifest_meta_dict = deepcopy(tmp_manifest_meta)
        header = manifest_meta_dict
        manifest_meta_dict['x-object-manifest'] = u'{0}/{1}'.format(
            self.segments, name.strip())
        logging.info('[*] Uploading Swift Manifest: {0}'.format(header))
        sw.put_object(container=self.container, obj=name,
                      contents=u'', headers=header)
        logging.info('[*] Manifest successfully uploaded!')

    def ready(self):
        return self.check_container_existence()[0]

    def prepare(self):
        containers = self.check_container_existence()
        if not containers[0]:
            self.client_manager.get_swift().put_container(self.container)
        if not containers[1]:
            self.client_manager.get_swift().put_container(
                segments_name(self.container))

    def check_container_existence(self):
        """
        Check if the provided container is already available on Swift.
        The verification is done by exact matching between the provided
        container name and the whole list of container available for the swift
        account.
        """
        sw_connector = self.client_manager.get_swift()
        containers_list = [c['name'] for c in sw_connector.get_account()[1]]
        return (self.container in containers_list,
                segments_name(self.container) in containers_list)

    def add_object(self, max_segment_size, backup_queue, absolute_file_path,
                   time_stamp):
        """
        Upload object on the remote swift server
        """
        file_chunk_index, file_chunk = backup_queue.get().popitem()
        package_name = absolute_file_path.split('/')[-1]
        while file_chunk_index or file_chunk:
            package_name = u'{0}/{1}/{2}/{3}'.format(
                package_name, time_stamp,
                max_segment_size, file_chunk_index)
            self.upload_chunk(file_chunk, package_name)
            file_chunk_index, file_chunk = backup_queue.get().popitem()
