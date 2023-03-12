import math
import random
from collections import defaultdict
from typing import Callable, Dict, List, NamedTuple, Optional, Set, Tuple

from src.data_types.player import BasePlayerAssignment, Player, PlayerAssignment, PlayerRole
from src.data_types.team import Team, TeamComposition, roles_to_average_score
from src.sampling import PlayerSamplingStrategy, sample_players


class _PlayerGroup(BasePlayerAssignment):
    def __init__(self, players: List[PlayerAssignment], role_averages: Dict[PlayerRole, float]) -> None:
        # Use a list for the players because order *does* matter. If there are too many queens, for ex., a team
        # could have multiple queens, but we assign queens *first* so the first queen in the list should be the
        # team's queen.
        self.players = players
        self._role_averages = role_averages

    @property
    def remaining_roles_required(self) -> List[PlayerRole]:
        missing_roles = []
        current_role_counts = defaultdict(int)
        expected_role_counts = defaultdict(int)
        for p in self.players:
            current_role_counts[p.assigned_role] += 1
        for role in TeamComposition.roles:
            expected_role_counts[role] += 1
        for role, count in expected_role_counts.items():
            diff = count - current_role_counts[role]
            if diff < 0:
                player_names = [p.player.name for p in self.players]
                raise ValueError(
                    f"Should not be possible: team with players {player_names} has too many for role {role.name}, "
                    f"should have at most {count} but has {current_role_counts[role]}"
                )
            if diff > 0:
                missing_roles.extend([role] * diff)
        return missing_roles

    @property
    def score(self) -> float:
        # Score represents the players CURRENTLY on the team and the average scores of players NOT YET ASSIGNED
        # onto the team
        existing_score = sum(p.score for p in self.players)
        average_scores = sum(self._role_averages[role] for role in self.remaining_roles_required)
        return existing_score + average_scores

    @property
    def weighted_score(self) -> float:
        # Weighted score represents the players CURRENTLY on the team and the average scores of players NOT YET ASSIGNED
        # onto the team
        existing_score = sum(p.weighted_score for p in self.players)
        average_scores = sum(
            Player.weighted_score_for_role(role, self._role_averages[role]) for role in self.remaining_roles_required
        )
        return round(existing_score + average_scores, 3)

    def weighted_score_excluding_role(self, role: PlayerRole) -> Optional[float]:
        if role not in self.remaining_roles_required:
            raise ValueError(
                f"Cannot exclude role in score calculation for role that is needed on the team anymore,"
                f" remaining: {self.remaining_roles_required}"
            )
        existing_score = sum(p.weighted_score for p in self.players)
        remaining_roles_required = self.remaining_roles_required
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


