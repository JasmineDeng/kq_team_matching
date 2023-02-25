import csv
from typing import Dict, List, Set

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


def _get_aliases_for_name(name: str) -> Set[str]:
    for aliases in NAME_ALIASES:
        if name in aliases:
            return aliases
    return {name}


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
            aliases = _get_aliases_for_name(name)
            current_player = None
            for alias in aliases:
                if alias.lower().strip() in player_info:
                    current_player = player_info[alias.lower().strip()]
                    break
            if current_player is None:
                raise ValueError(
                    f"Could not find ranking data for player with name: '{name}', had aliases: {aliases}, all possible players: {list(player_info.keys())}"
                )
            player = Player(name=name, ranking=current_player)
            players.add(player)
    return players


if __name__ == "__main__":
    print(load_data("data/test_data.csv"))
