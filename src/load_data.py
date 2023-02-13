from typing import Set
import csv
from data_types import Player, PlayerRanking, PlayerRole


def load_data(csv_path: str) -> Set[Player]:
    players = set()
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create rankings for the primary and secondary roles
            primary_role = PlayerRole[row["Primary Role"].upper()]
            secondary_role = PlayerRole[row["Secondary Role"].upper()]
            primary_rank = int(row["primary rank"])
            secondary_rank = int(row["secondary rank"])

            ranking = PlayerRanking(primary_role=primary_role, primary_ranking=primary_rank, secondary_role=secondary_role, secondary_ranking=secondary_rank)
            player = Player(name=row["Name"], ranking=ranking)
            players.add(player)
    return players


if __name__ == "__main__":
    print(load_data("data/test_data.csv"))
