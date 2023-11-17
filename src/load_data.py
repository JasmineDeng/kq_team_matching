import csv
from typing import List

from src.data_types.exclusion import Exclusion
from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerPool
from src.data_types.team import TeamComposition
from datetime import datetime


def _try_to_float(value: str, default_value: int = 1) -> float:
    """Try to convert the provided value to an integer, if it fails, return the default value."""
    try:
        return float(value)
    except Exception as e:
        print(f"Could not convert {value} to integer, because: {e}")
        return default_value


def load_data(csv_path: str) -> PlayerPool:
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
            # Create rankings
            primary_role = PlayerRole[row["Primary Role"].upper()]

            ranking_dict = {role: row[key] for key, role in column_name_to_role.items()}
            # convert values to floats
            float_ranking_dict = {key: _try_to_float(value) for key, value in ranking_dict.items()}

            name = row["name"].strip()

            player = Player(
                name=name,
                primary_role=primary_role,
                ranking=float_ranking_dict,
            )
            all_players.append(player)

    return PlayerPool(all_players)


def load_attendance(csv_path: str, player_pool: PlayerPool) -> PlayerPool:
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
                current_player.primary_role = PlayerRole.QUEEN
            elif is_obj == "1":
                current_player.primary_role = PlayerRole.OBJECTIVE
            elif current_player.primary_role == PlayerRole.QUEEN or current_player.primary_role == PlayerRole.OBJECTIVE:
                print(
                    f"Player {current_player.name} had role {current_player.primary_role} but those must be "
                    f"hand-selected. Setting player to FLEX."
                )
                current_player.primary_role = PlayerRole.FLEX

            player_list.append(current_player)
    return PlayerPool(player_list)


def load_exclusion_set(csv_path: str, player_pool: PlayerPool) -> list[Exclusion]:
    """Given a csv, load sets of people who should not play on the same team."""
    exclusion_set = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            if len(row) > 3 and datetime.strptime(row[3], "%Y-%m-%d") >= datetime.now():
                continue

            requestor = player_pool.get_player(row[0])
            other_player = player_pool.get_player(row[1])

            only_if_they_queen = False
            if len(row) > 2:
                only_if_they_queen = bool(row[2])

            exclusion_set.append(Exclusion(requestor, other_player, only_if_they_queen))

    return exclusion_set


def load_inclusion_set(csv_path: str, player_pool: PlayerPool) -> List[List[PlayerAssignment]]:
    inclusion_set = []

    role_to_csv_title = {
        PlayerRole.QUEEN: "Queen",
        PlayerRole.SPEED: "Speed Warrior",
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
                    if role != player.primary_role:
                        print(
                            f"Player {player.name} had primary role {player.primary_role.name} but because of "
                            f"inclusion set, role is now: {role.name}"
                        )
                    team.append(PlayerAssignment(player, assigned_role=role))
            if team:
                TeamComposition.validate_team(team, allow_missing=True)
                inclusion_set.append(team)
    return inclusion_set
