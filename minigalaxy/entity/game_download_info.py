from dataclasses import dataclass
from typing import List, Optional, Dict

from minigalaxy.entity.download_info import DownloadInfo
from minigalaxy.game import Game


@dataclass
class GameDownloadInfo:
    name: Game
    os: str
    language: str
    language_full: str
    total_size: int
    files: List[DownloadInfo]
    version: Optional[str]

    @staticmethod
    def from_dict(data: Dict) -> 'GameDownloadInfo':
        return GameDownloadInfo(
            name=data["name"],
            os=data["os"],
            language=data.get("language", ""),
            language_full=data.get("language_full", ""),
            version=data.get("version"),
            total_size=data["total_size"],
            files=[],
        )
