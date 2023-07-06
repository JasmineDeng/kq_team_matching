import enum
from typing import Dict


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
                print(f"Clipping ranking so it's between 1-10, got: {rank}")
                ranking[role] = clip_value(rank)

        # Below are public attrs
        self.name = name
        self.ranking = ranking
        self.primary_role = primary_role

    def to_primary_role_assignment(self) -> "PlayerAssignment":
        return PlayerAssignment(player=self, assigned_role=self.primary_role)

    @classmethod
    def weighted_score_for_role(cls, role: PlayerRole, score: float) -> float:
        if role == PlayerRole.QUEEN:
            weight = 0.275
        elif role == PlayerRole.SPEED:
            weight = 0.225
        elif role == PlayerRole.FLEX:
            weight = 0.1875
        elif role == PlayerRole.OBJECTIVE:
            weight = 0.125
        else:
            weight = 1.0
        return round(weight * score, 3)

    def __str__(self) -> str:
        return f"name: {self.name}, primary role: {self.primary_role}, ranking: {self.ranking}"

    def __repr__(self) -> str:
        return str(self)


class BasePlayerAssignment:
    @property
    def score(self) -> float:
        raise NotImplementedError

    @property
    def weighted_score(self) -> float:
        raise NotImplementedError


class PlayerAssignment(BasePlayerAssignment):
    def __init__(self, player: Player, assigned_role: PlayerRole) -> None:
        self.player = player
        self.assigned_role = assigned_role
        ranking = player.ranking
        self._score = ranking[assigned_role]

    @property
    def score(self) -> float:
        return self._score

    @property
    def weighted_score(self) -> float:
        return self.player.weighted_score_for_role(self.assigned_role, self.score)

    def __str__(self) -> str:
        return f"player: {self.player.name} {self.assigned_role.name}, weighted {self.weighted_score}."

    def __repr__(self) -> str:
        return str(self)
