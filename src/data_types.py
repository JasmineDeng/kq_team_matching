import enum
from typing import Dict, List


def clip_value(value: float, min_value: float = 1.0, max_value: float = 10.0) -> float:
    return max(min_value, min(max_value, value))


@enum.unique
class PlayerRole(enum.Enum):
    """Potential roles a player might play on a killer queen team.

    'speed' refers to warrior type, and should be hand-selected. 'objective' refers to the objective runner.
    """

    OBJECTIVE = 0
    FLEX = 1
    SPEED = 2
    QUEEN = 3


class Player:
    def __init__(self, name: str, primary_role: PlayerRole, ranking: Dict[PlayerRole, float]) -> None:

        for role, rank in ranking.items():
            if not (1 <= rank <= 10):
                print(f"Clipping ranking so it's between 1-5, got: {rank}")
                ranking[role] = clip_value(rank)

        # Below are public attrs
        self.name = name
        self.ranking = ranking
        self.primary_role = primary_role

    def __str__(self) -> str:
        return f"name: {self.name}, primary role: {self.primary_role}, ranking: {self.ranking}"

    def __repr__(self) -> str:
        return str(self)


class BasePlayerAssignment:
    @property
    def score(self) -> int:
        raise NotImplementedError


class PlayerAssignment(BasePlayerAssignment):
    def __init__(self, player: Player, assigned_role: PlayerRole) -> None:
        self.player = player
        self.assigned_role = assigned_role
        ranking = player.ranking
        self._score = ranking[assigned_role]

    @property
    def score(self) -> float:
        weight = 1.0
        if self.assigned_role == PlayerRole.QUEEN:
            weight = 0.275
        elif self.assigned_role == PlayerRole.SPEED:
            weight = 0.25
        elif self.assigned_role == PlayerRole.FLEX:
            weight = 0.175
        elif self.assigned_role == PlayerRole.OBJECTIVE:
            weight = 0.125
        return round(self._score * weight, 3)

    def __str__(self) -> str:
        return f"player: {self.player.name}, assigned: {self.assigned_role.name}, score {self.score}."

    def __repr__(self) -> str:
        return str(self)


class Team:
    def __init__(self, players: List[PlayerAssignment]) -> None:
        self.players = players
        self._queen = self._get_role(PlayerRole.QUEEN)
        self._speed = self._get_role(PlayerRole.SPEED)
        self._objective = self._get_role(PlayerRole.OBJECTIVE)

        names = {
            self._queen.player.name,
            self._speed.player.name,
            self._objective.player.name,
        }
        self._other_players = [p for p in players if p.player.name not in names]
        self._num_fills = 5 - len(players)
        if len(players) > 5:
            raise ValueError(f"Can't have more than 5 players on a team! Got: {len(players)}")

    def _get_role(self, role: PlayerRole) -> PlayerAssignment:
        players = [p for p in self.players if p.assigned_role == role]
        if len(players) == 0:
            error_string = f"Expected to find at least one role {role} from players {self.players}"
            if role == PlayerRole.QUEEN:
                error_string += "Currently all teams MUST have a queen, queen fills are not implemented."
            raise ValueError(error_string)
        return players[0]

    @property
    def total_score(self) -> float:
        return round(sum([p.score for p in self.players]), 3)

    @property
    def num_fills(self) -> int:
        return self._num_fills

    @property
    def needs_fill(self) -> bool:
        return self._num_fills > 0

    @property
    def team_name(self) -> str:
        return self._queen.player.name

    def __str__(self) -> str:
        role_to_print = {
            PlayerRole.QUEEN: "Queen",
            PlayerRole.SPEED: "Speed",
            PlayerRole.OBJECTIVE: "Obj  ",
            PlayerRole.FLEX: "Flex ",
        }
        to_return = ""
        for p in [self._queen, self._speed, self._objective, *self._other_players]:
            to_return += f"{role_to_print[p.assigned_role]}: {p.player.name}, {p.score}\n"
        if self._num_fills > 0:
            to_return += f"Fills: {self._num_fills} required\n"
        to_return += f"Total score: {self.total_score}\n"
        return to_return

    def __repr__(self) -> str:
        return str(self)
