from typing import Dict

from src.data_types.player import Player, PlayerAssignment, PlayerRole


def get_fake_ranking() -> Dict[PlayerRole, float]:
    return {role: 5.0 for role in PlayerRole}


def get_player_assignments(names: list[str], roles: list[PlayerRole]) -> list[PlayerAssignment]:
    assignments = []
    for name, role in zip(names, roles, strict=True):
        player = Player(name=name, ranking=get_fake_ranking())
        assignments.append(PlayerAssignment(player, role))
    return assignments
