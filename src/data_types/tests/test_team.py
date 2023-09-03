from collections import defaultdict
from typing import Dict

import py.path
import pytest

from src.data_types.player import Player, PlayerRole
from src.data_types.team import Team, TeamComposition, read_teams_from_csv, write_teams_to_csv


def _fake_ranking() -> Dict[PlayerRole, float]:
    return {role: 5.0 for role in PlayerRole}


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
    return Team([p.to_primary_role_assignment() for p in player_list])


def _get_team_list() -> list[list[Team]]:
    first_team_players = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()),
        Player("C", primary_role=PlayerRole.SPEED, ranking=_fake_ranking()),
        Player("D", primary_role=PlayerRole.OBJECTIVE, ranking=_fake_ranking()),
    ]

    # Second team also requires a fill
    second_team_players = [
        Player("E", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()),
        Player("F", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()),
        Player("G", primary_role=PlayerRole.SPEED, ranking=_fake_ranking()),
        Player("H", primary_role=PlayerRole.OBJECTIVE, ranking=_fake_ranking()),
    ]
    fill_player = Player("I", primary_role=PlayerRole.FLEX, ranking=_fake_ranking())
    other_fill_player = Player("J", primary_role=PlayerRole.FLEX, ranking=_fake_ranking())

    return [
        [_player_list_to_team(first_team_players), _player_list_to_team(second_team_players)],
        # First team has no fills
        [_player_list_to_team(first_team_players + [fill_player]), _player_list_to_team(first_team_players)],
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
                    Player("K", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()),
                    Player("L", primary_role=PlayerRole.OBJECTIVE, ranking=_fake_ranking()),
                    Player("M", primary_role=PlayerRole.SPEED, ranking=_fake_ranking()),
                    fill_player,
                    other_fill_player,
                ]
            ),
        ],
    ]


def test_team_composition() -> None:
    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("C", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    team.append(
        Player("D", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
    )
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)

    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("C", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("D", primary_role=PlayerRole.SPEED, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    # Now this should succeed since we allow flex fills
    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("C", primary_role=PlayerRole.OBJECTIVE, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("D", primary_role=PlayerRole.SPEED, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    TeamComposition.validate_team(team)
    # And if we add the final FLEX player
    team.append(Player("E", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment())
    TeamComposition.validate_team(team)
    # And if we add one more, it is now too many players
    team.append(Player("F", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment())
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)


def test_remaining_roles_remaining() -> None:
    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    remaining_roles = TeamComposition.remaining_roles_required(team)
    counts: Dict[PlayerRole, int] = defaultdict(int)
    for role in remaining_roles:
        counts[role] += 1
    assert counts == {
        PlayerRole.FLEX: 1,
        PlayerRole.SPEED: 1,
        PlayerRole.OBJECTIVE: 1,
    }


def test_csv_serialization() -> None:
    all_players = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()),
        Player("C", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()),
        Player("D", primary_role=PlayerRole.SPEED, ranking=_fake_ranking()),
        Player("E", primary_role=PlayerRole.OBJECTIVE, ranking=_fake_ranking()),
    ]
    all_players_dict = {p.name: p for p in all_players}
    # Define a team with A,B,D,E, aka requiring a fill for a FLEX player.
    team = Team([p.to_primary_role_assignment() for p in all_players if p.name in {"A", "B", "D", "E"}])

    new_team = Team.from_csv(team.to_csv(), all_players_dict)
    _assert_teams_equal(team, new_team)

    # Now add the last FLEX player.
    team = Team([p.to_primary_role_assignment() for p in all_players])
    new_team = Team.from_csv(team.to_csv(), all_players_dict)
    _assert_teams_equal(team, new_team)

    invalid_player_list = [p.to_primary_role_assignment() for p in all_players if p.name in {"A", "B", "D", "E"}]
    # This player is not in the all_players_dict, so it should fail.
    invalid_player_list.append(
        Player("F", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment()
    )
    team = Team(invalid_player_list)
    csv_list = team.to_csv()
    with pytest.raises(ValueError):
        Team.from_csv(csv_list, all_players_dict)


@pytest.mark.parametrize("team_list", _get_team_list())
def test_multi_team_csv_serialization(team_list: list[Team], tmpdir: py.path.local) -> None:
    output_path = f"{tmpdir}/test.csv"
    write_teams_to_csv(output_path, team_list)

    all_players = sum([t.players for t in team_list], [])
    new_teams = read_teams_from_csv(output_path, {p.player.name: p.player for p in all_players})
    for expected_team, team in zip(team_list, new_teams):
        _assert_teams_equal(expected_team, team)


def test_is_num_assignments_valid() -> None:
    # For speed, we require at least the number of players.
    assert TeamComposition.is_num_assignments_valid(PlayerRole.SPEED, 1, 1)
    assert not TeamComposition.is_num_assignments_valid(PlayerRole.SPEED, 5, 4)
    assert TeamComposition.is_num_assignments_valid(PlayerRole.SPEED, 5, 6)
    # For flex, we can have fills.
    assert TeamComposition.is_num_assignments_valid(PlayerRole.FLEX, 1, 1)
    assert TeamComposition.is_num_assignments_valid(PlayerRole.FLEX, 5, 4)
    assert TeamComposition.is_num_assignments_valid(PlayerRole.FLEX, 5, 6)
    # For queen/objective, we cannot have fills.
    for role in [PlayerRole.QUEEN, PlayerRole.OBJECTIVE]:
        assert TeamComposition.is_num_assignments_valid(role, 1, 1)
        assert not TeamComposition.is_num_assignments_valid(role, 5, 4)
        assert not TeamComposition.is_num_assignments_valid(role, 5, 6)
