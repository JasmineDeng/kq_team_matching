import csv
import logging
import os
from collections import defaultdict
from typing import Dict, List, NamedTuple, Optional, Tuple

from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerNamePool


class _SerializedTeamRow(NamedTuple):
    role: str
    name: str
    score: str
    weighted_score: str


class PlayerRoleMetadata(NamedTuple):
    """Metadata about a player role, such as if they allow a fill."""

    role: PlayerRole
    """The role this metadata is for."""

    allows_fill: bool
    """If True, then this role can have a 'fill' player on a team.

    This means that if the TeamComposition specifies 2 players for a certain role, and a fill is allowed, then there can
    be 0, 1, or 2 players on the team with that role. If no fills are allowed, then there must be exactly 2 players with
    that role on the team.
    """

    requires_exact_count: bool
    """If True, then this role must have the exact number of players defined in the TeamComposition during assignment.

    For example, for QUEEN and OBJECTIVE we may want exactly one queen per team, and one objective per team, so we
    require the number of players with those roles to be exactly the number of teams. But for other roles, like SPEED,
    because SPEED players can also FLEX, we can have more players assigned SPEED than the number of teams.
    """


def roles_to_average_score(all_players: list[PlayerAssignment]) -> Dict[PlayerRole, float]:
    role_to_players: Dict[PlayerRole, List[float]] = {}
    for player in all_players:
        if player.assigned_role not in role_to_players:
            role_to_players[player.assigned_role] = []
        role_to_players[player.assigned_role].append(player.score)
    to_return = {key: sum(val) / len(val) for key, val in role_to_players.items()}
    return to_return


class TeamComposition:
    @classmethod
    def get_roles(cls) -> list[PlayerRole]:
        raise NotImplementedError("Must be implemented by subclass")

    @classmethod
    def role_metadata(cls) -> dict[PlayerRole, PlayerRoleMetadata]:
        metadata_list = [
            PlayerRoleMetadata(role=PlayerRole.QUEEN, allows_fill=False, requires_exact_count=True),
            PlayerRoleMetadata(role=PlayerRole.SPEED, allows_fill=False, requires_exact_count=False),
            PlayerRoleMetadata(role=PlayerRole.FLEX, allows_fill=True, requires_exact_count=False),
            PlayerRoleMetadata(role=PlayerRole.OBJECTIVE, allows_fill=False, requires_exact_count=True),
        ]
        roles_to_return = [val.role for val in metadata_list]
        assert all(role in roles_to_return for role in cls.get_roles())
        metadata_dict = {val.role: val for val in metadata_list}
        return metadata_dict

    @classmethod
    def get_role_metadata(cls, role: PlayerRole) -> PlayerRoleMetadata:
        if role not in cls.role_metadata():
            raise ValueError(f"Invalid role {role}, not in team composition {cls.get_roles()}")
        return cls.role_metadata()[role]

    @classmethod
    def role_allows_fill(cls, role: PlayerRole) -> bool:
        return cls.get_role_metadata(role).allows_fill

    @classmethod
    def role_counts(cls) -> List[Tuple[PlayerRole, int]]:
        """Return a list of the role and the corresponding count in the same order as the roles list."""
        counts: Dict[PlayerRole, int] = defaultdict(int)
        for role in cls.get_roles():
            counts[role] += 1
        return [(role, counts[role]) for role in counts]

    @classmethod
    def total_score_for_ranking(cls, ranking: Dict[PlayerRole, float]) -> float:
        score_list = [ranking[role] for role in cls.get_roles()]
        return round(sum(score_list), 2)

    @classmethod
    def weighted_score_for_ranking(cls, ranking: Dict[PlayerRole, float]) -> float:
        score_list = [Player.weighted_score_for_role(role, ranking[role]) for role in cls.get_roles()]
        return round(sum(score_list), 2)

    @classmethod
    def validate_team(cls, team: List[PlayerAssignment], allow_missing: bool = False) -> None:
        role_counts = {role: count for role, count in cls.role_counts()}

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
            allows_fill = cls.role_allows_fill(role)
            if (not allows_fill and diff != 0) or (allows_fill and diff > 0):
                err_str += f"Should have had {role_counts[role]} players {role.name} but got {team_counts[role]}!\n"
        if err_str:
            err_str += f"Team players: {[p.player.name for p in team]}"
            raise ValueError(err_str)

    @classmethod
    def remaining_roles_required(cls, players: List[PlayerAssignment]) -> List[PlayerRole]:
        missing_roles = []
        current_role_counts: Dict[PlayerRole, int] = defaultdict(int)
        expected_role_counts: Dict[PlayerRole, int] = {key: val for key, val in cls.role_counts()}
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

    @classmethod
    def is_num_assignments_valid(cls, role: PlayerRole, num_teams: int, num_assignments: int) -> bool:
        role_metadata = cls.get_role_metadata(role)
        # Two scenarios:
        # 1. The role requires an exact count, so the number of assignments must be equal to the number of teams.
        # 2. The role does not require an exact count, but if the role does not allow fills, then the number of
        #   assignments must be equal to the number of teams.
        # We do not consider the case where the number of assignments is greater than the number of teams.
        if role_metadata.requires_exact_count:
            return num_assignments == num_teams
        # Now the role does not require exact count, but cannot have fills.
        if not role_metadata.allows_fill:
            return num_assignments >= num_teams
        # If it does allow fills, then it can have any number.
        return True


