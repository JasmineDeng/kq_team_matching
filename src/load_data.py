import csv
from typing import Dict, List, Optional, Set

from src.data_types import Player, PlayerRole

NAME_ALIASES: List[Set[str]] = [
    {"Matt", "Matthew", "Matt Wu"},
    {"Chris", "Blue Chris"},
    {"Maureen", "Mo"},
    {"Blee", "Brian Lee"},
    {"BrianM", "Brian M"},
]
"""A list of aliases that people can be called by.

The actual name comparison is case- and whitespace-insensitive. I.e., 'Matt ', 'mAtt', and ' MATT ' are treated as the
same name.
"""


def convert_alias_to_name(all_names: Set[str], name: str, all_aliases: Optional[List[Set[str]]] = None) -> str:
    """Given a set of all player names, check if the name is an alias and, if so, convert to the name in the set.

    This ensures that we refer to someone by only one name throughout the assignment, excluding nicknames.
    """
    # Mapping from the name we do comparison with to the name we should return
    lowercase_all_names: Dict[str, str] = {name.lower().strip(): name for name in all_names}

    alias_list = [name]
    all_aliases_list = all_aliases or NAME_ALIASES
    for elem in all_aliases_list:
        if name in elem:
            alias_list = elem
            break

    for alias in alias_list:
        # make sure the comparison is whitespace- and case-insensitive
        alias_to_compare = alias.lower().strip()
        if alias_to_compare in lowercase_all_names:
            return lowercase_all_names[alias_to_compare]
    return name


def _try_to_float(value: str, default_value: int = 1) -> float:
    """Try to convert the provided value to an integer, if it fails, return the default value."""
    try:
        return float(value)
    except Exception as e:
        print(f"Could not convert {value} to integer, because: {e}")
        return default_value


def load_data(csv_path: str) -> Dict[str, Player]:
    column_name_to_role = {
        "queen rank": PlayerRole.QUEEN,
        "flex rank": PlayerRole.FLEX,
        "speed rank": PlayerRole.SPEED,
        "objective rank": PlayerRole.OBJECTIVE,
    }

    all_names = []

    to_return = {}
    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create rankings
            primary_role = PlayerRole[row["Primary Role"].upper()]

            ranking_dict = {role: row[key] for key, role in column_name_to_role.items()}
            # convert values to floats
            ranking_dict = {key: _try_to_float(value) for key, value in ranking_dict.items()}

            name = row["Name"]
            to_return[name.lower().strip()] = Player(
                name=name,
                primary_role=primary_role,
                ranking=ranking_dict,
            )
            all_names.append(name)

    if len(all_names) != len(to_return):
        raise ValueError(f"Got a duplicate player somewhere. Had {len(to_return)} players but {len(all_names)}")
    return to_return


def load_attendance(csv_path: str, player_info: Dict[str, Player]) -> Set[Player]:
    players = set()

    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            name = row[0]

            is_queen = row[1]
            is_obj = row[2]

            # Get all players, checking if any of the nicknames have ranking data associated
            player_name = convert_alias_to_name(set(player_info.keys()), name)
            current_player = player_info.get(player_name, None)
            if current_player is None:
                raise ValueError(
                    f"Could not find ranking data for player with name: '{name}', possible aliases: {NAME_ALIASES}, "
                    f"all possible players: {list(player_info.keys())}"
                )
            # Set the role according to our hand selection
            if is_queen == "1" and is_obj == "1":
                raise ValueError("Cannot be both queen and obj, pick one")
            elif is_queen == "1":
                current_player.primary_role = PlayerRole.QUEEN
            elif is_obj == "1":
                current_player.primary_role = PlayerRole.OBJECTIVE
            elif current_player.primary_role == PlayerRole.QUEEN or current_player.primary_role == PlayerRole.OBJECTIVE:
                current_player.primary_role = PlayerRole.FLEX

            players.add(current_player)
    return players


def load_exclusion_set(csv_path: str, all_names: Set[str]) -> List[Set[str]]:
    """Given a csv, load sets of people who should not play on the same team."""
    exclusion_set = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            name1 = convert_alias_to_name(all_names, row[0])
            name2 = convert_alias_to_name(all_names, row[1])
            exclusion_set.append({name1, name2})

    return exclusion_set


if __name__ == "__main__":
    print(load_data("data/test_data.csv"))
