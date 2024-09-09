from typing import Set

import pytest

from src.assignment import _contains_exclusion_set, _validate_required_roles, assign_players_to_teams
from src.data_types.exclusion import Exclusion
from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerNamePool
from src.data_types.team import Team
from src.exceptions import WrongNumberOfPlayersException, assignment_to_names


def _player_one_role(name: str, player_role: PlayerRole, ranking: int) -> PlayerAssignment:
    ranking_dict = {role: 1.0 for role in PlayerRole}
    ranking_dict[player_role] = ranking
    return Player(name=name, ranking=ranking_dict).to_assignment(player_role)


def _team_to_player_names(team: Team) -> Set[str]:
    return {p.player.name for p in team.players}


def _name_list_to_exclusions(names: list[list[str]], all_assignments: list[Player]) -> list[Exclusion]:
    result = []

    for name_list in names:
        players = [p for p in all_assignments if p.name in name_list]
        result.append(Exclusion(players[0], players[1], False))

    return result


def _make_full_team(names: list[str]) -> Team:
    assert len(names) == 5, "Only full teams are supported"
    return Team(
        players=[
            _player_one_role(names[0], PlayerRole.QUEEN, 1),
            _player_one_role(names[1], PlayerRole.SPEED, 1),
            _player_one_role(names[2], PlayerRole.OBJECTIVE, 1),
            _player_one_role(names[3], PlayerRole.FLEX, 1),
            _player_one_role(names[4], PlayerRole.FLEX, 1),
        ],
    )


def test_contains_exclusion_set() -> None:
    assignments = [
        _player_one_role("A", PlayerRole.QUEEN, 5),
        _player_one_role("B", PlayerRole.SPEED, 5),
        _player_one_role("C", PlayerRole.OBJECTIVE, 5),
    ]
    all_assignments = assignments + [_player_one_role("D", PlayerRole.FLEX, 5)]
    all_players = [a.player for a in all_assignments]
    player_pool = PlayerNamePool(assignments)

    exclusion_players = _contains_exclusion_set(player_pool, _name_list_to_exclusions([["A", "B"]], all_players))
    assert exclusion_players is not None
    assert {p.name for p in exclusion_players.players} == {"A", "B"}
    assert _contains_exclusion_set(player_pool, _name_list_to_exclusions([["C", "D"]], all_players)) is None
    exclusion_players = _contains_exclusion_set(
        player_pool, _name_list_to_exclusions([["A", "B"], ["A", "C"]], all_players)
    )
    assert exclusion_players is not None
    assert {p.name for p in exclusion_players.players} == {"A", "B"}


def test_happy_assignment() -> None:
    all_players = [
        # Team 1
        _player_one_role("A", PlayerRole.QUEEN, 5),
        _player_one_role("B", PlayerRole.SPEED, 5),
        _player_one_role("C", PlayerRole.OBJECTIVE, 5),
        _player_one_role("D", PlayerRole.FLEX, 5),
        _player_one_role("E", PlayerRole.FLEX, 5),
    ]
    teams = assign_players_to_teams(PlayerNamePool(all_players), [], [])
    assert len(teams) == 1
    assert set({p.player.name for p in teams[0].players}) == {"A", "B", "C", "D", "E"}


def test_exclusion_set() -> None:
    all_players = [
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
    ]
    teams = assign_players_to_teams(PlayerNamePool(all_players), [], [])
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "F" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "B" in team_player_names

    teams = assign_players_to_teams(
        PlayerNamePool(all_players), [], [Exclusion(all_players[0].player, all_players[5].player, False)]
    )
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "B" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "F" in team_player_names


def test_exclusion_set_queen_only() -> None:
    all_players = [
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
    ]
    # NOTE: null case is missing because original non-exclusion UT covers it

    # A and F should play together as A doesn't want F to queen, but F doesn't care
    teams = assign_players_to_teams(
        PlayerNamePool(all_players), [], [Exclusion(all_players[0].player, all_players[5].player, True)]
    )
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "F" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "B" in team_player_names

    # F doesn't want A to queen
    teams = assign_players_to_teams(
        PlayerNamePool(all_players), [], [Exclusion(all_players[5].player, all_players[0].player, False)]
    )
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
    all_players = [
        # Team 1
        _player_one_role("A", PlayerRole.QUEEN, 10),
        _player_one_role("B", PlayerRole.SPEED, 10),
        _player_one_role("C", PlayerRole.OBJECTIVE, 10),
        _player_one_role("D", PlayerRole.FLEX, 10),
        # Team 2
        _player_one_role("E", PlayerRole.QUEEN, 8),
        _player_one_role("F", PlayerRole.OBJECTIVE, 8),
        _player_one_role("G", PlayerRole.FLEX, 10),
    ]
    with pytest.raises(WrongNumberOfPlayersException):
        assign_players_to_teams(PlayerNamePool(all_players), [], [])

    all_players.append(
        _player_one_role("H", PlayerRole.SPEED, 8),
    )
    teams = assign_players_to_teams(PlayerNamePool(all_players), [], [])
    assert len(teams) == 2


