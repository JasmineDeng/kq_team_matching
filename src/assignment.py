import math
import random
from typing import List, Optional, Set, Tuple

from data_types import (BasePlayerAssignment, Player, PlayerAssignment,
                        PlayerRole, Team)


def _sort_fn(assigned_player: BasePlayerAssignment) -> Tuple[int, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.score, random.random()


def _sort_fn_role_priority(assigned_player: PlayerAssignment) -> Tuple[int, int, float]:
    is_primary_role = assigned_player.assigned_role == assigned_player.player.ranking.primary_role
    return assigned_player.score, int(is_primary_role), random.random()


def _warrior_sort_fn(player: Player) -> Tuple[int, int, float]:
    # Lower number if the player is a warrior, so if we sort ascending, it appears first
    warrior_int: int
    if player.ranking.primary_role == PlayerRole.VANILLA:
        warrior_int = 0
    else:
        warrior_int = 1
    return warrior_int, player.ranking.primary_ranking, random.random()


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


def _players_to_primary_role_assignment(players: List[Player]) -> List[PlayerAssignment]:
    to_return = []
    for p in players:
        if p.ranking.primary_role == PlayerRole.QUEEN:
            to_return.append(PlayerAssignment(player=p, assigned_role=p.ranking.secondary_role))
        else:
            to_return.append(PlayerAssignment(player=p, assigned_role=p.ranking.primary_role))
    return to_return


def _select_player_role(players: List[Player], num_required: int, role: PlayerRole) -> List[PlayerAssignment]:
    """Select players for the provided role.

    Primary players denote players who have the role as their primary role, secondary players denote players who have
    the role as their secondary role.

    If len(primary_players) >= num_required, then remove a random subset until we have the correct amount.
    If len(primary_players) + len(secondary_players) >= num_required, then remove a random subset of secondary
        players until we have the correct amount.
    Else, return all primary/secondary players, but there must be fills.
    """
    primary_players = [PlayerAssignment(player=p, assigned_role=role) for p in players if p.ranking.primary_role == role]
    secondary_players = [PlayerAssignment(player=p, assigned_role=role) for p in players if p.ranking.secondary_role == role]
    # if True or role == PlayerRole.SPEED:
    #     all_players = primary_players + secondary_players
    #     all_players.sort(key=_sort_fn_role_priority, reverse=True)
    #     return all_players[:num_required]
    if len(primary_players) >= num_required:
        return random.sample(primary_players, num_required)
    if len(primary_players) + len(secondary_players) < num_required:
        return primary_players + secondary_players
    num_required_secondary = num_required - len(primary_players)
    secondary_players_sample = random.sample(secondary_players, num_required_secondary)
    return primary_players + secondary_players_sample


def assign_players_to_teams(players: Set[Player]) -> List[Team]:
    # Find the minimum number of teams required. At most we have 4 fills.
    total_teams = math.ceil(len(players) / 5)

    # assign roles to the teams in this order
    # after each step, the scores are ideally approximately the same.
    players_to_select = list(players)
    player_groups: Optional[List[_PlayerGroup]] = None
    for player_role in [PlayerRole.QUEEN, PlayerRole.SPEED, PlayerRole.OBJECTIVE, PlayerRole.VANILLA]:
        players_for_role = _select_player_role(players_to_select, total_teams, player_role)
        # TODO what do we do if there are fills? possibly: pick someone specific to be a fill, or pick most common
        #  score and anybody with that score can fill. or, average all queen scores and let anybody fill (has more
        #  variability). fills not a problem with the current test data

        players_to_select = _remove_subset_from_players(players_to_select, players_for_role)

        if not _should_find_fill(player_role):
            assert len(players_for_role) == total_teams, "fills not yet implemented for roles"
        else:
            # If fills are needed, find any random player remaining and assign them their primary role.
            subsampled_players = random.sample(players_to_select, total_teams - len(players_for_role))
            subsampled_assignment = _players_to_primary_role_assignment(subsampled_players)
            players_for_role.extend(subsampled_assignment)
            players_to_select = _remove_subset_from_players(players_to_select, subsampled_assignment)

        print(f"Got players for role {player_role}: {players_for_role}")

        if player_groups is None:
            # If player groups are currently None, then initialize to the current players, sorted lowest->highest score
            player_groups = sorted(list(_PlayerGroup([elem]) for elem in players_for_role), key=_sort_fn)
        else:
            # If player groups not None, then sort the current groups to ensure lowest->highest score
            # The selected players for the role are reverse sorted, highest->lowest and we group the players by
            # the position in the list. E.g., strongest player is added to weakest group, and weakest player is
            # assigned to the strongest group.
            player_groups = sorted(player_groups, key=_sort_fn)
            players_for_role = sorted(list(players_for_role), key=_sort_fn, reverse=True)
            for ind, group in enumerate(player_groups):
                group.players.append(players_for_role[ind])

    # The remaining players are what we can get.
    remaining_players = sorted(_players_to_primary_role_assignment(players_to_select), key=_sort_fn)
    assert player_groups is not None
    player_groups = sorted(player_groups, key=_sort_fn, reverse=True)
    print([group.score for group in player_groups])
    for ind, assignment in enumerate(remaining_players):
        player_groups[ind].players.append(assignment)

    teams = [Team(group.players) for group in player_groups]
    return teams
