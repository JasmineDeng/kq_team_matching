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
