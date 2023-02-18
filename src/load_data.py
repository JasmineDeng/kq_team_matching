import csv
from typing import Dict, Set

from data_types import Player, PlayerRanking, PlayerRole


def load_data(csv_path: str) -> Dict[str, PlayerRanking]:
    players = set()
    all_names = set()

    to_return = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create rankings for the primary and secondary roles
            primary_role = PlayerRole[row["Primary Role"].upper()]
            secondary_role = PlayerRole[row["Secondary Role"].upper()]
            primary_rank = int(row["primary rank"])
            secondary_rank = int(row["secondary rank"])

            name = row["Name"]

            # ranking = {role: row[key] for role, key in [(PlayerRole.QUEEN, "queen rank"), (PlayerRole.VANILLA, "vanilla rank"), (PlayerRole.SPEED, "speed rank"), (PlayerRole.OBJECTIVE, "objective rank")]}
            # convert the str to int
            # ranking = {key: _try_to_int(val) for key, val in ranking.items()}
            to_return[name.lower().strip()] = PlayerRanking(primary_role=primary_role, primary_ranking=primary_rank,secondary_ranking=secondary_rank, secondary_role=secondary_role)
            all_names.add(name)

    # if len(all_names) != len(players):
    #     raise ValueError(f"Got a duplicate player somewhere. Had {len(to_return)} players but {len(all_names)}")
    return to_return


def load_attendance(csv_path: str, player_info: Dict[str, PlayerRanking]) -> Set[Player]:
    players = set()

    attendance_to_role_enum = {"Vanilla Warrior": PlayerRole.VANILLA, "Objective": PlayerRole.OBJECTIVE, "Speed Warrior": PlayerRole.SPEED, "Queen": PlayerRole.QUEEN}

    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # skip the header
        for row in reader:
            name, primary_role, secondary_role = row[1], row[2], row[3]
            primary_role_enum = attendance_to_role_enum[primary_role]
            secondary_role_enum = attendance_to_role_enum[secondary_role]

            player_ranking = player_info[name.lower().strip()]
            player = Player(name=name, ranking=player_info[name.lower().strip()])
            players.add(player)
    return players


if __name__ == "__main__":
    print(load_data("data/test_data.csv"))
