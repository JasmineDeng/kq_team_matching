import math
import random
from typing import Callable, Dict, List, NamedTuple, Optional, Set, Tuple

from src.data_types.player import BasePlayerAssignment, Player, PlayerAssignment, PlayerRole
from src.data_types.player_pool import PlayerPool
from src.data_types.team import Team, TeamComposition, roles_to_average_score
from src.sampling import PlayerSamplingStrategy, get_players_for_role, sample_players


class _PlayerGroup(BasePlayerAssignment):
    def __init__(self, players: List[PlayerAssignment], role_averages: Dict[PlayerRole, float]) -> None:
        # Use a list for the players because order *does* matter. If there are too many queens, for ex., a team
        # could have multiple queens, but we assign queens *first* so the first queen in the list should be the
        # team's queen.
        self.players = players
        self._role_averages = role_averages

    @property
    def score(self) -> float:
        # Score represents the players CURRENTLY on the team and the average scores of players NOT YET ASSIGNED
        # onto the team
        existing_score = sum(p.score for p in self.players)
        average_scores = sum(
            self._role_averages[role] for role in TeamComposition.remaining_roles_required(self.players)
        )
        return existing_score + average_scores

    @property
    def weighted_score(self) -> float:
        # Weighted score represents the players CURRENTLY on the team and the average scores of players NOT YET ASSIGNED
        # onto the team
        existing_score = sum(p.weighted_score for p in self.players)
        average_scores = sum(
            Player.weighted_score_for_role(role, self._role_averages[role])
            for role in TeamComposition.remaining_roles_required(self.players)
        )
        return round(existing_score + average_scores, 3)

    def weighted_score_excluding_role(self, role: PlayerRole) -> float:
        remaining_roles_required = TeamComposition.remaining_roles_required(self.players)
        if role not in remaining_roles_required:
            raise ValueError(
                f"Cannot exclude role in score calculation for role that is needed on the team anymore,"
                f" remaining: {remaining_roles_required}"
            )
        existing_score = sum(p.weighted_score for p in self.players)
        # will remove only the *first* instance of the role, which we want in case there are duplicate roles, ex. flex
        remaining_roles_required.remove(role)
        average_scores = sum(
            Player.weighted_score_for_role(role, self._role_averages[role]) for role in remaining_roles_required
        )
        return round(existing_score + average_scores, 3)

    def __str__(self) -> str:
        return f"players: {_player_to_names([p.player for p in self.players])}, score: {self.score}, weighted {self.weighted_score}\n"

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


def _get_sort_by_role_score_fn(role: PlayerRole) -> Callable[[Player], float]:
    def _sort_fn(player: Player) -> float:
        return player.ranking[role]

    return _sort_fn


def _player_to_names(players: List[Player]) -> List[str]:
    return [p.name for p in players]


def _assignment_to_names(assignments: list[PlayerAssignment]) -> List[str]:
    return [a.player.name for a in assignments]


