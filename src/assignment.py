import enum
import math
import random
from typing import List, Optional, Set, Tuple

from src.data_types import BasePlayerAssignment, Player, PlayerAssignment, PlayerRole, Team


class PlayerSamplingStrategy(enum.Enum):
    """Enum representing the ways we sample players for a given role."""

    PRIORITIZE_PREFERRED_ROLE = 0
    PRIORITIZE_HIGHEST_SCORE = 1


def _sort_fn(assigned_player: BasePlayerAssignment) -> Tuple[int, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.score, random.random()


def _sort_fn_role_priority(
    assigned_player: PlayerAssignment,
) -> Tuple[int, int, float]:
    is_primary_role = assigned_player.assigned_role == assigned_player.player.ranking.primary_role
    # Return a higher value for if it is their primary role
    return assigned_player.score, int(is_primary_role), random.random()


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


def check_blacklist(potential_player: Player, group, blacklist) -> bool:
    for y in group.players:
        y = y.player.name
        for x in blacklist:
            if x == {potential_player, y}:
                return True
    return False


def assign_players_to_teams(
    players: Set[Player], player_sampling_strategy: PlayerSamplingStrategy, blacklist
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
        if player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_PREFERRED_ROLE:
            players_for_role = _sample_players_by_preferred_role(players_to_select, total_teams, player_role)
        elif player_sampling_strategy == PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE:
            players_for_role = _sample_players_by_highest_score(players_to_select, total_teams, player_role)
        else:
            raise NotImplementedError(f"No sampling strategy defined for enum: {player_sampling_strategy}")
        # TODO what do we do if there are fills? possibly: pick someone specific to be a fill, or pick most common
        #  score and anybody with that score can fill. or, average all queen scores and let anybody fill (has more
        #  variability). fills not a problem with the current test data

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

        if player_groups is None:
            # If player groups are currently None, then initialize to the current players, sorted lowest->highest score
            player_groups = sorted(
                list(_PlayerGroup([elem]) for elem in players_for_role),
                key=_sort_fn,
            )
        else:
            # If player groups not None, then sort the current groups to ensure lowest->highest score
            # The selected players for the role are reverse sorted, highest->lowest and we group the players by
            # the position in the list. E.g., strongest player is added to weakest group, and weakest player is
            # assigned to the strongest group.
            # If a player cannot be added to the player group, then??
            player_groups = sorted(player_groups, key=_sort_fn)
            players_for_role = sorted(list(players_for_role), key=_sort_fn, reverse=True)
            for ind, group in enumerate(player_groups):
                potential_player = players_for_role[ind].player.name
                check_blacklist(potential_player, group, blacklist)
                group.players.append(players_for_role[ind])
            # for group in player_groups:
            # possible_players = _get_all_players_not_on_blacklist(blacklist, all_players) <- need to write this function
            # player = _sample_players_by_highest_score(possible_players, 1, role)
            # group.players.append(player)
            # _remove_from_set(all_players, player)

    # The remaining players are what we can get.
    remaining_players = sorted(_players_to_primary_role_assignment(players_to_select), key=_sort_fn)
    assert player_groups is not None
    player_groups = sorted(player_groups, key=_sort_fn, reverse=True)
    print([group.score for group in player_groups])
    for ind, assignment in enumerate(remaining_players):
        player_groups[ind].players.append(assignment)

    teams = [Team(group.players) for group in player_groups]
    return teams
