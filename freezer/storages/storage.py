class AbstractStorage(object):

    def upload_manifest(self, name, meta_dict):
        """
        Manifest can be different for different types of storage.

        Each storage should have idea how to work with data.

        For example:
            Swift can create an empty file with metainformation or can
            create file with json (For example amount of information exceeds
            256 bytes (limit for metadata in Swift).

            FileSystem can create a file with information about descriptions,
            authors and etc.

            Amazon S3 can keep this information in its own manner.

        :param name: Name of manifest file
        :type name: str
        :param meta_dict: Dict with metainformation
        :type meta_dict: dict
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    def upload_chunk(self, content, path):
        raise NotImplementedError("Should have implemented this")

    def prepare(self):
        raise NotImplementedError("Should have implemented this")

    def ready(self):
        raise NotImplementedError("Should have implemented this")