def _validate_required_roles(
    num_teams: int, total_players: list[Player], inclusion_set: list[list[PlayerAssignment]]
) -> None:
    """Validate that for each role that does not allow fills, we have enough players.

    Create and print a helpful error string that will indicate who was assigned the role, if they are in an inclusion
    set, or if they were assigned the role but that role was removed due to being in an inclusion set.
    """
    all_inclusion_set_names = _assignment_to_names(sum(inclusion_set, []))
    for required_role in set(TeamComposition.roles):
        if TeamComposition.role_allows_fill(required_role):
            continue

        # Get the number of players in this role in an inclusion set.
        assignments_in_inclusion = []
        overriden_assignments_in_inclusion = []
        for player_assignment_list in inclusion_set:
            assignments = [p for p in player_assignment_list if p.assigned_role == required_role]
            assignments_in_inclusion.extend(assignments)
            # Get the players who had the primary role as the required role, but it was overriden in the inclusion set.
            overriden_assignments = [
                p
                for p in player_assignment_list
                if p.player.primary_role == required_role and p.assigned_role != required_role
            ]
            overriden_assignments_in_inclusion.extend(overriden_assignments)

        assignments_for_role = get_players_for_role(total_players, required_role)
        # These are all players for the role who are *not* on an inclusion set. We must remove players in inclusion
        # sets and check that separately, since the inclusion set role overrides the default role.
        filtered_assignments_for_inclusion = [
            assignment for assignment in assignments_for_role if assignment.player.name not in all_inclusion_set_names
        ]
        # These are all the players with the assigned role, whether or not they are in an inclusion set.
        total_assignments_for_role = filtered_assignments_for_inclusion + assignments_in_inclusion

        # Either:
        # 1. We require an exact count and the number of players is not equal to the number of teams.
        # 2. We don't require an exact count, but the role does not allow fills, and the number of players is less than
        #   the number of teams.
        if not TeamComposition.is_num_assignments_valid(required_role, num_teams, len(total_assignments_for_role)):
            too_many_players = len(total_assignments_for_role) > num_teams
            help_str = "Remove" if too_many_players else "Add"
            add_help_str = (
                f"{', '.join(_assignment_to_names(overriden_assignments_in_inclusion))} player(s) "
                f"previously had role {required_role} but were overriden because they are in an inclusion set.\n"
                if overriden_assignments_in_inclusion
                else "No one's role was overriden in an inclusion set.\n"
            )
            diff = abs(len(total_assignments_for_role) - num_teams)
            inclusion_set_str = (
                f"{', '.join(_assignment_to_names(assignments_in_inclusion))} player(s) are assigned to an inclusion set"
                if assignments_in_inclusion
                else "No one with that role is in an inclusion set"
            )
            raise ValueError(
                f"For role {required_role}, there are {len(total_assignments_for_role)} player(s), but {num_teams} "
                f"teams. {inclusion_set_str}, and in total, "
                f"we have: {', '.join(_assignment_to_names(total_assignments_for_role))} player(s).\n"
                f"{add_help_str if not too_many_players else ''}"
                f"{help_str} {diff} player(s) with role {required_role}."
            )


def _remove_subset_from_players(all_players: List[Player], to_remove: List[PlayerAssignment]) -> List[Player]:
    to_remove_names = {p.player.name for p in to_remove}
    to_return = [p for p in all_players if p.name not in to_remove_names]
    return to_return


def _remove_subset_from_assignments(
    all_assignments: List[PlayerAssignment], to_remove: List[PlayerAssignment]
) -> List[PlayerAssignment]:
    to_remove_names = {p.player.name for p in to_remove}
    to_return = [p for p in all_assignments if p.player.name not in to_remove_names]
    return to_return


def _players_to_assignment(players: List[Player], role: PlayerRole) -> List[PlayerAssignment]:
    return [PlayerAssignment(player=p, assigned_role=role) for p in players]


def _contains_exclusion_set(players: list[Player], exclusion_set: list[list[Player]]) -> Optional[list[Player]]:
    """Check if the set of players violates an exclusion set."""
    players_to_check = PlayerPool(players)
    for exclusion in exclusion_set:
        exclusion_pool = PlayerPool(exclusion)
        if players_to_check.contains_pool(exclusion_pool):
            return exclusion
    return None


def _get_match_exclusion_set_players(
    all_players: List[Player], group: _PlayerGroup, exclusion_set: list[list[Player]]
) -> Set[str]:
    """Given a list of all players and a group of players, return all players who CANNOT be put on the team."""
    to_exclude: Set[str] = set()
    for player in all_players:
        possible_team = [p.player for p in group.players] + [player]
        if _contains_exclusion_set(possible_team, exclusion_set) is not None:
            to_exclude.add(player.name)
    return to_exclude


def _get_player_for_ideal_score(
    player_assignments: List[PlayerAssignment],
    ideal_score: float,
    to_exclude: Optional[Set[str]] = None,
) -> Optional[PlayerAssignment]:
    """Get a player with the given role, not in the exclusion set, with a score as close as possible to the ideal."""
    if to_exclude is not None:
        players_minus_exclusion = [player for player in player_assignments if player.player.name not in to_exclude]
    else:
        players_minus_exclusion = player_assignments
    # Get as close to the ideal score as possible
    sorted_players = sorted(players_minus_exclusion, key=lambda p: abs(ideal_score - p.weighted_score))
    print([abs(ideal_score - p.weighted_score) for p in sorted_players])
    if len(sorted_players) == 0:
        return None
    return sorted_players[0]


