from dataclasses import dataclass


@dataclass
class LaunchCommand:
    name: str
    command: list[str]
