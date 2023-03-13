from collections import defaultdict
from typing import Dict, List, Set

from src.data_types.player import Player, PlayerAssignment, PlayerRole


def roles_to_average_score(all_players: Set[Player]) -> Dict[PlayerRole, float]:
    role_to_players: Dict[PlayerRole, List[float]] = {}
    for player in all_players:
        if player.primary_role not in role_to_players:
            role_to_players[player.primary_role] = []
        role_to_players[player.primary_role].append(player.ranking[player.primary_role])
    to_return = {key: sum(val) / len(val) for key, val in role_to_players.items()}
    return to_return


class TeamComposition:

    roles: List[PlayerRole] = [
        PlayerRole.QUEEN,
        PlayerRole.SPEED,
        PlayerRole.FLEX,
        PlayerRole.FLEX,
        PlayerRole.OBJECTIVE,
    ]

    @classmethod
    def total_score_for_ranking(cls, ranking: Dict[PlayerRole, float]) -> float:
        score_list = [ranking[role] for role in cls.roles]
        return round(sum(score_list), 2)

    @classmethod
    def weighted_score_for_ranking(cls, ranking: Dict[PlayerRole, float]) -> float:
        score_list = [Player.weighted_score_for_role(role, ranking[role]) for role in cls.roles]
        return round(sum(score_list), 2)

    @classmethod
    def validate_team(cls, team: List[PlayerAssignment], allow_missing: bool = False) -> None:
        expected_counts: Dict[PlayerRole, float] = defaultdict(int)
        for role in cls.roles:
            expected_counts[role] += 1

        team_counts: Dict[PlayerRole, float] = defaultdict(int)
        for player in team:
            team_counts[player.assigned_role] += 1
        team_player_diff: Dict[PlayerRole, float] = {
            role: team_counts[role] - expected_counts[role] for role in expected_counts
        }
        err_str = ""
        for role, diff in team_player_diff.items():
            if (not allow_missing and diff != 0) or (allow_missing and diff > 0):
                err_str += f"Should have had {expected_counts[role]} players {role.name} but got {team_counts[role]}!\n"
        if err_str:
            err_str += f"Team players: {[p.player.name for p in team]}"
            raise ValueError(err_str)


class Team:
    def __init__(self, players: List[PlayerAssignment]) -> None:
        self.players = players

        TeamComposition.validate_team(self.players, allow_missing=True)

        self._queen = self._get_role(PlayerRole.QUEEN)
        self._speed = self._get_role(PlayerRole.SPEED)
        self._objective = self._get_role(PlayerRole.OBJECTIVE)

        names = {
            self._queen.player.name,
            self._speed.player.name,
            self._objective.player.name,
        }
        self._flex_players = [p for p in players if p.player.name not in names]
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
        return sum([p.score for p in self.players])

    @property
    def total_weighted_score(self) -> float:
        return round(sum([p.weighted_score for p in self.players]), 3)

    @property
    def num_fills(self) -> int:
        return self._num_fills

    @property
    def needs_fill(self) -> bool:
        return self._num_fills > 0

    @property
    def team_name(self) -> str:
        return self._queen.player.name

    def format(self, hide_scores: bool = False) -> str:
        role_to_print = {
            PlayerRole.QUEEN: "Queen",
            PlayerRole.SPEED: "Speed",
            PlayerRole.OBJECTIVE: "Obj  ",
            PlayerRole.FLEX: "Flex ",
        }
        to_return = ""
        for p in [self._queen, self._speed, self._objective, *self._flex_players]:
            if hide_scores:
                to_return += f"{role_to_print[p.assigned_role]}: {p.player.name}\n"
            else:
                to_return += f"{role_to_print[p.assigned_role]}: {p.player.name}, {p.score}\n"
        if self._num_fills > 0:
            to_return += f"Fills: {self._num_fills} required\n"
        if not hide_scores:
            to_return += f"Total score: {self.total_score}, weighted: {self.total_weighted_score}\n"
        return to_return

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return str(self)