def _compute_ideal_score_for_group(
    groups: List[_PlayerGroup],
    groups_to_skip: List[_PlayerGroup],
    players: List[Player],
    role: PlayerRole,
    team_average_score: float,
) -> Optional[Dict[_PlayerGroup, float]]:
    """Compute the ideal score for the group, given remaining players.

    Ignoring the exclusion set, sample all players using the provided strategy.

    Sort the groups from low to high, and sort the players for the role from high to low. Assignment would normally
    happen (ignoring exclusion set) by then zipping the groups together, i.e., strongest player to weakest group,
    and vice versa. Therefore, the player that would have been assigned to the group is the 'ideal score' the player
    *actually* assigned should have.

    The *actually* assigned player may differ from the ideal player once exclusion sets are accounted for.
    """
    possible_players_pre_exclusion = sorted(
        [PlayerAssignment(player=p, assigned_role=role) for p in players],
        key=_sort_by_score_fn,
        reverse=True,
    )
    # If no possible players are found, the later code cannot find any either and will skip assignment (meaning we
    # need fills). But that will be handled later.
    if len(possible_players_pre_exclusion) == 0:
        return None

    # These are the groups to skip, aka they have assigned someone for the role and their scores are set.
    set_group_scores = [group.weighted_score for group in groups_to_skip]
    average_set_group_score = (
        sum(set_group_scores) / len(set_group_scores) if len(set_group_scores) > 0 else team_average_score
    )

    ideal_scores = {}
    for group in groups:
        score = average_set_group_score - group.weighted_score_excluding_role(role)
        ideal_scores[group] = score
    return ideal_scores


def _assign_players_with_exclusion_set(
    groups_to_assign: List[_PlayerGroup],
    groups_to_skip: List[_PlayerGroup],
    possible_players: List[Player],
    role: PlayerRole,
    exclusion_set: list[list[Player]],
    role_averages: Dict[PlayerRole, float],
    use_uniform_sampling: bool,
) -> List[PlayerAssignment]:
    """Assign players to teams, accounting for the exclusion set.

    The selected players for the role are reverse sorted, highest->lowest, and we group the players by
    the position in the list. E.g., the strongest player is added to the weakest group, and weakest player is
    assigned to the strongest group.

    However, since we have an exclusion set, we actually assign players to exclusion sets first, to avoid
    assigning possibly the players we need to satisfy the constraint elsewhere. To avoid imbalancing, for
    each team with an exclusion set, we have an 'ideal score' that the player should satisfy.

    For non-exclusion-set teams, assignment goes as normal, where we sample players and assign the
    highest->lowest and vice versa.

    Returns the set of players that were assigned, so they can be removed from further assignment consideration.
    """
    if len(possible_players) == 0:
        return []

    groups_to_assign = sorted(groups_to_assign, key=_sort_by_score_fn)
    assigned_players = []

    groups_with_exclusion = []
    groups_without_exclusion = []
    for group in groups_to_assign:
        group_exclusion_set = _get_match_exclusion_set_players(possible_players, group, exclusion_set)
        print(f"Excluding {group_exclusion_set} for group {group}")
        if len(group_exclusion_set) > 0:
            groups_with_exclusion.append(_GroupWithExclusions(group=group, to_exclude=group_exclusion_set))
        else:
            groups_without_exclusion.append(group)
    # Sort so that the group with the most exclusion sets is assigned first (to reduce the chances of not being
    # able to assign any teams)

    # First sort by score. Doing both of these sorts means that we try to handle the group with the most exclusion
    # sets, but if that number is tied, we start by looking at the lowest-score team first.
    # Anecdotally, it seems to work better by examining the lower-score teams first.
    groups_with_exclusion = sorted(groups_with_exclusion, key=lambda g: g.group.score)
    groups_with_exclusion = sorted(groups_with_exclusion, key=lambda g: len(g.to_exclude), reverse=True)

    # Find the ideal score that the player should have
    ideal_scores = _compute_ideal_score_for_group(
        groups_to_assign,
        groups_to_skip,
        possible_players,
        role,
        TeamComposition.weighted_score_for_ranking(role_averages),
    )
    if ideal_scores is None:
        raise ValueError(
            f"Failed to find ideal scores given {possible_players} and role {role} with {len(groups_to_assign)} groups"
        )
    # Assign the teams with excluded people first
    for exclude_group in groups_with_exclusion:
        ideal_score = ideal_scores[exclude_group.group]
        assignment = _get_player_for_ideal_score(
            get_players_for_role(possible_players, role),
            ideal_scores[exclude_group.group],
            to_exclude=exclude_group.to_exclude,
        )
        if assignment is None:
            print(f"Skipping assignment for {exclude_group}, role {role}, ideal score {ideal_score}")
            continue
        exclude_group.group.players.append(assignment)
        assigned_players.append(assignment)
        possible_players = _remove_subset_from_players(possible_players, [assignment])
        print(
            f"Excluding {exclude_group.to_exclude}, picked {assignment} for team {exclude_group.group}, "
            f"ideal score: {ideal_score}"
        )
    if len(groups_without_exclusion) == 0:
        return assigned_players

    sampling_strategy = (
        PlayerSamplingStrategy.RANDOM if not use_uniform_sampling else PlayerSamplingStrategy.UNIFORM_SCORE
    )
    sampled_players = sample_players(sampling_strategy, possible_players, len(groups_without_exclusion), role)
    # Anecdotally, it seems to work better to sort by the player scores in this order.
    sampled_players = sorted(sampled_players, key=_sort_by_score_fn)
    groups_without_exclusion = sorted(groups_without_exclusion, key=_sort_by_score_fn, reverse=True)
    ind = 0
    for ind, player in enumerate(sampled_players):
        groups_without_exclusion[ind].players.append(player)
        assigned_players.append(player)

    skipped_groups = groups_without_exclusion[ind + 1 :]
    if len(skipped_groups) > 0:
        print(f"fills required for: {skipped_groups}")
    return assigned_players


