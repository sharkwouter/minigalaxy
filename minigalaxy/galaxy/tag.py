from dataclasses import dataclass


@dataclass
class Tag:
    id: int
    name: str
    productCount: int

    @staticmethod
    def from_dict(d: dict) -> 'Tag':
        return Tag(
            id=d["id"] if "id" in d else 0,
            name=d["name"] if "name" in d else "",
            productCount=d["productCount"] if "productCount" in d else 0,
        )
