import csv
from datetime import datetime
from typing import List

from src.data_types.exclusion import Exclusion
from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerNamePool
from src.data_types.team import TeamComposition


def _try_to_float(value: str, default_value: int = 1) -> float:
    """Try to convert the provided value to an integer, if it fails, return the default value."""
    try:
        return float(value)
    except Exception as e:
        print(f"Could not convert {value} to integer, because: {e}")
        return default_value


def load_data(csv_path: str) -> PlayerNamePool[Player]:
    column_name_to_role = {
        "queen rank": PlayerRole.QUEEN,
        "flex rank": PlayerRole.FLEX,
        "speed rank": PlayerRole.SPEED,
        "objective rank": PlayerRole.OBJECTIVE,
    }

    all_players = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ranking_dict = {role: row[key] for key, role in column_name_to_role.items()}

            # convert values to floats
            float_ranking_dict = {key: _try_to_float(value) for key, value in ranking_dict.items()}

            name = row["name"].strip()

            player = Player(
                name=name,
                ranking=float_ranking_dict,
            )
            all_players.append(player)

    return PlayerNamePool(all_players)


def _load_assigned_speed(csv_path: str, player_pool: PlayerNamePool[Player]) -> PlayerNamePool[Player]:
    """Read the speed-assigned roles from the scores csv.

    Currently assigned roles are split between the scores csv and attendance csv, so we need to read both.
    In the future, we should auto-assign speed positions.

    We *only* assign SPEED in the scores csv, so all other 'assigned' roles are ignored.
    """
    to_return = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            assigned_role = PlayerRole[row["Primary Role"].upper()]
            if assigned_role == PlayerRole.SPEED:
                to_return.append(player_pool.get_player(row["name"]))
    return PlayerNamePool(to_return)


def load_attendance(
    csv_path: str, player_pool: PlayerNamePool[Player], assign_speed: bool, scores_csv_path: str | None = None
) -> PlayerNamePool[PlayerAssignment]:
    """Given a csv, and all possible players with ranking data, return the players who are in attendance."""
    player_list = []
    assigned_speed = None
    if assign_speed and scores_csv_path:
        assigned_speed = _load_assigned_speed(scores_csv_path, player_pool)
    elif not assign_speed:
        print("Speed assignment is not enabled, so we will not load the scores csv.")

    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            name = row[0]

            is_queen = row[1]
            is_obj = row[2]

            # Get all players, checking if any of the nicknames have ranking data associated
            current_player = player_pool.get_player(name)
            # Set the role according to our hand selection
            if is_queen == "1" and is_obj == "1":
                raise ValueError(f"Player {current_player.name} cannot be both queen and obj, pick one")
            elif is_queen == "1":
                assigned_role = PlayerRole.QUEEN
            elif is_obj == "1":
                assigned_role = PlayerRole.OBJECTIVE
            elif assigned_speed is not None and assigned_speed.contains_name(name):
                assigned_role = PlayerRole.SPEED
            else:
                assigned_role = PlayerRole.FLEX

            player_list.append(current_player.to_assignment(assigned_role))
    return PlayerNamePool(player_list)


def _str_to_bool(value: str) -> bool:
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    raise ValueError(f"Could not convert {value} to boolean, must be one of 'TRUE' or 'FALSE'")


def load_exclusion_set(csv_path: str, player_pool: PlayerNamePool[Player]) -> list[Exclusion]:
    """Given a csv, load sets of people who should not play on the same team."""
    exclusion_set = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            if len(row) > 3 and row[3] and datetime.strptime(row[3], "%Y-%m-%d") <= datetime.now():
                continue

            requestor = player_pool.get_player(row[0])
            other_player = player_pool.get_player(row[1])

            only_if_they_queen = False
            if len(row) > 2:
                only_if_they_queen = _str_to_bool(row[2])

            exclusion_set.append(Exclusion(requestor, other_player, only_if_they_queen))

    return exclusion_set


def load_inclusion_set(
    csv_path: str, player_pool: PlayerNamePool[PlayerAssignment], team_composition: type[TeamComposition]
) -> List[List[PlayerAssignment]]:
    inclusion_set = []

    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            team = []
            for i, name in enumerate(row):
                if i == 0:
                    # The first entry is the team name, which we ignore
                    continue
                if not name:
                    continue
                if not player_pool.contains_name(name):
                    raise ValueError(
                        f"Player {name} in inclusion set, but not found in player pool - see tests/data/inclusion_set.csv for valid format."
                    )
                player = player_pool.get_player(name)
                team.append(player)
            if team:
                team_composition.validate_team(team, allow_missing=True)
                inclusion_set.append(team)
    return inclusion_set
