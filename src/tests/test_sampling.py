from src.data_types.player import Player, PlayerRole
from src.sampling import _sample_players_by_highest_score, _sample_players_by_preferred_role, _sample_players_uniform


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
    # Still prioritize by the primary/assigned role
    names = {a.player.name for a in assignments}
    assert names == {"B", "C"}


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


def _get_flex_player(name: str, score: int) -> Player:
    return Player(name, PlayerRole.FLEX, {PlayerRole.FLEX: score})


def test_sample_players_uniformly() -> None:
    players = [_get_flex_player(str(i), i + 1) for i in range(10)]
    sampled_players = _sample_players_uniform(players, 6, PlayerRole.FLEX)
    scores = [p.score for p in sampled_players]
    assert set(scores) == {2, 4, 6, 8, 9, 10}
