from dataclasses import dataclass, field


@dataclass
class DLC:
    id: int
    name: str
    is_installed: bool = False
    update_available: bool = False
    files: list[str] = field(default_factory=list)
