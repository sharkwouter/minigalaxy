class Game:
    def __init__(self, name: str, game_id: int, image_url: str):
        self.__name = name
        self.__id = game_id
        self.__image_url = image_url

    def get_name(self) -> str:
        return self.__name

    def get_id(self) -> str:
        return self.__id

    def get_image_url(self) -> str:
        return self.__image_url

    def __str__(self):
        return "{}: {}, {}".format(self.__id, self.__name, self.__image_url)


