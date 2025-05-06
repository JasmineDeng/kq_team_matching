import os

from src.data_types.player import Player
from src.data_types.player_pool import PlayerNamePool
from src.main import load_exclusion_set

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_load_exclusion_set_date_exclusion() -> None:
    # This test will fail starting in 10 years.  Sorry not sorry
    playerPool = PlayerNamePool(
        [
            Player(name="A", ranking={}),
            Player(name="G", ranking={}),
            Player(name="F", ranking={}),
            Player(name="ABC", ranking={}),
            Player(name="DEF", ranking={}),
            Player(name="GHI", ranking={}),
            Player(name="JKL", ranking={}),
        ]
    )
    exclusionSets = load_exclusion_set(os.path.join(TEST_DATA_DIR, "exclusion_set.csv"), playerPool)

    assert len(exclusionSets) == 3

    assert exclusionSets[2].requester.name == "ABC"
    assert exclusionSets[2].other_player.name == "DEF"
