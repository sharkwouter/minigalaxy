class Game:
    def __init__(self, name: str, game_id: int, image_url: str):
        self.name = name
        self.id = game_id
        self.image_url = image_url

    def __str__(self):
        return self.name


