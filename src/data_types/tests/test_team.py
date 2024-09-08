from collections import defaultdict
from typing import Dict

import py
import pytest

from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerNamePool
from src.data_types.team import Team, TeamComposition, read_teams_from_csv, write_teams_to_csv
from src.data_types.tests.mock_data import get_fake_ranking, get_player_assignments


def _assert_teams_equal(expected_team: Team, team: Team) -> None:
    players = sorted(team.players, key=lambda p: p.player.name)
    expected_players = sorted(expected_team.players, key=lambda p: p.player.name)
    for assignment, expected_assignment in zip(players, expected_players):
        assert assignment.assigned_role == expected_assignment.assigned_role
        assert assignment.player.name == expected_assignment.player.name
        assert assignment.player.ranking == expected_assignment.player.ranking
        assert assignment.score == expected_assignment.score
        assert assignment.weighted_score == expected_assignment.weighted_score


def _player_list_to_team(player_list: list[Player]) -> Team:
    # Arbitrarily cast the players following the team composition rules.
    assignments = []
    player_list_ind = 0

    role_counts = TeamComposition.role_counts_dict()
    for required_role in TeamComposition.required_roles():
        required_number = role_counts[required_role]

        for _ in range(required_number):
            assignments.append(player_list[player_list_ind].to_assignment(required_role))
            player_list_ind += 1

    # Remaining players are given the fillable role (we assume here there is only one role that takes fills
    # and that num_remaining_players < max_fills_for_role).
    remaining_role = TeamComposition.fill_roles()[0]
    for player in player_list[player_list_ind:]:
        assignments.append(player.to_assignment(remaining_role))

    return Team(assignments)


def _get_team_list() -> list[list[Team]]:
    first_team_players = [
        Player("A", ranking=get_fake_ranking()),
        Player("B", ranking=get_fake_ranking()),
        Player("C", ranking=get_fake_ranking()),
        Player("D", ranking=get_fake_ranking()),
    ]

    # Second team also requires a fill
    second_team_players = [
        Player("E", ranking=get_fake_ranking()),
        Player("F", ranking=get_fake_ranking()),
        Player("G", ranking=get_fake_ranking()),
        Player("H", ranking=get_fake_ranking()),
    ]
    fill_player = Player("I", ranking=get_fake_ranking())
    other_fill_player = Player("J", ranking=get_fake_ranking())

    return [
        [_player_list_to_team(first_team_players), _player_list_to_team(second_team_players)],
        # First team has no fills
        [_player_list_to_team(first_team_players + [fill_player]), _player_list_to_team(second_team_players)],
        # Second team has no fills
        [_player_list_to_team(first_team_players), _player_list_to_team(second_team_players + [fill_player])],
        # Both have no fill
        [
            _player_list_to_team(first_team_players + [fill_player]),
            _player_list_to_team(second_team_players + [other_fill_player]),
        ],
        # Now we have three teams
        [
            _player_list_to_team(first_team_players),
            _player_list_to_team(second_team_players),
            _player_list_to_team(
                [
                    Player("K", ranking=get_fake_ranking()),
                    Player("L", ranking=get_fake_ranking()),
                    Player("M", ranking=get_fake_ranking()),
                    fill_player,
                    other_fill_player,
                ]
            ),
        ],
    ]


def test_team_composition() -> None:
    team = get_player_assignments(["A", "B", "C"], [PlayerRole.QUEEN, PlayerRole.FLEX, PlayerRole.FLEX])
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    team.append(
        Player("D", ranking=get_fake_ranking()).to_assignment(PlayerRole.FLEX),
    )
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    team = get_player_assignments(["A", "B"], [PlayerRole.QUEEN, PlayerRole.QUEEN])
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)

    # Now this should fail since we allow flex fills, but at most one
    team = get_player_assignments(["A", "B", "C"], [PlayerRole.QUEEN, PlayerRole.FLEX, PlayerRole.OBJECTIVE])
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    # And if we add the final FLEX players
    team.extend(get_player_assignments(["D"], [PlayerRole.FLEX]))
    TeamComposition.validate_team(team)
    team.extend(get_player_assignments(["E"], [PlayerRole.FLEX]))
    TeamComposition.validate_team(team)
    # Now we have too many players
    team.extend(get_player_assignments(["F"], [PlayerRole.FLEX]))
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)


