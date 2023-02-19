import csv
from typing import Dict, Optional, Set

from data_types import Player, PlayerRanking, PlayerRole


def _try_to_int(value: str, default_value: int = 1) -> Optional[int]:
    """Try to convert the provided value to an integer, if it fails, return the default value."""
    try:
        return int(value)
    except Exception:
        print(f"Could not convert {value} to integer")
        return default_value


def _load_all_rankings(data: Dict[str, str]) -> Dict[str, int]:
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
        raise ValueError(
            f"Got a duplicate player somewhere. Had {len(to_return)} players but {len(all_names)}"
        )
    return to_return


def load_attendance(
    csv_path: str, player_info: Dict[str, PlayerRanking]
) -> Set[Player]:
    players = set()

    with open(csv_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip the header
        for row in reader:
            name = row[1]
            player = Player(name=name, ranking=player_info[name.lower().strip()])
            players.add(player)
    return players


if __name__ == "__main__":
    print(load_data("data/test_data.csv"))
