from typing import Set, Optional, List
from data_types import Player, Team, PlayerRole, PlayerAssignment, BasePlayerAssignment
import math
import random
from typing import Tuple


def _sort_fn(assigned_player: BasePlayerAssignment) -> Tuple[int, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.score, random.random()


def _warrior_sort_fn(player: Player) -> Tuple[int, int, float]:
    # Lower number if the player is a warrior, so if we sort ascending, it appears first
    warrior_int: int
    if player.ranking.primary_role == PlayerRole.VANILLA:
        warrior_int = 0
    else:
        warrior_int = 1
    return warrior_int, player.ranking.primary_ranking, random.random()


def _remove_assignment_from_players(all_players: Set[Player], to_remove: Set[PlayerAssignment]) -> Set[Player]:
    to_remove_names = {p.player.name for p in to_remove}
    to_return = {p for p in all_players if p.name not in to_remove_names}
    return to_return


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


def _players_to_assignment(players: Set[Player], role: PlayerRole) -> Set[PlayerAssignment]:
    return {PlayerAssignment(player=p, assigned_role=role) for p in players}


def _select_player_role(players: Set[Player], num_required: int, role: PlayerRole) -> Set[PlayerAssignment]:
    """Select players for the provided role.

    Primary players denote players who have the role as their primary role, secondary players denote players who have
    the role as their secondary role.

    If len(primary_players) >= num_required, then remove a random subset until we have the correct amount.
    If len(primary_players) + len(secondary_players) >= num_required, then remove a random subset of secondary
        players until we have the correct amount.
    Else, return all primary/secondary players, but there must be fills.
    """
    primary_players = [p for p in players if p.ranking.primary_role == role]
    secondary_players = [p for p in players if p.ranking.secondary_role == role]
    if len(primary_players) >= num_required:
        return _players_to_assignment(set(random.sample(primary_players, num_required)), role)
    if len(primary_players) + len(secondary_players) < num_required:
        return _players_to_assignment(set(primary_players + secondary_players), role)
    num_required_secondary = num_required - len(primary_players)
    secondary_players_sample = random.sample(secondary_players, num_required_secondary)
    selected_players_set = set(primary_players + secondary_players_sample)
    return _players_to_assignment(selected_players_set, role)


def assign_players_to_teams(players: Set[Player]) -> Set[Team]:
    # Find the minimum number of teams required. At most we have 4 fills.
    total_teams = math.ceil(len(players) / 5)

    # assign roles to the teams in this order
    # after each step, the scores are ideally approximately the same.
    players_to_select = players
    player_groups: Optional[List[_PlayerGroup]] = None
    for player_role in [PlayerRole.QUEEN, PlayerRole.SPEED, PlayerRole.OBJECTIVE]:
        players_for_role = _select_player_role(players_to_select, total_teams, player_role)
        # TODO what do we do if there are fills? possibly: pick someone specific to be a fill, or pick most common
        #  score and anybody with that score can fill. or, average all queen scores and let anybody fill (has more
        #  variability). fills not a problem with the current test data
        assert len(players_for_role) == total_teams, "fills not yet implemented for roles"
        print(f"Got players for role {player_role}: {players_for_role}")

        players_to_select = _remove_assignment_from_players(players_to_select, players_for_role)
        print(len(players_to_select))

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

    # The last two players matter the least. We prefer assigning maximum 2 main objective runners per team, so try
    # to sort the list such that a warrior position is sorted first, lowest->highest score
    # If there are <5 primary warriors left, a team may have up to 3 objective runners.
    players_to_select = sorted(players_to_select, key=_warrior_sort_fn)
    # Extend the remaining required players by fills
    # Do assignment by sorting so the teams are sorted high->low score
    # The remaining players are sorted low->high. Assign the last half (who should be mostly primary warriors)
    for i in range(2):
        remaining_players = players_to_select[i * total_teams: (i + 1) * total_teams]
        print(remaining_players)
        player_groups = sorted(player_groups, key=_sort_fn, reverse=True)
        print([group.score for group in player_groups])
        for ind, remaining_player in enumerate(remaining_players):
            player_groups[ind].players.append(PlayerAssignment(remaining_player, assigned_role=remaining_player.ranking.primary_role))

    teams = [Team(group.players) for group in player_groups]
    return set(teams)
