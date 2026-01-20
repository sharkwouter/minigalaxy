from enum import Enum


class TranslatorType(Enum):
    OS = "os"
    ISA = "isa"


class Translator:
    def __init__(self, name, type, path, icon=None, version=None, description=None, custom=False):
        self.name = name  # e.g., "Wine", "Proton-GE", "FEX", "QEMU"
        self.type = TranslatorType(type)  # OS or ISA
        self.path = path  # Executable path
        self.icon = icon  # Path to icon file (optional)
        self.version = version  # Version string (optional)
        self.description = description  # Description/help text (optional)
        self.custom = custom  # True if user-defined

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type.value,
            "path": self.path,
            "icon": self.icon,
            "version": self.version,
            "description": self.description,
            "custom": self.custom,
        }

    @staticmethod
    def from_dict(data):
        return Translator(
            name=data["name"],
            type=data["type"],
            path=data["path"],
            icon=data.get("icon"),
            version=data.get("version"),
            description=data.get("description"),
            custom=data.get("custom", False),
        )
