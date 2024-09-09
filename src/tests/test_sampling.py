from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.sampling import _sample_players_by_highest_score, _sample_players_uniform


def test_sample_players_by_highest_score() -> None:
    players = [
        Player(
            name="B",
            ranking={
                PlayerRole.OBJECTIVE: 2,
                PlayerRole.FLEX: 5,
            },
        ).to_assignment(PlayerRole.OBJECTIVE),
        Player(
            name="C",
            ranking={
                PlayerRole.OBJECTIVE: 4,
                PlayerRole.FLEX: 5,
            },
        ).to_assignment(PlayerRole.OBJECTIVE),
    ]

    assignments: list[PlayerAssignment] = _sample_players_by_highest_score(players, 1)
    assert len(assignments) == 1
    assert assignments[0].assigned_role == PlayerRole.OBJECTIVE
    # Get C even if A and C have the same score, because C wants to play objective
    assert assignments[0].player.name == "C"
    assignments = _sample_players_by_highest_score(players, 2)
    assert len(assignments) == 2
    # Still prioritize by the primary/assigned role
    names = {a.player.name for a in assignments}
    assert names == {"B", "C"}


def _get_flex_player(name: str, score: int) -> PlayerAssignment:
    return Player(name, {PlayerRole.FLEX: score}).to_assignment(PlayerRole.FLEX)


def test_sample_players_uniformly() -> None:
    players = [_get_flex_player(str(i), i + 1) for i in range(10)]
    sampled_players: list[PlayerAssignment] = _sample_players_uniform(players, 6)
    scores = [p.score for p in sampled_players]
    assert set(scores) == {2, 4, 6, 8, 9, 10}
