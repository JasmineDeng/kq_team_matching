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


def load_data(csv_path: str) -> PlayerNamePool[PlayerAssignment]:
    column_name_to_role = {
        "queen rank": PlayerRole.QUEEN,
        "flex rank": PlayerRole.FLEX,
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
            # By default, assume all players are FLEX.
            all_players.append(player.to_assignment(PlayerRole.FLEX))

    return PlayerNamePool(all_players)


def load_attendance(csv_path: str, player_pool: PlayerNamePool[Player]) -> PlayerNamePool[PlayerAssignment]:
    """Given a csv, and all possible players with ranking data, return the players who are in attendance."""
    player_list = []

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
            if len(row) > 3 and row[3] and datetime.strptime(row[3], "%Y-%m-%d") >= datetime.now():
                continue

            requestor = player_pool.get_player(row[0])
            other_player = player_pool.get_player(row[1])

            only_if_they_queen = False
            if len(row) > 2:
                only_if_they_queen = _str_to_bool(row[2])

            exclusion_set.append(Exclusion(requestor, other_player, only_if_they_queen))

    return exclusion_set


def load_inclusion_set(csv_path: str, player_pool: PlayerNamePool[Player]) -> List[List[PlayerAssignment]]:
    inclusion_set = []

    role_to_csv_title = {
        PlayerRole.QUEEN: "Queen",
        PlayerRole.OBJECTIVE: "Objective",
        PlayerRole.FLEX: "Flex",
    }
    role_to_ind = {}
    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        field_names = next(reader)
        for role, title in role_to_csv_title.items():
            role_to_ind[role] = [i for i, name in enumerate(field_names) if name == title]
        for row in reader:
            team = []
            for role, ind_list in role_to_ind.items():
                for ind in ind_list:
                    name = row[ind]
                    if not name:
                        continue
                    player = player_pool.get_player(name)
                    team.append(PlayerAssignment(player, assigned_role=role))
            if team:
                TeamComposition.validate_team(team, allow_missing=True)
                inclusion_set.append(team)
    return inclusion_set
