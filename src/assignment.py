import math
import random
from typing import Dict, List, NamedTuple, Set, Tuple

from src.data_types import BasePlayerAssignment, Player, PlayerAssignment, PlayerRole, Team
from src.sampling import PlayerSamplingStrategy, sample_players


class _PlayerGroup(BasePlayerAssignment):
    def __init__(self, players: List[PlayerAssignment]) -> None:
        # Use a list for the players because order *does* matter. If there are too many queens, for ex., a team
        # could have multiple queens, but we assign queens *first* so the first queen in the list should be the
        # team's queen.
        self.players = players

    @property
    def score(self) -> int:
        return sum(p.score for p in self.players)

    def __str__(self) -> str:
        return f"players: {self.players}, score: {self.score}"

    def __repr__(self) -> str:
        return str(self)


class _GroupWithExclusions(NamedTuple):
    group: _PlayerGroup
    to_exclude: Set[str]
    """Players who cannot be added to this group due to the exclusion set."""


def _sort_by_score_fn(assigned_player: BasePlayerAssignment) -> Tuple[int, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.score, random.random()


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
        if p.ranking.primary_role == PlayerRole.QUEEN:
            to_return.append(PlayerAssignment(player=p, assigned_role=p.ranking.secondary_role))
        else:
            to_return.append(PlayerAssignment(player=p, assigned_role=p.ranking.primary_role))
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
    players: List[Player], role: PlayerRole, to_exclude: Set[str], ideal_score: int
) -> PlayerAssignment:
    """Get a player with the given role, not in the exclusion set, with a score as close as possible to the ideal."""
    players_minus_exclusion = [player for player in players if player.name not in to_exclude]
    player_assignments = [
        PlayerAssignment(player=player, assigned_role=role)
        for player in players_minus_exclusion
        if role in player.possible_roles
    ]
    # Get as close to the ideal score as possible
    sorted_players = sorted(player_assignments, key=lambda p: abs(ideal_score - p.score))
    if len(sorted_players) == 0:
        raise ValueError(f"Requested at least player for role {role} from {player_assignments}, found none")
    return sorted_players[0]


def _compute_ideal_score_for_group(
    groups: List[_PlayerGroup],
    player_sampling_strategy: PlayerSamplingStrategy,
    players: List[Player],
    num_required: int,
    role: PlayerRole,
) -> Dict[_PlayerGroup, int]:
    possible_players_pre_exclusion = sorted(
        sample_players(player_sampling_strategy, players, num_required, role),
        key=_sort_by_score_fn,
        reverse=True,
    )
    ideal_scores = {group: possible_players_pre_exclusion[ind].score for ind, group in enumerate(groups)}
    return ideal_scores


def assign_players_to_teams(
    players: Set[Player], player_sampling_strategy: PlayerSamplingStrategy, exclusion_set: List[Set[str]]
) -> List[Team]:
    # Find the minimum number of teams required. At most we have 4 fills.
    total_teams = math.ceil(len(players) / 5)

    # assign roles to the teams in this order
    # after each step, the scores are ideally approximately the same.
    players_to_select = list(players)

    # Find all the queens first
    players_for_role = sample_players(player_sampling_strategy, players_to_select, total_teams, PlayerRole.QUEEN)
    players_to_select = _remove_subset_from_players(players_to_select, players_for_role)

    print(f"Got players for role {PlayerRole.QUEEN}: {players_for_role}")
    player_groups: List[_PlayerGroup] = sorted(
        [_PlayerGroup([elem]) for elem in players_for_role],
        key=_sort_by_score_fn,
    )

    for player_role in [
        PlayerRole.SPEED,
        PlayerRole.OBJECTIVE,
        PlayerRole.VANILLA,
    ]:
        # The selected players for the role are reverse sorted, highest->lowest and we group the players by
        # the position in the list. E.g., strongest player is added to weakest group, and weakest player is
        # assigned to the strongest group.
        # However, since we have an exclusion set, we actually assign players to exclusion sets first, to avoid
        # assigning possibly the players we need to satisfy the constraint elsewhere. To avoid imbalancing, for
        # each team with an exclusion set, we have an 'ideal score' that the player should satisfy.
        # For non-exclusion-set teams, assignment goes as normal, where we sample players and assign the
        # highest->lowest and vice versa.
        player_groups = sorted(player_groups, key=_sort_by_score_fn)
        groups_with_exclusion = []
        groups_without_exclusion = []
        for group in player_groups:
            group_exclusion_set = _get_match_exclusion_set_players(players_to_select, group, exclusion_set)
            if len(group_exclusion_set) > 0:
                groups_with_exclusion.append(_GroupWithExclusions(group=group, to_exclude=group_exclusion_set))
            else:
                groups_without_exclusion.append(group)
        # Sort so that the group with the most exclusion sets is assigned first (to reduce the chances of not being
        # able to assign any teams)
        groups_with_exclusion = sorted(groups_with_exclusion, key=lambda g: len(g.to_exclude), reverse=True)

        # Find the ideal score that the player should have
        ideal_scores = _compute_ideal_score_for_group(
            player_groups, player_sampling_strategy, players_to_select, total_teams, player_role
        )
        # Assign the teams with excluded people first
        for group in groups_with_exclusion:
            ideal_score = ideal_scores[group.group]
            assignment = _get_player_with_exclusion_set(
                players_to_select,
                player_role,
                group.to_exclude,
                ideal_score,
            )
            group.group.players.append(assignment)
            players_to_select = _remove_subset_from_players(players_to_select, [assignment])
            print(
                f"Excluding {group.to_exclude}, picked player {assignment} for team {group}, ideal score: {ideal_score}"
            )

        players_to_assign = sample_players(
            player_sampling_strategy, players_to_select, len(groups_without_exclusion), player_role
        )
        players_to_assign = sorted(players_to_assign, key=_sort_by_score_fn, reverse=True)
        players_to_select = _remove_subset_from_players(players_to_select, players_to_assign)
        print(f"Picked player {players_to_assign}")
        for ind, group in enumerate(groups_without_exclusion):
            group.players.append(players_to_assign[ind])

    # The remaining players are what we can get.
    remaining_players = sorted(_players_to_primary_role_assignment(players_to_select), key=_sort_by_score_fn)
    assert player_groups is not None
    player_groups = sorted(player_groups, key=_sort_by_score_fn, reverse=True)
    print([group.score for group in player_groups])
    for ind, assignment in enumerate(remaining_players):
        player_groups[ind].players.append(assignment)

    teams = [Team(group.players) for group in player_groups]
    return teams
