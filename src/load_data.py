import csv
from typing import Dict, List, Optional, Set

from src.data_types import Player, PlayerRanking, PlayerRole

NAME_ALIASES: List[Set[str]] = [
    {"Matt", "Matthew", "Matt Wu"},
    {"Chris", "Blue Chris"},
    {"Maureen", "Mo"},
    {"Blee", "Brian Lee"},
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


def _try_to_int(value: str, default_value: int = 1) -> int:
    """Try to convert the provided value to an integer, if it fails, return the default value."""
    try:
        return int(value)
    except Exception as e:
        print(f"Could not convert {value} to integer, because: {e}")
        return default_value


def _load_all_rankings(data: Dict[str, str]) -> Dict[PlayerRole, int]:
    """Load all rankings for all roles given a dictionary representing a CSV row.

    This function is currently not used.
    """
    ranking = {
        role: data[key]
        for role, key in [
            (PlayerRole.QUEEN, "queen rank"),
            (PlayerRole.VANILLA, "vanilla rank"),
            (PlayerRole.SPEED, "speed rank"),
            (PlayerRole.OBJECTIVE, "objective rank"),
        ]
    }
    # convert the str to int
    integer_ranking = {key: _try_to_int(val) for key, val in ranking.items()}
    return integer_ranking


def load_data(csv_path: str) -> Dict[str, PlayerRanking]:
    all_names = []

    to_return = {}
    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create rankings for the primary and secondary roles
            primary_role = PlayerRole[row["Primary Role"].upper()]
            secondary_role = PlayerRole[row["Secondary Role"].upper()]
            primary_rank = int(row["primary rank"])
            secondary_rank = int(row["secondary rank"])

            name = row["Name"]
            to_return[name.lower().strip()] = PlayerRanking(
                primary_role=primary_role,
                primary_ranking=primary_rank,
                secondary_ranking=secondary_rank,
                secondary_role=secondary_role,
            )
            all_names.append(name)

    if len(all_names) != len(to_return):
        raise ValueError(f"Got a duplicate player somewhere. Had {len(to_return)} players but {len(all_names)}")
    return to_return


def load_attendance(csv_path: str, player_info: Dict[str, PlayerRanking]) -> Set[Player]:
    players = set()

    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            name = row[1]

            # Get all players, checking if any of the nicknames have ranking data associated
            player_name = convert_alias_to_name(set(player_info.keys()), name)
            current_player = player_info.get(player_name, None)
            if current_player is None:
                raise ValueError(
                    f"Could not find ranking data for player with name: '{name}', possible aliases: {NAME_ALIASES}, "
                    f"all possible players: {list(player_info.keys())}"
                )
            player = Player(name=name, ranking=current_player)
            players.add(player)
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
