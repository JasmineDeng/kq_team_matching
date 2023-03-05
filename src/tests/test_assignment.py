from typing import Set

import pytest

from src.assignment import assign_players_to_teams
from src.data_types import Player, PlayerRole, Team


def _player_one_role(name: str, player_role: PlayerRole, ranking: int) -> Player:
    ranking_dict = {role: 1.0 for role in PlayerRole}
    ranking_dict[player_role] = ranking
    return Player(name=name, primary_role=player_role, ranking=ranking_dict)


def _team_to_player_names(team: Team) -> Set[str]:
    return {p.player.name for p in team.players}


def test_exclusion_assign_players_to_teams() -> None:
    all_players = {
        # Team 1
        _player_one_role("A", PlayerRole.QUEEN, 5),
        _player_one_role("B", PlayerRole.SPEED, 5),
        _player_one_role("C", PlayerRole.OBJECTIVE, 5),
        _player_one_role("D", PlayerRole.FLEX, 5),
        # Team 2
        _player_one_role("E", PlayerRole.QUEEN, 4),
        _player_one_role("F", PlayerRole.SPEED, 4),
        _player_one_role("G", PlayerRole.FLEX, 5),
        _player_one_role("H", PlayerRole.OBJECTIVE, 5),
    }
    teams = assign_players_to_teams(all_players, [])
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "F" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "B" in team_player_names

    teams = assign_players_to_teams(all_players, [{"A", "F"}])
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "B" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "F" in team_player_names


def test_allows_flex_fills() -> None:
    # In a sad day, we only have 6 people (2 queen, 2 speed, 2 obj), but theoretically we should still allow any
    # flex position to fill it.
    all_players = {
        # Team 1
        _player_one_role("A", PlayerRole.QUEEN, 10),
        _player_one_role("B", PlayerRole.SPEED, 10),
        _player_one_role("C", PlayerRole.OBJECTIVE, 10),
        _player_one_role("D", PlayerRole.FLEX, 10),
        # Team 2
        _player_one_role("E", PlayerRole.QUEEN, 8),
        _player_one_role("F", PlayerRole.OBJECTIVE, 8),
    }
    with pytest.raises(ValueError):
        assign_players_to_teams(all_players, [])

    all_players.add(
        _player_one_role("H", PlayerRole.SPEED, 8),
    )
    teams = assign_players_to_teams(all_players, [])
    assert len(teams) == 2
