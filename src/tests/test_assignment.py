from typing import Set

import pytest

from src.assignment import _contains_exclusion_set, assign_players_to_teams
from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.team import Team


def _player_one_role(name: str, player_role: PlayerRole, ranking: int) -> Player:
    ranking_dict = {role: 1.0 for role in PlayerRole}
    ranking_dict[player_role] = ranking
    return Player(name=name, primary_role=player_role, ranking=ranking_dict)


def _team_to_player_names(team: Team) -> Set[str]:
    return {p.player.name for p in team.players}


def test_contains_exclusion_set() -> None:
    players = [
        _player_one_role("A", PlayerRole.QUEEN, 5),
        _player_one_role("B", PlayerRole.SPEED, 5),
        _player_one_role("C", PlayerRole.OBJECTIVE, 5),
    ]
    assert _contains_exclusion_set(set(players), [{"A", "B"}]) == {"A", "B"}
    assert _contains_exclusion_set(set(players), [{"C", "D"}]) is None
    assert _contains_exclusion_set(set(players), [{"A", "B"}, {"A", "C"}]) == {"A", "B"}


def test_happy_assignment() -> None:
    all_players = {
        # Team 1
        _player_one_role("A", PlayerRole.QUEEN, 5),
        _player_one_role("B", PlayerRole.SPEED, 5),
        _player_one_role("C", PlayerRole.OBJECTIVE, 5),
        _player_one_role("D", PlayerRole.FLEX, 5),
        _player_one_role("E", PlayerRole.FLEX, 5),
    }
    teams = assign_players_to_teams(all_players, [], [])
    assert len(teams) == 1
    assert set({p.player.name for p in teams[0].players}) == {"A", "B", "C", "D", "E"}


def test_exclusion_set() -> None:
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
    teams = assign_players_to_teams(all_players, [], [])
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "F" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "B" in team_player_names

    teams = assign_players_to_teams(all_players, [], [{"A", "F"}])
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
        assign_players_to_teams(all_players, [], [])

    all_players.add(
        _player_one_role("H", PlayerRole.SPEED, 8),
    )
    teams = assign_players_to_teams(all_players, [], [])
    assert len(teams) == 2


def test_inclusion_set() -> None:
    b_player = _player_one_role("B", PlayerRole.FLEX, 10)
    c_player = _player_one_role("C", PlayerRole.OBJECTIVE, 10)
    all_players = {
        # Team 1
        _player_one_role("A", PlayerRole.QUEEN, 5),
        _player_one_role("I", PlayerRole.SPEED, 5),
        b_player,
        c_player,
        _player_one_role("D", PlayerRole.FLEX, 5),
        # Team 2
        _player_one_role("E", PlayerRole.QUEEN, 4),
        _player_one_role("F", PlayerRole.SPEED, 4),
        _player_one_role("G", PlayerRole.FLEX, 5),
        _player_one_role("H", PlayerRole.OBJECTIVE, 5),
    }
    # Not enough objective/speed players
    inclusion_set = [[PlayerAssignment(b_player, PlayerRole.FLEX), PlayerAssignment(c_player, PlayerRole.FLEX)]]
    with pytest.raises(ValueError):
        assign_players_to_teams(all_players, inclusion_set, [])
    # Too many objective players should raise an error
    inclusion_set = [
        [PlayerAssignment(b_player, PlayerRole.OBJECTIVE), PlayerAssignment(c_player, PlayerRole.OBJECTIVE)]
    ]
    with pytest.raises(ValueError):
        assign_players_to_teams(all_players, inclusion_set, [])
    # Too many speed players should NOT raise an error
    inclusion_set = [[PlayerAssignment(b_player, PlayerRole.SPEED), PlayerAssignment(c_player, PlayerRole.OBJECTIVE)]]
    assignment = assign_players_to_teams(all_players, inclusion_set, [])
    # The assignment should not be None, but we assert to indicate assignment should succeed
    assert assignment is not None

    inclusion_set = [[PlayerAssignment(b_player, PlayerRole.FLEX), PlayerAssignment(c_player, PlayerRole.OBJECTIVE)]]
    teams = assign_players_to_teams(all_players, [], [], use_uniform_sampling=True)
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "C" in team_player_names and "B" not in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "C" not in team_player_names and "B" in team_player_names

    # Disable random sampling so it is deterministic
    teams = assign_players_to_teams(all_players, inclusion_set, [], use_uniform_sampling=True)
    teams.sort(key=lambda team: team.team_name)
    # should be on the second team since the second team has the weaker queen
    team_player_names = _team_to_player_names(teams[1])
    assert "C" in team_player_names and "B" in team_player_names
