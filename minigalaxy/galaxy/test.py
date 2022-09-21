import dataclasses
from dataclasses import dataclass, is_dataclass
from typing import get_type_hints, Optional, List, get_args


@dataclass
class TestList:
    items: List[str]


@dataclass
class Category:
    id: Optional[int]
    name: str


@dataclass
class Test:
    id: int
    name: str
    category: Category


class NotADataClassException(BaseException):
    pass


class NotAClassException(BaseException):
    pass


def dict_to_dataclass(d: dict, c: type):
    if not is_dataclass(c):
        raise NotADataClassException(f"Variable c was not set to a dataclass")

    args = []
    fields = dataclasses.fields(c)
    for field in fields:
        if field.name in d:
            if is_dataclass(field.type):
                args.append(dict_to_dataclass(d[field.name], field.type))
            elif type(d[field.name]) is list:
                print(type(d[field.name]))
                print(field.type.__origin__)
                arg = []
                list_type = field.type.__args__[0]
                if is_dataclass(list_type):
                    for a in d[field.name]:
                        arg.append(dict_to_dataclass(a, list_type))
                args.append(arg)
            else:
                args.append(d[field.name])
        else:
            if is_dataclass(field.type):
                args.append(dict_to_dataclass({}, field.type))
            elif field.type == list:
                args.append([])
            elif field.type == str:
                args.append("")
            elif field.type == int or field.type == float:
                args.append(0)
            else:
                args.append(None)
    return c(*args)


def main():
    tstl = TestList(["test"])
    print(get_type_hints(TestList))
    print(get_args(get_type_hints(tstl)["items"]))
    ds = [
        {"id": 1, "name": "test1", "category": {"id": 1, "test": 1, "name": "file"}},
        {"id": 2, "name": "test2"},
        {"id": 3, "name": "test3"},
        {},
        {"id": 5},
        {"name": "test6"},
    ]
    tests = []
    for d in ds:
        test = dict_to_dataclass(d, Test)
        print(test)
        tests.append(test)


if __name__ == "__main__":
    main()
