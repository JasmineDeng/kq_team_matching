from src.data_types.player import Player
from src.data_types.player_pool import PlayerPool


class Exclusion:
    """Two players who will not play together, at least given certain criteria.

    Behind the scenes it is implemented using a PlayerPool, as that handles all the weirdness around names
    """

    def __init__(self, requester: Player, other_player: Player, only_if_they_queen: bool) -> None:
        self.requester = requester
        self.other_player = other_player
        self.player_pool = PlayerPool([requester, other_player])
        self.only_if_they_queen = only_if_they_queen

    def __str__(self) -> str:
        return f"Exclusion({self.requester.name}, {self.other_player.name}, {self.only_if_they_queen})"