def _make_missing_players_error_string(
    player_role: PlayerRole,
    num_teams: int,
    groups_to_skip: List[_PlayerGroup],
    selected_players: List[Player],
    all_players: List[Player],
) -> str:
    num_missing = num_teams - len(selected_players)
    current_player_names = _player_to_names(selected_players)
    strongest_players = sorted(
        [p for p in all_players if p.name not in current_player_names],
        key=_get_sort_by_role_score_fn(role=player_role),
        reverse=True,
    )
    strongest_players_str = ", ".join(
        [f"{p.name} ({player_role.name}={p.ranking[player_role]})" for p in strongest_players[:num_missing]]
    )
    assigned_players = [
        player.player for group in groups_to_skip for player in group.players if player.assigned_role == player_role
    ]
    assigned_player_names = _player_to_names(assigned_players)
    return (
        f"Role {player_role} is not allowed to have fills, please manually assign more people! Selected: "
        f"{', '.join(current_player_names)}.\n"
        f"Player(s): {', '.join(assigned_player_names)} already assigned to a team (via inclusion set), need "
        f"{num_missing} more player(s).\nMaybe assign: {strongest_players_str}?"
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


def _role_allows_fill(role: PlayerRole) -> bool:
    """Only flex is allowed to have fills."""
    return role == PlayerRole.FLEX


def _players_to_assignment(players: List[Player], role: PlayerRole) -> List[PlayerAssignment]:
    return [PlayerAssignment(player=p, assigned_role=role) for p in players]


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
    if len(sorted_players) == 0:
        return None
    return sorted_players[0]


def _compute_ideal_score_for_group(
    groups: List[_PlayerGroup],
    groups_to_skip: List[_PlayerGroup],
    players: List[Player],
    role: PlayerRole,
    role_average: float,
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
        [p.to_primary_role_assignment() for p in players if p.primary_role == role],
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
        sum(set_group_scores) / len(set_group_scores) if len(set_group_scores) > 0 else role_average
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
    exclusion_set: List[Set[str]],
    role_averages: Dict[PlayerRole, float],
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
        if len(group_exclusion_set) > 0:
            groups_with_exclusion.append(_GroupWithExclusions(group=group, to_exclude=group_exclusion_set))
        else:
            groups_without_exclusion.append(group)
    # Sort so that the group with the most exclusion sets is assigned first (to reduce the chances of not being
    # able to assign any teams)
    groups_with_exclusion = sorted(groups_with_exclusion, key=lambda g: len(g.to_exclude), reverse=True)

    # Find the ideal score that the player should have
    ideal_scores = _compute_ideal_score_for_group(
        groups_to_assign, groups_to_skip, possible_players, role, role_averages[role]
    )
    if ideal_scores is None:
        raise ValueError(
            f"Failed to find ideal scores given {possible_players} and role {role} with {len(groups_to_assign)} groups"
        )
    sampled_players = sample_players(
        PlayerSamplingStrategy.UNIFORM_SCORE,
        possible_players,
        len(groups_with_exclusion) + len(groups_without_exclusion),
        role,
    )
    # Assign the teams with excluded people first
    for exclude_group in groups_with_exclusion:
        ideal_score = ideal_scores[exclude_group.group]
        assignment = _get_player_for_ideal_score(
            sampled_players,
            ideal_score,
            to_exclude=exclude_group.to_exclude,
        )
        if assignment is None:
            print(f"Skipping assignment for {exclude_group}, role {role}, ideal score {ideal_score}")
            continue
        exclude_group.group.players.append(assignment)
        assigned_players.append(assignment)
        sampled_players = _remove_subset_from_assignments(sampled_players, [assignment])
        print(
            f"Excluding {exclude_group.to_exclude}, picked {assignment} for team {exclude_group.group}, "
            f"ideal score: {ideal_score}"
        )

    for group in groups_without_exclusion:
        player = _get_player_for_ideal_score(sampled_players, ideal_scores[group])
        print(f"picked {player} for ideal score {ideal_scores[group]}, role {role}, group {group}")
        if player is None:
            continue
        group.players.append(player)
        assigned_players.append(player)
        sampled_players = _remove_subset_from_assignments(sampled_players, [player])
    return assigned_players


def assign_players_to_teams(
    players: Set[Player], inclusion_set: List[List[PlayerAssignment]], exclusion_set: List[Set[str]]
) -> List[Team]:
    # Find the minimum number of teams required.
    total_teams = math.ceil(len(players) / 5)

    # Get the averages per role
    role_averages = roles_to_average_score(players)
    # Remove the people in the inclusion set from the overall set
    for inclusion in inclusion_set:
        players = _remove_subset_from_players(players, inclusion)

    # Create the initial player groups, account for the inclusion set
    players_to_select = list(players)
    num_empty_teams = total_teams - len(inclusion_set)
    player_groups = [_PlayerGroup(inclusion, role_averages) for inclusion in inclusion_set] + [
        _PlayerGroup([], role_averages) for _ in range(num_empty_teams)
    ]

    for player_role in TeamComposition.roles:
        # Some groups, because of the inclusion set, will already have a player assigned for this role.
        # In that case, we should skip it and not assign another player.
        groups_to_skip = [group for group in player_groups if player_role not in group.remaining_roles_required]
        print(f"Assigning {player_role.name}, skipping groups: {groups_to_skip}")
        # Then remove them from the player group list
        groups_to_assign = [group for group in player_groups if player_role in group.remaining_roles_required]
        print(f"Assigning {player_role.name} for groups {groups_to_assign}")

        # if you can play speed, you can flex
        valid_roles = {player_role} if player_role != PlayerRole.FLEX else {PlayerRole.FLEX, PlayerRole.SPEED}
        players_for_role = [player for player in players_to_select if player.primary_role in valid_roles]
        # We require queen/obj/speed to be assigned, raise and add helpful messages to assign more people.
        if len(players_for_role) < len(groups_to_assign) and not _role_allows_fill(player_role):
            error_str = _make_missing_players_error_string(
                player_role, len(groups_to_assign), groups_to_skip, players_for_role, players_to_select
            )
            raise ValueError(error_str)

        assigned_players = _assign_players_with_exclusion_set(
            groups_to_assign,
            groups_to_skip,
            players_for_role,
            player_role,
            exclusion_set,
            role_averages,
        )
        players_to_select = _remove_subset_from_players(players_to_select, assigned_players)

    if len(players_to_select) > 0:
        raise ValueError(
            f"Some people were not assigned! like: {[(p.name, p.primary_role.name) for p in players_to_select]}"
        )

    assert player_groups is not None
    teams = [Team(group.players) for group in player_groups]
    return teams
