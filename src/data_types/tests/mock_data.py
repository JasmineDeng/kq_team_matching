from typing import Dict

from src.data_types.player import PlayerRole


def get_fake_ranking() -> Dict[PlayerRole, float]:
    return {role: 5.0 for role in PlayerRole}
