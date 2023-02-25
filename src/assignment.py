import math
import random
from typing import List, Optional, Set, Tuple

from src.data_types import BasePlayerAssignment, Player, PlayerAssignment, PlayerRole, Team
from src.sampling import PlayerSamplingStrategy, sample_players


def _sort_by_score_fn(assigned_player: BasePlayerAssignment) -> Tuple[int, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.score, random.random()


def _remove_subset_from_players(all_players: List[Player], to_remove: List[PlayerAssignment]) -> List[Player]:
    to_remove_names = {p.player.name for p in to_remove}
    to_return = [p for p in all_players if p.name not in to_remove_names]
    return to_return


def _should_find_fill(role: PlayerRole) -> bool:
    """Return if we should find a fill for the team, given the role we are currently assigning.

    Currently ONLY find fills if the role is vanilla - since this is the last role we assign for, it is the most
    likely to require fills. Filling for roles, such as queen, would probably require more complicated logic.
    """
    return role == PlayerRole.VANILLA


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


def _players_to_assignment(players: List[Player], role: PlayerRole) -> List[PlayerAssignment]:
    return [PlayerAssignment(player=p, assigned_role=role) for p in players]


def _players_to_primary_role_assignment(
    players: List[Player],
) -> List[PlayerAssignment]:
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
            if exclusion.issubset(possible_team):
                to_exclude.add(player.name)
                break
    return to_exclude


def _get_player_with_exclusion_set(
    players: List[Player], role: PlayerRole, to_exclude: Set[str], ideal_score: int
) -> PlayerAssignment:
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


def assign_players_to_teams(
    players: Set[Player], player_sampling_strategy: PlayerSamplingStrategy, exclusion_set: List[Set[str]]
) -> List[Team]:
    # Find the minimum number of teams required. At most we have 4 fills.
    total_teams = math.ceil(len(players) / 5)

    # assign roles to the teams in this order
    # after each step, the scores are ideally approximately the same.
    players_to_select = list(players)
    player_groups: Optional[List[_PlayerGroup]] = None
    for player_role in [
        PlayerRole.QUEEN,
        PlayerRole.SPEED,
        PlayerRole.OBJECTIVE,
        PlayerRole.VANILLA,
    ]:
        if player_groups is None:
            # If player groups are currently None, then initialize to the current players, sorted lowest->highest score
            # TODO what do we do if there are fills? possibly: pick someone specific to be a fill, or pick most common
            #  score and anybody with that score can fill. or, average all queen scores and let anybody fill (has more
            #  variability). fills not a problem with the current test data
            players_for_role = sample_players(player_sampling_strategy, players_to_select, total_teams, player_role)
            players_to_select = _remove_subset_from_players(players_to_select, players_for_role)

            if not _should_find_fill(player_role):
                assert len(players_for_role) == total_teams, f"fills not yet implemented for role {player_role}"
            else:
                # If fills are needed, find any random player remaining and assign them their primary role.
                subsampled_players = random.sample(players_to_select, total_teams - len(players_for_role))
                subsampled_assignment = _players_to_primary_role_assignment(subsampled_players)
                players_for_role.extend(subsampled_assignment)
                players_to_select = _remove_subset_from_players(players_to_select, subsampled_assignment)

            print(f"Got players for role {player_role}: {players_for_role}")
            player_groups = sorted(
                list(_PlayerGroup([elem]) for elem in players_for_role),
                key=_sort_by_score_fn,
            )
        else:
            # If player groups not None, then sort the current groups to ensure lowest->highest score
            # The selected players for the role are reverse sorted, highest->lowest and we group the players by
            # the position in the list. E.g., strongest player is added to weakest group, and weakest player is
            # assigned to the strongest group.
            # However, since we have an exclusion set, we actually assign players to exclusion sets first, to avoid
            # assigning possibly the players we need to satisfy the constraint elsewhere. To avoid imbalancing, for
            # each team with an exclusion set, we have an 'ideal score' that the player should satisfy.
            # For non-exclusion-set teams, assignment goes as normal, where we sample players and assign the
            # highest->lowest and vice versa.
            player_groups = sorted(player_groups, key=_sort_by_score_fn)
            possible_players_pre_exclusion = sorted(
                sample_players(player_sampling_strategy, players_to_select, total_teams, player_role),
                key=_sort_by_score_fn,
                reverse=True,
            )
            ideal_scores = {group: possible_players_pre_exclusion[ind].score for ind, group in enumerate(player_groups)}
            group_to_exclusion_set = {
                group: _get_match_exclusion_set_players(players_to_select, group, exclusion_set)
                for group in player_groups
            }
            # Assign the teams with excluded people first
            groups_with_exclusion = [group for group in player_groups if len(group_to_exclusion_set[group]) > 0]
            groups_without_exclusion = [group for group in player_groups if len(group_to_exclusion_set[group]) == 0]
            for group in groups_with_exclusion:
                curr_exclusion = group_to_exclusion_set[group]
                assignment = _get_player_with_exclusion_set(
                    players_to_select, player_role, curr_exclusion, ideal_scores[group]
                )
                group.players.append(assignment)
                players_to_select = _remove_subset_from_players(players_to_select, [assignment])
                print(f"Excluding {curr_exclusion}, picked player {assignment} for team {group}")

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
