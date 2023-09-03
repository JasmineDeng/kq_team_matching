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
