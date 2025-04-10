import pytest

from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.team import SpeedTeamComposition, Team, TeamComposition, ThreeFlexTeamComposition
from src.find_fills import find_fills


def _player_for_role(name: str, role: PlayerRole, score: float = 5.0) -> PlayerAssignment:
    return Player(name=name, ranking={r: score for r in PlayerRole}).to_assignment(role)


def get_team_no_fills(team_composition: type[TeamComposition]) -> Team:
    team = Team(
        players=[_player_for_role(str(i), role, 6 + i) for i, role in enumerate(team_composition.get_roles())],
        team_composition=team_composition,
    )
    return team


def test_find_speed_team_fills() -> None:
    team_composition = SpeedTeamComposition

    team = get_team_no_fills(team_composition)
    team_with_fill = Team(
        players=[
            _player_for_role("A", PlayerRole.QUEEN),
            _player_for_role("B", PlayerRole.FLEX),
            _player_for_role("C", PlayerRole.OBJECTIVE),
            _player_for_role("D", PlayerRole.FLEX),
        ],
        team_composition=team_composition,
    )
    all_players = team.players + team_with_fill.players
    # Cannot find a fill for speed
    with pytest.raises(ValueError):
        find_fills(team_with_fill, all_players, [team], team_composition=team_composition)
    # No fill needed
    assert find_fills(team, all_players, [team, team_with_fill], team_composition=team_composition) == []

    team_with_fill = Team(
        players=[
            _player_for_role("A", PlayerRole.QUEEN, score=10.0),
            _player_for_role("B", PlayerRole.FLEX),
            _player_for_role("C", PlayerRole.OBJECTIVE),
            _player_for_role("D", PlayerRole.SPEED),
        ],
        team_composition=team_composition,
    )
    all_players = team.players + team_with_fill.players
    fills = find_fills(team_with_fill, all_players, [team], team_composition=team_composition)
    assert fills[0].player.name == "4"


def test_find_flex_team_fills() -> None:
    team = get_team_no_fills(ThreeFlexTeamComposition)
    team_with_fill = Team(
        players=[
            _player_for_role("A", PlayerRole.QUEEN),
            _player_for_role("B", PlayerRole.FLEX),
            _player_for_role("C", PlayerRole.OBJECTIVE),
            _player_for_role("D", PlayerRole.FLEX),
        ],
        team_composition=ThreeFlexTeamComposition,
    )
    all_players = team.players + team_with_fill.players
    assert find_fills(team, all_players, [team_with_fill], team_composition=ThreeFlexTeamComposition) == []
    fills = find_fills(team_with_fill, all_players, [team], team_composition=ThreeFlexTeamComposition)
    assert fills[0].player.name == "4"