class SpeedTeamComposition(TeamComposition):
    @classmethod
    def get_roles(cls) -> List[PlayerRole]:
        return [
            PlayerRole.QUEEN,
            PlayerRole.SPEED,
            PlayerRole.FLEX,
            PlayerRole.FLEX,
            PlayerRole.OBJECTIVE,
        ]


class ThreeFlexTeamComposition(TeamComposition):
    @classmethod
    def get_roles(cls) -> List[PlayerRole]:
        return [
            PlayerRole.QUEEN,
            PlayerRole.FLEX,
            PlayerRole.FLEX,
            PlayerRole.FLEX,
            PlayerRole.OBJECTIVE,
        ]


class Team:

    NUM_ROWS_SERIALIZED = 6
    """The number of CSV rows when the team is serialized.

    Presently, we have one row for the player names and one row for the scores.
    """

    def __init__(self, players: List[PlayerAssignment], team_composition: type[TeamComposition]) -> None:
        self.players = players

        self._team_composition = team_composition
        self._team_composition.validate_team(self.players, allow_missing=True)

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

    def queen_or_raise(self) -> PlayerAssignment:
        if self._queen is None:
            raise ValueError("No queen found for team!")
        return self._queen

    def speed_or_raise(self) -> PlayerAssignment:
        if self._speed is None:
            raise ValueError("No speed found for team!")
        return self._speed

    def objective_or_raise(self) -> PlayerAssignment:
        if self._objective is None:
            raise ValueError("No objective found for team!")
        return self._objective

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
        for role, count in self._team_composition.role_counts():
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
    def from_csv(cls, csv_data: list[list[str]], player_pool: PlayerNamePool[Player]) -> "Team":
        name_to_role = {}
        name_to_score = {}
        name_to_weighted_score = {}

        ordered_names = []
        for row in csv_data:
            team_row = _SerializedTeamRow(*row)
            # Assume that these rows contain the total scores
            if not team_row.role and not team_row.name:
                logging.info(f"Found row: {row} that does not represent player. Stopping deserialization.")
                break

            name_to_role[team_row.name] = PlayerRole[team_row.role]
            name_to_score[team_row.name] = float(team_row.score)
            name_to_weighted_score[team_row.name] = float(team_row.weighted_score)
            # Append the role to the ordered roles list, so we can also deserialize in order.
            ordered_names.append(team_row.name)

        team_players = []

        for player_name in ordered_names:
            # This should never raise an error if we are properly constructing the dicts.
            if player_name not in name_to_role:
                raise ValueError(f"Player role {player_name} not found in role list! Got: {list(name_to_role.keys())}.")
            player_role = name_to_role[player_name]
            player = player_pool.get_player(player_name)

            assignment = PlayerAssignment(player=player, assigned_role=player_role)
            if (
                assignment.score != name_to_score[player_name]
                or assignment.weighted_score != name_to_weighted_score[player_name]
            ):
                logging.warning(
                    f"Score mismatch for player {player_name}, expected {name_to_score[player_name]}, weighted "
                    f"{name_to_weighted_score[player_name]}, but got {assignment.score}. Was their score updated?"
                )
            team_players.append(assignment)
        return cls(team_players)


def write_teams_to_csv(output_file_name: str, teams: list[Team]) -> None:
    # Make the parent directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)

    with open(output_file_name, "w") as f:
        writer = csv.writer(f)
        for team in teams:
            writer.writerows(team.to_csv())
            writer.writerow([])


def read_teams_from_csv(csv_path: str, player_pool: PlayerNamePool[Player]) -> list[Team]:
    """Given a csv, load a list of teams."""
    teams = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        # Assume we go a certain number of rows at a time.
        serialized_team: list[list[str]] = []
        row_count = 0
        for row in reader:
            stripped_row = [elem for elem in row if elem]
            is_empty_row = len(row) == 0
            # If it's not an empty row, it must have been serialized, and we count this.
            # Some rows will be empty when stripped because they are a fill player and do not exist.
            if not is_empty_row:
                row_count += 1
            if stripped_row:
                serialized_team.append(row)
            if row_count == Team.NUM_ROWS_SERIALIZED:
                deserialized_team = Team.from_csv(serialized_team, player_pool)
                teams.append(deserialized_team)

                player_pool = player_pool.remove_subset_from([p.player for p in deserialized_team.players])
                serialized_team = []

                row_count = 0
    return teams


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
