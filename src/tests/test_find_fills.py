import pytest

from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.team import Team, TeamComposition
from src.find_fills import find_fills


def _player_for_role(name: str, role: PlayerRole, score: float = 5.0) -> PlayerAssignment:
    return Player(name=name, primary_role=role, ranking={r: score for r in PlayerRole}).to_primary_role_assignment()


def test_happy_find_fills() -> None:
    team = Team(players=[_player_for_role(str(i), role, 6 + i) for i, role in enumerate(TeamComposition.roles)])
    team_with_fill = Team(
        players=[
            _player_for_role("A", PlayerRole.QUEEN),
            _player_for_role("B", PlayerRole.FLEX),
            _player_for_role("C", PlayerRole.OBJECTIVE),
            _player_for_role("D", PlayerRole.FLEX),
        ],
    )
    all_players = team.players + team_with_fill.players
    with pytest.raises(ValueError):
        find_fills(team_with_fill, set(p.player for p in all_players), [team])
    # No fill needed
    assert find_fills(team, set(p.player for p in all_players), [team, team_with_fill]) == []

    team_with_fill = Team(
        players=[
            _player_for_role("A", PlayerRole.QUEEN, score=10.0),
            _player_for_role("B", PlayerRole.FLEX),
            _player_for_role("C", PlayerRole.OBJECTIVE),
            _player_for_role("D", PlayerRole.SPEED),
        ]
    )
    all_players = team.players + team_with_fill.players
    fills = find_fills(team_with_fill, set(p.player for p in all_players), [team])
    assert fills[0].player.name == "4"
