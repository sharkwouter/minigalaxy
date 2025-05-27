class FileInfo:
    """
    Just a container for the md5 checksum and file size of a downloadable file
    """
    def __init__(self, md5=None, size=0):
        self.md5 = md5
        self.size = size

    def as_dict(self):
        return {
            "md5": self.md5,
            "size": self.size
        }
