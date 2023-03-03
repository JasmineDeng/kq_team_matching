from src.data_types import Player, PlayerRole
from src.sampling import _sample_players_by_highest_score, _sample_players_by_preferred_role


def test_sample_players_by_highest_score() -> None:
    players = [
        Player(
            name="A",
            primary_role=PlayerRole.FLEX,
            ranking={
                PlayerRole.FLEX: 3,
                PlayerRole.OBJECTIVE: 4,
            },
        ),
        Player(
            name="B",
            primary_role=PlayerRole.OBJECTIVE,
            ranking={
                PlayerRole.OBJECTIVE: 2,
                PlayerRole.FLEX: 5,
            },
        ),
        Player(
            name="C",
            primary_role=PlayerRole.OBJECTIVE,
            ranking={
                PlayerRole.OBJECTIVE: 4,
                PlayerRole.FLEX: 5,
            },
        ),
    ]
    assignments = _sample_players_by_highest_score(players, 1, PlayerRole.OBJECTIVE)
    assert len(assignments) == 1
    assert assignments[0].assigned_role == PlayerRole.OBJECTIVE
    # Get C even if A and C have the same score, because C wants to play objective
    assert assignments[0].player.name == "C"
    assignments = _sample_players_by_highest_score(players, 2, PlayerRole.OBJECTIVE)
    assert len(assignments) == 2
    # Now we get A and C, B is ignored even if they want to do objective because the score is low
    names = {a.player.name for a in assignments}
    assert names == {"A", "C"}


def test_sample_players_by_preferred_role() -> None:
    players = [
        Player(
            name="A",
            primary_role=PlayerRole.FLEX,
            ranking={
                PlayerRole.FLEX: 3,
                PlayerRole.OBJECTIVE: 4,
            },
        ),
        Player(
            name="B",
            primary_role=PlayerRole.OBJECTIVE,
            ranking={PlayerRole.OBJECTIVE: 2, PlayerRole.FLEX: 5},
        ),
    ]
    assignments = _sample_players_by_preferred_role(players, 1, PlayerRole.OBJECTIVE)
    assert len(assignments) == 1
    assert assignments[0].assigned_role == PlayerRole.OBJECTIVE
    assert assignments[0].player.name == "B"
