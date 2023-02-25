import enum
import random
from typing import List, Tuple

from src.data_types import Player, PlayerAssignment, PlayerRole


class PlayerSamplingStrategy(enum.Enum):
    """Enum representing the ways we sample players for a given role."""

    PRIORITIZE_PREFERRED_ROLE = 0
    PRIORITIZE_HIGHEST_SCORE = 1


def _sort_fn_role_priority(
    assigned_player: PlayerAssignment,
) -> Tuple[int, int, float]:
    is_primary_role = assigned_player.assigned_role == assigned_player.player.ranking.primary_role
    # Return a higher value for if it is their primary role
    return assigned_player.score, int(is_primary_role), random.random()


def _sample_players_by_highest_score(
    players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    """Select players for their provided role, based on the player's score.

    This method selects the players for the role by the highest score in their primary or secondary scores. The sort
    function is biased towards players with primary roles, but if a player with the secondary role has a high score,
    they are always selected over a primary-role person.
    """
    primary_players = [
        PlayerAssignment(player=p, assigned_role=role) for p in players if p.ranking.primary_role == role
    ]
    secondary_players = [
        PlayerAssignment(player=p, assigned_role=role) for p in players if p.ranking.secondary_role == role
    ]
    all_players = primary_players + secondary_players
    # We must sort this reversed since we want to select the strongest players. Players with the role as their primary
    # role have [1] in the second element, so they will also be prioritized via tie break.
    all_players.sort(key=_sort_fn_role_priority, reverse=True)
    return all_players[:num_required]


def _sample_players_by_preferred_role(
    players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    """Select players for the provided role, based on the player's preferred role.

    This method prioritizes that role people want to play; we only select the players for their secondary roles if
    there are not enough people with the primary role.

    Primary players denote players who have the role as their primary role, secondary players denote players who have
    the role as their secondary role.

    If len(primary_players) >= num_required, then remove a random subset until we have the correct amount.
    If len(primary_players) + len(secondary_players) >= num_required, then remove a random subset of secondary
        players until we have the correct amount.
    Else, return all primary/secondary players, but there must be fills.
    """
    primary_players = [
        PlayerAssignment(player=p, assigned_role=role) for p in players if p.ranking.primary_role == role
    ]
    secondary_players = [
        PlayerAssignment(player=p, assigned_role=role) for p in players if p.ranking.secondary_role == role
    ]
    if len(primary_players) >= num_required:
        return random.sample(primary_players, num_required)
    if len(primary_players) + len(secondary_players) < num_required:
        return primary_players + secondary_players
    num_required_secondary = num_required - len(primary_players)
    secondary_players_sample = random.sample(secondary_players, num_required_secondary)
    return primary_players + secondary_players_sample


def sample_players(
    player_sampling_strategy: PlayerSamplingStrategy, players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    if player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_PREFERRED_ROLE:
        return _sample_players_by_preferred_role(players, num_required, role)
    elif player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE:
        return _sample_players_by_highest_score(players, num_required, role)
    raise NotImplementedError(f"No sampling strategy defined for enum: {player_sampling_strategy}")