def assign_players_to_teams(
    player_pool: PlayerPool,
    inclusion_set: List[List[PlayerAssignment]],
    exclusion_set: list[list[Player]],
    use_uniform_sampling: bool = False,
) -> List[Team]:
    # Find the minimum number of teams required.
    total_teams = math.ceil(player_pool.num_players / 5)

    # Get the averages per role
    role_averages = roles_to_average_score(player_pool.players)
    players_to_select = player_pool.players
    # Remove the people in the inclusion set from the overall set, and also check it does not violate the exclusion set.
    for inclusion in inclusion_set:
        excluded = _contains_exclusion_set([p.player for p in inclusion], exclusion_set)
        if excluded is not None:
            raise ValueError(f"Can't assign teams when inclusion set: {inclusion} violates exclusion set: {excluded}")
        players_to_select = _remove_subset_from_players(players_to_select, inclusion)

    # Validate that all the roles that do not allow fills are satisfied.
    _validate_required_roles(total_teams, players_to_select, inclusion_set)

    # Create the initial player groups, account for the inclusion set
    num_empty_teams = total_teams - len(inclusion_set)
    player_groups = [_PlayerGroup(inclusion, role_averages) for inclusion in inclusion_set] + [
        _PlayerGroup([], role_averages) for _ in range(num_empty_teams)
    ]

    for player_role in TeamComposition.roles:
        # Some groups, because of the inclusion set, will already have a player assigned for this role.
        # In that case, we should skip it and not assign another player.
        groups_to_skip = [
            group
            for group in player_groups
            if player_role not in TeamComposition.remaining_roles_required(group.players)
        ]
        print(f"Assigning {player_role.name}, skipping groups: {groups_to_skip}")
        # Then remove them from the player group list
        groups_to_assign = [
            group for group in player_groups if player_role in TeamComposition.remaining_roles_required(group.players)
        ]
        print(f"Assigning {player_role.name} for groups {groups_to_assign}")

        # if you can play speed, you can flex
        valid_roles = {player_role} if player_role != PlayerRole.FLEX else {PlayerRole.FLEX, PlayerRole.SPEED}
        players_for_role = [player for player in players_to_select if player.primary_role in valid_roles]

        assigned_players = _assign_players_with_exclusion_set(
            groups_to_assign,
            groups_to_skip,
            players_for_role,
            player_role,
            exclusion_set,
            role_averages,
            use_uniform_sampling,
        )
        players_to_select = _remove_subset_from_players(players_to_select, assigned_players)

    if len(players_to_select) > 0:
        raise ValueError(
            f"Some people were not assigned! like: {[(p.name, p.primary_role.name) for p in players_to_select]}"
        )

    teams = [Team(group.players) for group in player_groups]
    return teams