def test_inclusion_set() -> None:
    b_player = _player_one_role("B", PlayerRole.FLEX, 10)
    c_player = _player_one_role("C", PlayerRole.OBJECTIVE, 10)
    all_players = [
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
    ]
    player_pool = PlayerNamePool(all_players)
    # Not enough objective/speed players
    inclusion_set = [[b_player, c_player.player.to_assignment(PlayerRole.FLEX)]]
    with pytest.raises(WrongNumberOfPlayersException):
        assign_players_to_teams(player_pool, inclusion_set, [])
    # Too many objective players should raise an error
    inclusion_set = [[b_player.player.to_assignment(PlayerRole.OBJECTIVE), c_player]]
    with pytest.raises(WrongNumberOfPlayersException):
        assign_players_to_teams(player_pool, inclusion_set, [])
    # Too many speed players should NOT raise an error
    inclusion_set = [[b_player.player.to_assignment(PlayerRole.SPEED), c_player]]
    assignment = assign_players_to_teams(player_pool, inclusion_set, [])
    # The assignment should not be None, but we assert to indicate assignment should succeed
    assert assignment is not None

    inclusion_set = [[b_player, c_player]]
    teams = assign_players_to_teams(player_pool, [], [], use_uniform_sampling=True)
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "C" in team_player_names and "B" not in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "C" not in team_player_names and "B" in team_player_names

    # Disable random sampling so it is deterministic
    teams = assign_players_to_teams(player_pool, inclusion_set, [], use_uniform_sampling=True)
    teams.sort(key=lambda team: team.team_name)
    # should be on the second team since the second team has the weaker queen
    team_player_names = _team_to_player_names(teams[1])
    assert "C" in team_player_names and "B" in team_player_names


def test_validate_required_roles() -> None:
    team1 = _make_full_team(["A", "B", "C", "D", "E"])
    team2 = _make_full_team(["F", "G", "H", "I", "J"])
    team3 = _make_full_team(["K", "L", "M", "N", "O"])

    total_team_num = 3

    all_assignments = team1.players + team2.players + team3.players
    player_pool_assignments = PlayerNamePool(all_assignments)

    # This should succeed without any includion set.
    _validate_required_roles(total_team_num, player_pool_assignments, [])

    # This should succeed because the overall counts are correct
    _validate_required_roles(
        total_team_num,
        player_pool_assignments,
        [
            [team1.queen_or_raise(), team2.speed_or_raise()],
            [team2.queen_or_raise(), team3.objective_or_raise()],
        ],
    )

    # This will not pass because now we are missing obj.
    team2_obj = team2.objective_or_raise().player
    try:
        _validate_required_roles(
            total_team_num,
            player_pool_assignments,
            [
                [team1.queen_or_raise(), PlayerAssignment(team2_obj, PlayerRole.SPEED)],
            ],
        )
    except WrongNumberOfPlayersException as e:
        # Obj will error instead of speed because we allow extra speed roles.
        # We do not have enough obj players because team2_obj is in the inclusion set.
        assert e.expected_number == total_team_num
        assert e.role == PlayerRole.OBJECTIVE
        assert set(assignment_to_names(e.players)) == set(
            assignment_to_names([team1.objective_or_raise(), team3.objective_or_raise()])
        )
        assert e.players_in_inclusion == []

    # If we just remove queens from the player list, we will get an error.
    try:
        _validate_required_roles(
            total_team_num, PlayerNamePool([p for p in all_assignments if p.assigned_role != PlayerRole.QUEEN]), []
        )
    except WrongNumberOfPlayersException as e:
        assert e.expected_number == total_team_num
        assert e.role == PlayerRole.QUEEN
        assert e.players == []
        assert e.players_in_inclusion == []

    # Too many queens will also cause an error, but not if one is overridden to another role.
    team1_queen = team1.queen_or_raise().player
    _validate_required_roles(
        total_team_num,
        PlayerNamePool(all_assignments + [_player_one_role("foo", PlayerRole.QUEEN, 10)]),
        [[PlayerAssignment(team1_queen, PlayerRole.OBJECTIVE), PlayerAssignment(team2_obj, PlayerRole.FLEX)]],
    )

    # Adding an extra queen finally will just cause an error.
    extra_queen = _player_one_role("foo", PlayerRole.QUEEN, 10)
    team1_queen = team1.queen_or_raise().player
    team1_speed = team1.speed_or_raise().player
    try:
        _validate_required_roles(
            total_team_num,
            PlayerNamePool(all_assignments + [extra_queen]),
            # Inclusion shouldn't matter here. The overall counts are thes ame since we effectively
            # swapped queen and speed roles for two players.
            [
                [extra_queen, team1.objective_or_raise()],
                [PlayerAssignment(team1_queen, PlayerRole.SPEED), PlayerAssignment(team1_speed, PlayerRole.QUEEN)],
            ],
        )
    except WrongNumberOfPlayersException as e:
        assert e.expected_number == total_team_num
        assert e.role == PlayerRole.QUEEN
        assert set(assignment_to_names(e.players)) == set(
            assignment_to_names([team1.speed_or_raise(), team2.queen_or_raise(), team3.queen_or_raise(), extra_queen])
        )
        assert set(assignment_to_names(e.players_in_inclusion)) == {"foo", team1_speed.name}