def test_remaining_roles_remaining() -> None:
    team = get_player_assignments(["A", "B"], [PlayerRole.QUEEN, PlayerRole.FLEX])
    remaining_roles = TeamComposition.remaining_roles_required(team)
    counts: Dict[PlayerRole, int] = defaultdict(int)
    for role in remaining_roles:
        counts[role] += 1
    assert counts == {
        PlayerRole.FLEX: 2,
        PlayerRole.OBJECTIVE: 1,
    }


def test_csv_serialization() -> None:
    all_players = get_player_assignments(["A", "B", "C", "D", "E"], TeamComposition.roles)
    player_pool = PlayerNamePool([p.player for p in all_players])
    # Define a team with A,B,D,E, aka requiring a fill for a FLEX player.
    curr_assignments = [p for p in all_players if p.name in {"A", "B", "D", "E"}]
    team = Team(curr_assignments)

    new_team = Team.from_csv(team.to_csv(), player_pool)
    _assert_teams_equal(team, new_team)

    # Now add the last FLEX player.
    team = Team(all_players)
    new_team = Team.from_csv(team.to_csv(), player_pool)
    _assert_teams_equal(team, new_team)

    invalid_assignment_list = [p for p in all_players if p.name in {"A", "B", "D", "E"}]
    # This player is not in the all_players_dict, so it should fail.
    invalid_assignment_list.append(
        Player("F", ranking=get_fake_ranking()).to_assignment(PlayerRole.FLEX),
    )
    team = Team(invalid_assignment_list)
    csv_list = team.to_csv()
    with pytest.raises(ValueError):
        Team.from_csv(csv_list, player_pool)


@pytest.mark.parametrize("team_list", _get_team_list())
def test_multi_team_csv_serialization(team_list: list[Team], tmpdir: py.path.local) -> None:
    output_path = f"{tmpdir}/test.csv"
    write_teams_to_csv(output_path, team_list)

    all_players: list[PlayerAssignment] = sum([t.players for t in team_list], [])
    new_teams = read_teams_from_csv(output_path, PlayerNamePool([p.player for p in all_players]))
    for expected_team, team in zip(team_list, new_teams):
        _assert_teams_equal(expected_team, team)


def test_multi_team_csv_duplicate_player(tmpdir: py.path.local) -> None:
    first_team = get_player_assignments(
        ["A", "B", "C", "D"], [PlayerRole.QUEEN, PlayerRole.FLEX, PlayerRole.OBJECTIVE, PlayerRole.FLEX]
    )
    second_team = [
        first_team[0],
        *get_player_assignments(["E", "F", "G"], [PlayerRole.FLEX, PlayerRole.OBJECTIVE, PlayerRole.FLEX]),
    ]
    team_list = [Team(first_team), Team(second_team)]

    output_path = f"{tmpdir}/test.csv"
    all_players: list[PlayerAssignment] = first_team + second_team

    write_teams_to_csv(output_path, team_list)
    with pytest.raises(ValueError):
        read_teams_from_csv(output_path, PlayerNamePool([p.player for p in all_players]))


def test_is_num_assignments_valid() -> None:
    # For flex, we can have fills.
    assert TeamComposition.is_num_assignments_valid(PlayerRole.FLEX, 1, 1)
    assert TeamComposition.is_num_assignments_valid(PlayerRole.FLEX, 5, 4)
    assert TeamComposition.is_num_assignments_valid(PlayerRole.FLEX, 5, 6)
    # For queen/objective, we cannot have fills.
    for role in [PlayerRole.QUEEN, PlayerRole.OBJECTIVE]:
        assert TeamComposition.is_num_assignments_valid(role, 1, 1)
        assert not TeamComposition.is_num_assignments_valid(role, 5, 4)
        assert not TeamComposition.is_num_assignments_valid(role, 5, 6)
