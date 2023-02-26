import math
import random
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

from src.data_types import BasePlayerAssignment, Player, PlayerAssignment, PlayerRole, Team
from src.sampling import PlayerSamplingStrategy, sample_players


class _PlayerGroup(BasePlayerAssignment):
    def __init__(self, players: List[PlayerAssignment]) -> None:
        # Use a list for the players because order *does* matter. If there are too many queens, for ex., a team
        # could have multiple queens, but we assign queens *first* so the first queen in the list should be the
        # team's queen.
        self.players = players

    @property
    def score(self) -> float:
        return sum(p.score for p in self.players)

    @property
    def weighted_score(self) -> float:
        return round(sum(p.weighted_score for p in self.players), 3)

    def __str__(self) -> str:
        return f"players: {self.players}, score: {self.score}, weighted {self.weighted_score}\n"

    def __repr__(self) -> str:
        return str(self)


class _GroupWithExclusions(NamedTuple):
    group: _PlayerGroup
    to_exclude: Set[str]
    """Players who cannot be added to this group due to the exclusion set."""


def _sort_by_score_fn(assigned_player: BasePlayerAssignment) -> Tuple[float, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.weighted_score, random.random()


def _remove_subset_from_players(all_players: List[Player], to_remove: List[PlayerAssignment]) -> List[Player]:
    to_remove_names = {p.player.name for p in to_remove}
    to_return = [p for p in all_players if p.name not in to_remove_names]
    return to_return


def _players_to_assignment(players: List[Player], role: PlayerRole) -> List[PlayerAssignment]:
    return [PlayerAssignment(player=p, assigned_role=role) for p in players]


def _players_to_primary_role_assignment(players: List[Player]) -> List[PlayerAssignment]:
    """Create player assignments where players are assigned their primary role, UNLESS that role is queen.

    This method should be used to assign 'fills' for any arbitrary role for a created team, which should already
    have a queen.
    """
    to_return = []
    for p in players:
        if p.primary_role == PlayerRole.QUEEN:
            to_return.append(PlayerAssignment(player=p, assigned_role=PlayerRole.FLEX))
        else:
            to_return.append(PlayerAssignment(player=p, assigned_role=p.primary_role))
    return to_return


def _get_match_exclusion_set_players(
    all_players: List[Player], group: _PlayerGroup, exclusion_set: List[Set[str]]
) -> Set[str]:
    """Given a list of all players and a group of players, return all players who CANNOT be put on the team."""
    to_exclude: Set[str] = set()
    for player in all_players:
        # TODO this lower is kind of annoying maybe we should standardize somehow
        possible_team = {p.player.name.lower() for p in group.players} | {player.name.lower()}
        for exclusion in exclusion_set:
            exclusion_to_compare = {elem.lower() for elem in exclusion}
            if exclusion_to_compare.issubset(possible_team):
                to_exclude.add(player.name)
                break
    return to_exclude


def _get_player_with_exclusion_set(
    players: List[Player], role: PlayerRole, to_exclude: Set[str], ideal_score: float
) -> Optional[PlayerAssignment]:
    """Get a player with the given role, not in the exclusion set, with a score as close as possible to the ideal."""
    players_minus_exclusion = [player for player in players if player.name not in to_exclude]
    player_assignments = [PlayerAssignment(player=player, assigned_role=role) for player in players_minus_exclusion]
    # Get as close to the ideal score as possible
    sorted_players = sorted(player_assignments, key=lambda p: abs(ideal_score - p.score))
    if len(sorted_players) == 0:
        return None
    return sorted_players[0]


def _compute_ideal_score_for_group(
    groups: List[_PlayerGroup],
    player_sampling_strategy: PlayerSamplingStrategy,
    players: List[Player],
    num_required: int,
    role: PlayerRole,
) -> Dict[_PlayerGroup, float]:
    possible_players_pre_exclusion = sorted(
        sample_players(player_sampling_strategy, players, num_required, role),
        key=_sort_by_score_fn,
        reverse=True,
    )
    # If no possible players are found, the later code cannot find any either and will skip assignment (meaning we
    # need fills). But that will be handled later.
    if len(possible_players_pre_exclusion) == 0:
        return {group: 5.0 for group in groups}
    group_scores = [groups[ind].score + player.score for ind, player in enumerate(possible_players_pre_exclusion)]
    average_group_score = sum(group_scores) / len(group_scores)
    ideal_scores = {}
    for ind, group in enumerate(groups):
        if ind < len(possible_players_pre_exclusion):
            ideal_scores[group] = possible_players_pre_exclusion[ind].score
        else:
            ideal_scores[group] = average_group_score - group.score
    return ideal_scores


def _assign_players_with_exclusion_set(
    player_groups: List[_PlayerGroup], possible_players: List[Player], role: PlayerRole, exclusion_set: List[Set[str]]
) -> List[PlayerAssignment]:
    # The selected players for the role are reverse sorted, highest->lowest and we group the players by
    # the position in the list. E.g., strongest player is added to weakest group, and weakest player is
    # assigned to the strongest group.
    # However, since we have an exclusion set, we actually assign players to exclusion sets first, to avoid
    # assigning possibly the players we need to satisfy the constraint elsewhere. To avoid imbalancing, for
    # each team with an exclusion set, we have an 'ideal score' that the player should satisfy.
    # For non-exclusion-set teams, assignment goes as normal, where we sample players and assign the
    # highest->lowest and vice versa.
    player_groups = sorted(player_groups, key=_sort_by_score_fn)
    assigned_players = []

    groups_with_exclusion = []
    groups_without_exclusion = []
    for group in player_groups:
        group_exclusion_set = _get_match_exclusion_set_players(possible_players, group, exclusion_set)
        if len(group_exclusion_set) > 0:
            groups_with_exclusion.append(_GroupWithExclusions(group=group, to_exclude=group_exclusion_set))
        else:
            groups_without_exclusion.append(group)
    # Sort so that the group with the most exclusion sets is assigned first (to reduce the chances of not being
    # able to assign any teams)
    groups_with_exclusion = sorted(groups_with_exclusion, key=lambda g: len(g.to_exclude), reverse=True)

    # Find the ideal score that the player should have
    ideal_scores = _compute_ideal_score_for_group(
        player_groups, PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE, possible_players, len(player_groups), role
    )
    # Assign the teams with excluded people first
    for group in groups_with_exclusion:
        ideal_score = ideal_scores[group.group]
        assignment = _get_player_with_exclusion_set(
            possible_players,
            role,
            group.to_exclude,
            ideal_score,
        )
        if assignment is None:
            print(f"Skipping assignment for {group}, role {role}, ideal score {ideal_score}")
            continue
        group.group.players.append(assignment)
        assigned_players.append(assignment)
        possible_players = _remove_subset_from_players(possible_players, [assignment])
        print(f"Excluding {group.to_exclude}, picked player {assignment} for team {group}, ideal score: {ideal_score}")

    players_to_assign = sample_players(
        PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE, possible_players, len(groups_without_exclusion), role
    )
    players_to_assign = sorted(players_to_assign, key=_sort_by_score_fn, reverse=True)
    print(f"Picked player {players_to_assign} of expected {len(groups_without_exclusion)} from {possible_players}")
    for ind, assignment in enumerate(players_to_assign):
        groups_without_exclusion[ind].players.append(assignment)
        assigned_players.append(assignment)
    return assigned_players


def assign_players_to_teams(players: Set[Player], exclusion_set: List[Set[str]]) -> List[Team]:
    # Find the minimum number of teams required. At most we have 1 fill per team.
    total_teams = math.ceil(len(players) / 5)

    # assign roles to the teams in this order
    # after each step, the scores are ideally approximately the same.
    players_to_select = list(players)

    # Find all the queens first
    players_for_role = sample_players(
        PlayerSamplingStrategy.PRIORITIZE_PREFERRED_ROLE, players_to_select, total_teams, PlayerRole.QUEEN
    )
    players_to_select = _remove_subset_from_players(players_to_select, players_for_role)

    print(f"Got players for role {PlayerRole.QUEEN}: {players_for_role}")
    player_groups: List[_PlayerGroup] = sorted(
        [_PlayerGroup([elem]) for elem in players_for_role],
        key=_sort_by_score_fn,
    )

    for player_role in [
        PlayerRole.SPEED,
        PlayerRole.FLEX,
        PlayerRole.FLEX,
        PlayerRole.OBJECTIVE,
    ]:
        print(f"groups: {player_groups}")

        # if you can play speed, you can flex
        valid_roles = {player_role} if player_role != PlayerRole.FLEX else {PlayerRole.FLEX, PlayerRole.SPEED}
        current_subset = [player for player in players_to_select if player.primary_role in valid_roles]
        assigned_players = _assign_players_with_exclusion_set(player_groups, current_subset, player_role, exclusion_set)
        players_to_select = _remove_subset_from_players(players_to_select, assigned_players)

    if len(players_to_select) > 0:
        raise ValueError(f"Some people were not assigned! like: {players_to_select}")

    teams = [Team(group.players) for group in player_groups]
    return teams
