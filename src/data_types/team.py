import csv
import logging
from collections import defaultdict
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

from src.data_types.player import Player, PlayerAssignment, PlayerRole


class _SerializedTeamRow(NamedTuple):
    role: str
    name: str
    score: str
    weighted_score: str


class PlayerRoleMetadata(NamedTuple):
    role: PlayerRole
    allows_fill: bool
    requires_exact_count: bool


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
    def role_metadata(cls) -> List[PlayerRoleMetadata]:
        to_return = [
            PlayerRoleMetadata(role=PlayerRole.QUEEN, allows_fill=False, requires_exact_count=True),
            PlayerRoleMetadata(role=PlayerRole.SPEED, allows_fill=False, requires_exact_count=False),
            PlayerRoleMetadata(role=PlayerRole.FLEX, allows_fill=True, requires_exact_count=False),
            PlayerRoleMetadata(role=PlayerRole.OBJECTIVE, allows_fill=False, requires_exact_count=True),
        ]
        roles_to_return = [val.role for val in to_return]
        assert all(role in cls.roles for role in roles_to_return)
        return to_return

    @classmethod
    def role_allows_fill(cls, role: PlayerRole) -> bool:
        for metadata in cls.role_metadata():
            if metadata.role == role:
                return metadata.allows_fill
        raise ValueError(f"Invalid role {role}, not in team composition {cls.roles}")

    @classmethod
    def role_counts(cls) -> List[Tuple[PlayerRole, int]]:
        """Return a list of the role and the corresponding count in the same order as the roles list."""
        counts: Dict[PlayerRole, int] = defaultdict(int)
        for role in cls.roles:
            counts[role] += 1
        return [(role, counts[role]) for role in counts]

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
        role_counts = {role: count for role, count in cls.role_counts()}
        role_to_metadata = {metadata.role: metadata for metadata in cls.role_metadata()}

        team_counts: Dict[PlayerRole, float] = defaultdict(int)
        for player in team:
            team_counts[player.assigned_role] += 1
        # If diff > 0, then the team has extra players, otherwise they are missing a player.
        team_player_diff: Dict[PlayerRole, float] = {
            role: team_counts[role] - role_counts[role] for role in role_counts
        }
        err_str = ""
        for role, diff in team_player_diff.items():
            if allow_missing and diff < 0:
                continue
            allows_fill = role_to_metadata[role].allows_fill
            if (not allows_fill and diff != 0) or (allows_fill and diff > 0):
                err_str += f"Should have had {role_counts[role]} players {role.name} but got {team_counts[role]}!\n"
        if err_str:
            err_str += f"Team players: {[p.player.name for p in team]}"
            raise ValueError(err_str)

    @classmethod
    def remaining_roles_required(cls, players: List[PlayerAssignment]) -> List[PlayerRole]:
        missing_roles = []
        current_role_counts: Dict[PlayerRole, int] = defaultdict(int)
        expected_role_counts: Dict[PlayerRole, int] = {key: val for key, val in TeamComposition.role_counts()}
        for p in players:
            current_role_counts[p.assigned_role] += 1
        for role, count in expected_role_counts.items():
            diff = count - current_role_counts[role]
            if diff < 0:
                raise ValueError(
                    f"Should not be possible: team with players {players} has too many for role {role.name}, "
                    f"should have at most {count} but has {current_role_counts[role]}"
                )
            if diff > 0:
                missing_roles.extend([role] * diff)
        return missing_roles


