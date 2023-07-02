from dataclasses import dataclass


@dataclass
class DownloadChunk:
    chunk_id: int
    from_byte: int
    to_byte: int
    method: str
    checksum: str
