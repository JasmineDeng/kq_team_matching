import enum
import math
import random
from typing import List

from src.data_types.player import PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerNamePool


class PlayerSamplingStrategy(enum.Enum):
    """Enum representing the ways we sample players for a given role."""

    PRIORITIZE_HIGHEST_SCORE = enum.auto()
    UNIFORM_SCORE = enum.auto()
    RANDOM = enum.auto()


def get_players_for_role(player_pool: PlayerNamePool[PlayerAssignment], role: PlayerRole) -> List[PlayerAssignment]:
    return [p for p in player_pool.players if p.assigned_role == role]


def _sort_fn_random_tie_break(player: PlayerAssignment) -> tuple[float, float]:
    return player.score, random.random()


def _sample_players_by_highest_score(all_players: List[PlayerAssignment], num_required: int) -> List[PlayerAssignment]:
    """Select players for their provided role, based on the player's score.

    This method selects the players for the role with the highest score. Ties are broken if the role is a person's
    primary role, but the primary role is mostly ignored.
    """
    # We must sort this reversed since we want to select the strongest players. Players with the role as their primary
    # role have [1] in the second element, so they will also be prioritized via tie break.
    all_players.sort(key=_sort_fn_random_tie_break, reverse=True)
    return all_players[:num_required]


def _sample_players_uniform(all_players: List[PlayerAssignment], num_required: int) -> List[PlayerAssignment]:
    all_players = sorted(all_players, key=lambda p: p.score, reverse=True)
    stride = math.ceil(len(all_players) / num_required)
    to_return = []
    # Represent 'strides' to step through the list
    ind = 0
    starting_ind = 0
    for _ in range(num_required):
        to_return.append(all_players[ind])
        ind += stride
        # If we've exceeded the length, reset, but *not* to the same starting index to ensure we sample
        # WITHOUT replacement
        if ind >= len(all_players):
            starting_ind += 1
            if starting_ind == stride and len(to_return) != num_required:
                return to_return
            ind = starting_ind
    return to_return


def sample_players(
    player_sampling_strategy: PlayerSamplingStrategy,
    players: PlayerNamePool[PlayerAssignment],
    num_required: int,
    role: PlayerRole,
) -> List[PlayerAssignment]:
    all_players_for_role = get_players_for_role(players, role)

    if player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE:
        return _sample_players_by_highest_score(all_players_for_role, num_required)
    elif player_sampling_strategy == PlayerSamplingStrategy.UNIFORM_SCORE:
        return _sample_players_uniform(all_players_for_role, num_required)
    elif player_sampling_strategy == PlayerSamplingStrategy.RANDOM:
        return random.sample(all_players_for_role, num_required)
    raise NotImplementedError(f"No sampling strategy defined for enum: {player_sampling_strategy}")
