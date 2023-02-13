import math
from typing import List, Set

from data_types import Player, PlayerRole, Team, clip_value


def find_fills(team: Team, all_players: Set[Player], ideal_score: float) -> List[str]:
    """Find a fill, where we're aiming to hit the average score of finalized teams.

    The fill is generally a range, and any kind of player can fill. Players who are primarily queens will have
    their secondary role assigned.
    """
    score_diff = ideal_score - team.total_score
    if float(score_diff).is_integer():
        scores_to_find = {score_diff, score_diff + 1, score_diff - 1}
    else:
        scores_to_find = {math.ceil(score_diff), math.floor(score_diff)}
    scores_to_find = {clip_value(val) for val in scores_to_find}
    possible_players = []
    for p in all_players:
        if p.ranking.primary_role == PlayerRole.QUEEN and p.ranking.secondary_ranking in scores_to_find:
            possible_players.append(p)
        if p.ranking.primary_role != PlayerRole.QUEEN and p.ranking.primary_ranking in scores_to_find:
            possible_players.append(p)

    return [f"{p.name} ({p.ranking.primary_ranking})" for p in possible_players]
