from dataclasses import dataclass
import shlex

from minigalaxy.game import Game
from minigalaxy.game import InfoKey


@dataclass
class LaunchCommand:
    name: str
    command: list[str]

    def apply_game_launch_config(self, game: Game) -> None:
        if game.get_info(InfoKey.GAMEMODE) is True:
            self.command.insert(0, "gamemoderun")
        if game.get_info(InfoKey.MANGOHUD) is True:
            self.command.insert(0, "mangohud")
            self.command.insert(1, "--dlsym")

        var_list = shlex.split(game.get_info(InfoKey.VARIABLES))
        command_list = shlex.split(game.get_info(InfoKey.COMMAND))

        if var_list:
            if var_list[0] not in ["env"]:
                var_list.insert(0, "env")
            if 'env' == self.command[0]:
                self.command = self.command[1:]

        self.command = var_list + self.command + command_list
