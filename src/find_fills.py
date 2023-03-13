import math
from typing import List, Set

from src.data_types.player import Player, PlayerAssignment, PlayerRole, clip_value
from src.data_types.team import Team


def find_fills(team: Team, all_players: Set[Player], ideal_score: float) -> List[str]:
    """Find a fill, where we're aiming to hit the average score of finalized teams.

    The fill is generally a range, and any kind of player can fill as flex.
    """
    score_diff = ideal_score - team.total_score
    # Use a range for all the score differences to increase the chances of finding a fill.
    if float(score_diff).is_integer():
        scores_to_find = {score_diff}
    else:
        scores_to_find = {math.ceil(score_diff), math.floor(score_diff)}
    scores_to_find = {clip_value(val) for val in scores_to_find}
    possible_players = []
    team_names = [p.player.name for p in team.players]
    for p in all_players:
        if p.name in team_names:
            continue
        # Always assume fills are flex
        if p.ranking[PlayerRole.FLEX] in scores_to_find:
            possible_players.append(PlayerAssignment(player=p, assigned_role=PlayerRole.FLEX))

    return [f"{p.player.name} ({p.assigned_role.name[0]}) ({p.score})" for p in possible_players]
