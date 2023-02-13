import enum
from typing import Dict, Set, NamedTuple
import logging

logger = logging.getLogger(__file__)


def _clip_value(value: int, min_value: int = 1, max_value: int = 5) -> int:
    return max(min_value, min(max_value, value))


@enum.unique
class PlayerRole(enum.Enum):
    """Potential roles a player might play on a killer queen team.

    'vanilla and 'speed' refer to warrior type. 'objective' refers to the objective runner.
    """
    OBJECTIVE = 0
    VANILLA = 1
    SPEED = 2
    QUEEN = 3


class PlayerRanking(NamedTuple):
    primary_role: PlayerRole
    secondary_role: PlayerRole
    primary_ranking: int
    secondary_ranking: int


class BasePlayer:
    @property
    def possible_roles(self) -> Set[PlayerRole]:
        raise NotImplementedError


class Player(BasePlayer):
    def __init__(self, name: str, ranking: PlayerRanking) -> None:
        if ranking.primary_role == ranking.secondary_role:
            raise ValueError(f"Primary role cannot be the same as the secondary role! For {name}, got: {ranking}")

        if not (1 <= ranking.primary_ranking <= 5):
            logger.warning(f"Clipping primary ranking so it's between 1-5, got: {ranking.primary_ranking}")
            val = ranking.primary_ranking
            ranking = ranking._replace(primary_ranking=_clip_value(val))

        if not (1 <= ranking.secondary_ranking <= 5):
            logger.warning(f"Clipping secondary ranking so it's between 1-5, got: {ranking.secondary_ranking}")
            val = ranking.secondary_ranking
            ranking = ranking._replace(primary_ranking=_clip_value(val))

        # Below are public attrs
        self.name = name
        self.ranking = ranking

    @property
    def possible_roles(self) -> Set[PlayerRole]:
        return {self.ranking.primary_role, self.ranking.secondary_role}

    def __str__(self) -> str:
        return f"name: {self.name}, ranking: {self.ranking}"

    def __repr__(self) -> str:
        return str(self)


class PlayerFill(BasePlayer):
    def __init__(self, possible_roles: Set[PlayerRole]) -> None:
        self._possible_roles = possible_roles

    @property
    def possible_roles(self) -> Set[PlayerRole]:
        return self._possible_roles


class BasePlayerAssignment:
    @property
    def score(self) -> int:
        raise NotImplementedError


class PlayerAssignment(BasePlayerAssignment):
    def __init__(self, player: Player, assigned_role: PlayerRole):
        self.player = player
        self.assigned_role = assigned_role
        if self.assigned_role not in player.possible_roles:
            raise ValueError(f"Assigned role must be a possible role for the player! Got: {assigned_role} for {player}")
        ranking = player.ranking
        self._score = ranking.primary_ranking if ranking.primary_role == assigned_role else ranking.secondary_ranking

    @property
    def score(self) -> int:
        return self._score

    def __str__(self) -> str:
        return f"player: {self.player.name}, assigned: {self.assigned_role.name}, score {self.score}."

    def __repr__(self) -> str:
        return str(self)


class Team:
    def __init__(self, players: Set[Player], fills: Set[PlayerFill]) -> None:
        self._players = players
        self._fills = fills
        if len(players) + len(fills) != 5:
            raise ValueError(f"Players and fills, once summed, must sum to 5 players total, but got: {self._players} players, {self._fills} fills")
        queens = [PlayerRole.QUEEN in p.possible_roles for p in self._players] + [PlayerRole.QUEEN in f.possible_roles for f in self._fills]
        if len(queens) != 1:
            raise ValueError(f"Exactly one player must have 'queen' as a possible role, got {queens}")
        self._queen = queens[0]