class Team:

    NUM_ROWS_SERIALIZED = 6
    """The number of CSV rows when the team is serialized.

    Presently, we have one row for the player names and one row for the scores.
    """

    def __init__(self, players: List[PlayerAssignment]) -> None:
        self.players = players

        TeamComposition.validate_team(self.players, allow_missing=True)

        self._queen = self._get_role(PlayerRole.QUEEN)
        self._speed = self._get_role(PlayerRole.SPEED)
        self._objective = self._get_role(PlayerRole.OBJECTIVE)
        self._flex_players = [p for p in players if p.assigned_role == PlayerRole.FLEX]
        self._num_fills = 5 - len(players)
        if len(players) > 5:
            raise ValueError(f"Can't have more than 5 players on a team! Got: {len(players)}")

    def _get_role(self, role: PlayerRole) -> Optional[PlayerAssignment]:
        players = [p for p in self.players if p.assigned_role == role]
        if len(players) == 0:
            return None
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
        team_name = self._queen.player.name if self._queen is not None else "team unknown"
        return team_name

    def format(self, hide_scores: bool = False) -> str:
        role_to_print = {
            PlayerRole.QUEEN: "Queen",
            PlayerRole.SPEED: "Speed",
            PlayerRole.OBJECTIVE: "Obj  ",
            PlayerRole.FLEX: "Flex ",
        }
        to_return = ""
        for role, count in TeamComposition.role_counts():
            player = [p for p in self.players if p.assigned_role == role]
            assert len(player) <= count
            for p in player:
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

    def to_csv(self) -> list[list[str]]:
        serialized_rows = serialize_players_in_order(self.players)
        to_return: list[list[str]] = [list(elem) for elem in serialized_rows]
        # Add weighted and total scores
        row = _SerializedTeamRow(
            name="", role="", score=str(self.total_score), weighted_score=str(self.total_weighted_score)
        )
        to_return.append(list(row))

        # Assert the number of serialized rows is correct
        assert len(to_return) == self.NUM_ROWS_SERIALIZED

        return to_return

    @classmethod
    def from_csv(cls, csv_data: list[list[str]], players: list[Player]) -> "Team":
        name_to_role = {}
        name_to_score = {}
        name_to_weighted_score = {}
        for row in csv_data:
            team_row = _SerializedTeamRow(*row)  # type: ignore
            # Assume that these rows contain the total scores
            if not team_row.role and not team_row.name:
                logging.info(f"Found row: {row} that does not represent player. Stopping deserialization.")
                break

            name_to_role[team_row.name] = PlayerRole[team_row.role]
            name_to_score[team_row.name] = float(team_row.score)
            name_to_weighted_score[team_row.name] = float(team_row.weighted_score)

        team_players = []
        for p in players:
            if p.name in name_to_role:
                player_role = name_to_role[p.name]
                assignment = PlayerAssignment(player=p, assigned_role=player_role)
                if (
                    assignment.score != name_to_score[p.name]
                    or assignment.weighted_score != name_to_weighted_score[p.name]
                ):
                    logging.warning(
                        f"Score mismatch for player {p.name}, expected {name_to_score[p.name]}, weighted {name_to_weighted_score[p.name]}, but got {assignment.score}. Was their score updated?"
                    )
                team_players.append(assignment)
        return cls(team_players)


def write_teams_to_csv(output_file_name: str, teams: list[Team]) -> None:
    with open(output_file_name, "w") as f:
        writer = csv.writer(f)
        for team in teams:
            writer.writerows(team.to_csv())
            writer.writerow([])


def serialize_players_in_order(player_assignments: list[PlayerAssignment]) -> list[_SerializedTeamRow]:
    """Reorder players so that the players are in the same order as the team composition.

    This is useful for when you want to compare the same players across different team compositions.
    """
    role_to_assignments: dict[PlayerRole, list[PlayerAssignment]] = {role: [] for role in PlayerRole}
    for p in player_assignments:
        role_to_assignments[p.assigned_role].append(p)
    # Sort by name so that the order is consistent
    for role in role_to_assignments:
        role_to_assignments[role].sort(key=lambda assignment: assignment.player.name)

    to_return = []
    for role in TeamComposition.roles:
        current_assignments = role_to_assignments[role]
        if len(current_assignments) == 0 and not TeamComposition.role_allows_fill(role):
            raise ValueError(f"Missing player for role {role}")
        elif len(current_assignments) == 0:
            to_return.append(_SerializedTeamRow(name="", role="", score="", weighted_score=""))
        else:
            assignment = current_assignments.pop()
            to_return.append(
                _SerializedTeamRow(
                    name=assignment.player.name,
                    role=assignment.assigned_role.name,
                    score=str(assignment.score),
                    weighted_score=str(assignment.weighted_score),
                )
            )

    # If anybody is left, then there are more players than the team composition allows.
    for role, assignments in role_to_assignments.items():
        if len(assignments) > 0:
            raise ValueError(
                f"Too many players for team composition! Got {assignments} for role {role}, but expected {TeamComposition.roles}"
            )

    return to_return
