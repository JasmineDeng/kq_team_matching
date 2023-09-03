import pytest

from src.data_types.player import Player, PlayerRole
from src.data_types.player_pool import PlayerPool
from src.data_types.tests.mock_data import get_fake_ranking


def fake_player(name: str) -> Player:
    return Player(name, primary_role=PlayerRole.FLEX, ranking=get_fake_ranking())


def test_convert_alias_to_name() -> None:
    aliases = [
        {"B", "BEE"},
    ]
    all_names = {"AB", "BEE", "C"}
    all_players = [fake_player(name) for name in all_names]
    player_pool = PlayerPool(all_players, aliases)

    assert player_pool._convert_alias_to_name("D") == "D"
    assert player_pool._convert_alias_to_name("B") == "BEE"
    assert player_pool._convert_alias_to_name("BEE") == "BEE"


def test_player_pool_name_get_contains() -> None:
    all_names = ["A", "B", "C", "D", "E"]
    all_players = [fake_player(name) for name in all_names]
    player_pool = PlayerPool(all_players, [{"B", "BEE"}, {"C", "SEE", "SEA"}])
    assert player_pool.get_player("BEE") == player_pool.get_player("B")
    assert player_pool.get_player("SEE") == player_pool.get_player("C")
    assert player_pool.get_player("SEA") == player_pool.get_player("C")

    # Test it works regardless of casing or whitespace
    assert player_pool.get_player("bEe") == player_pool.get_player("B")
    assert player_pool.get_player("  bEe  ") == player_pool.get_player("B")
    assert player_pool.get_player("a") == player_pool.get_player("A")

    # Test contains works also regardless of casing or whitespace
    assert player_pool.contains_player("bEe")
    assert player_pool.contains_player("B")
    assert player_pool.contains_player("  bEe  ")

    # Construct another player pool with a subset of all players
    player_pool_subset = PlayerPool(all_players[:3])
    assert player_pool.contains_pool(player_pool_subset)
    assert not player_pool_subset.contains_pool(player_pool)
    # Make another pool that is disjoint
    player_pool_disjoint = PlayerPool(all_players[:3] + [fake_player("F")])
    assert not player_pool.contains_pool(player_pool_disjoint)
    assert not player_pool_disjoint.contains_pool(player_pool)

    # Should raise since we have duplicate players
    with pytest.raises(ValueError):
        PlayerPool(all_players + [fake_player("A")])

    # Test removing a subset
    curr_pool = PlayerPool(all_players)
    new_pool = PlayerPool.remove_subset_from(curr_pool, all_players[:3])
    assert curr_pool.contains_pool(new_pool)
    assert new_pool.contains_player("D")
    assert new_pool.contains_player("E")
    assert new_pool.num_players == 2
