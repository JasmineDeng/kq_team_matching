import enum
import random
from typing import List, Tuple

from src.data_types import Player, PlayerAssignment, PlayerRole


class PlayerSamplingStrategy(enum.Enum):
    """Enum representing the ways we sample players for a given role."""

    PRIORITIZE_PREFERRED_ROLE = 0
    PRIORITIZE_HIGHEST_SCORE = 1
    ONLY_PREFERRED_ROLE = 2


def _sort_fn_role_priority(
    assigned_player: PlayerAssignment,
) -> Tuple[float, int, float]:
    is_primary_role = assigned_player.assigned_role == assigned_player.player.primary_role
    # Return a higher value for if it is their primary role
    return assigned_player.score, int(is_primary_role), random.random()


def _sample_players_by_highest_score(
    players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    """Select players for their provided role, based on the player's score.

    This method selects the players for the role with the highest score. Ties are broken if the role is a person's
    primary role, but the primary role is mostly ignored.
    """
    all_players = [PlayerAssignment(player=p, assigned_role=role) for p in players]
    # We must sort this reversed since we want to select the strongest players. Players with the role as their primary
    # role have [1] in the second element, so they will also be prioritized via tie break.
    all_players.sort(key=_sort_fn_role_priority, reverse=True)
    return all_players[:num_required]


def _sample_players_by_preferred_role(
    players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    """Select players for the provided role, based on the player's preferred role.

    This method prioritizes that role people want to play; we only select the players for their other roles if
    there are not enough people with the primary role.

    Primary players denote players who have the role as their primary role.
    """
    primary_players = [PlayerAssignment(player=p, assigned_role=role) for p in players if p.primary_role == role]
    remaining_players = [PlayerAssignment(player=p, assigned_role=role) for p in players]
    if len(primary_players) >= num_required:
        return random.sample(primary_players, num_required)
    if len(primary_players) + len(remaining_players) < num_required:
        return primary_players + remaining_players
    num_required_remaining = num_required - len(primary_players)
    remaining_players_sample = random.sample(remaining_players, num_required_remaining)
    return primary_players + remaining_players_sample


def _sample_players_only_preferred_role(
    players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    """Select players who MUST have the role as their primary role."""
    primary_players = [PlayerAssignment(player=p, assigned_role=role) for p in players if p.primary_role == role]
    if len(primary_players) < num_required:
        raise ValueError(f"Not enough players with primary role {role} for required amount {num_required}")
    if len(primary_players) > num_required:
        return random.sample(primary_players, num_required)
    return primary_players


def sample_players(
    player_sampling_strategy: PlayerSamplingStrategy, players: List[Player], num_required: int, role: PlayerRole
) -> List[PlayerAssignment]:
    if player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_PREFERRED_ROLE:
        return _sample_players_by_preferred_role(players, num_required, role)
    elif player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE:
        return _sample_players_by_highest_score(players, num_required, role)
    elif player_sampling_strategy == PlayerSamplingStrategy.ONLY_PREFERRED_ROLE:
        return _sample_players_only_preferred_role(players, num_required, role)
    raise NotImplementedError(f"No sampling strategy defined for enum: {player_sampling_strategy}")
