from collections import defaultdict
from typing import Dict

import pytest

from src.data_types.player import Player, PlayerRole
from src.data_types.team import TeamComposition


def _fake_ranking() -> Dict[PlayerRole, float]:
    return {role: 5.0 for role in PlayerRole}


def test_team_composition() -> None:
    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("C", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team)
    # Should succeed
    TeamComposition.validate_team(team, allow_missing=True)
    team.append(
        Player("D", primary_role=PlayerRole.FLEX, ranking=_fake_ranking()).to_primary_role_assignment(),
    )
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team, allow_missing=True)
    team = [
        Player("A", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
        Player("B", primary_role=PlayerRole.QUEEN, ranking=_fake_ranking()).to_primary_role_assignment(),
    ]
    with pytest.raises(ValueError):
        TeamComposition.validate_team(team, allow_missing=True)


def test_required_roles_no_fill() -> None:
    assert TeamComposition.required_roles_no_fill() == [PlayerRole.QUEEN, PlayerRole.SPEED, PlayerRole.OBJECTIVE]


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
