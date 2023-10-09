from typing import List

from src.data_types.player import Player, PlayerAssignment, PlayerRole
from src.data_types.team import Team, TeamComposition, roles_to_average_score


def find_fills(team: Team, all_players: list[Player], all_teams: List[Team]) -> List[PlayerAssignment]:
    """Find a fill, where we're aiming to hit the average score of finalized teams.

    We always assume that the fill is a FLEX player.
    """
    remaining_roles = TeamComposition.remaining_roles_required(team.players)
    if len(remaining_roles) == 0:
        print(f"No fills needed for team {team.team_name}")
        return []
    if not all(role == PlayerRole.FLEX for role in remaining_roles):
        raise ValueError(f"Can only fill FLEX right now. Remaining roles: {remaining_roles}")

    all_weighted_scores = [t.total_weighted_score for t in all_teams if not t.needs_fill]
    if len(all_weighted_scores) > 0:
        average_weighted_score = sum(all_weighted_scores) / len(all_weighted_scores)
        ideal_score = average_weighted_score - team.total_weighted_score
    else:
        # Set it to the average of the FLEX role
        role_to_average_score = roles_to_average_score(all_players)
        ideal_score = role_to_average_score[PlayerRole.FLEX]

    possible_players = []
    team_names = [p.player.name for p in team.players]
    for p in all_players:
        if p.name in team_names:
            continue
        # Always assume fills are flex
        possible_players.append(PlayerAssignment(player=p, assigned_role=PlayerRole.FLEX))
    possible_players.sort(key=lambda p: abs(ideal_score - p.weighted_score))
    # arbitrary threshold, return at most 5 players
    return possible_players[:5]
