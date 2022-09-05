class FileInfo:
    """
    Just a container for the md5 checksum and file size of a downloadable file
    """
    def __init__(self, md5, size):
        self.md5 = md5
        self.size = size
