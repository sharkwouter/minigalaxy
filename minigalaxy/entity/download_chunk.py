from dataclasses import dataclass


@dataclass
class DownloadChunk:
    chunk_id: int
    from_byte: int
    to_byte: int
    method: str
    checksum: str

    def get_size(self) -> int:
        return self.to_byte - (self.from_byte - 1)  # the -1 is because the from-byte is included
