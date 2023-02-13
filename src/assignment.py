from typing import Set
from data_types import Player, Team, PlayerRole, PlayerAssignment, BasePlayerAssignment
import math
import random
from typing import Tuple


def _sort_fn(assigned_player: BasePlayerAssignment) -> Tuple[int, float]:
    """Return the score and a random number.

    The second random number will be used to break ties randomly.
    """
    return assigned_player.score, random.random()


class _PlayerGroup(BasePlayerAssignment):
    def __init__(self, players: Set[PlayerAssignment]) -> None:
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
    """Select queens.

    If len(primary_queens) >= num_required, then remove a random subset until we have the correct amount.
    If len(primary_queens) + len(secondary_queens) >= num_required, then remove a random subset of secondary
        queens until we have the correct amount.
    Else, return all queens, but there must be fills.
    """
    primary_players = [p for p in players if p.ranking.primary_role == role]
    secondary_players = [p for p in players if p.ranking.secondary_role == role]
    if len(primary_players) >= num_required:
        return _players_to_assignment(set(random.sample(primary_players, num_required)), role)
    if len(primary_players) + len(secondary_players) < num_required:
        return _players_to_assignment(set(primary_players + secondary_players), role)
    num_required_secondary = num_required - len(primary_players)
    secondary_players_sample = random.sample(secondary_players, num_required_secondary)
    queen_set = set(primary_players + secondary_players_sample)
    return _players_to_assignment(queen_set, role)


def assign_players_to_teams(players: Set[Player]) -> Set[Team]:
    total_teams = math.ceil(len(players) / 5)
    # Select queens
    queens = _select_player_role(players, total_teams, PlayerRole.QUEEN)
    # TODO what do we do if there are fills? possibly: pick someone specific to be a fill, or pick most common
    #  score and anybody with that score can fill. or, average all queen scores and let anybody fill (has more variability)
    #  fills not a problem with the current test data
    assert len(queens) == total_teams, "fills not yet implemented for queen"
    print(f"Got queens: {queens}")
    # Next, select speed warriors. We want all the ranking scores to be approximately the same after this step,
    # since if the queen is weaker we should compensate with a stronger speed warrior.
    speed_warriors = _select_player_role(players, total_teams, PlayerRole.SPEED)
    # TODO what do we do if there are fills?
    assert len(speed_warriors) == total_teams, "fills not yet implemented for speed warriors"
    print(f"Got speed warriors: {speed_warriors}")

    queens = sorted(list(queens), key=_sort_fn)
    speed_warriors = sorted(list(speed_warriors), key=_sort_fn, reverse=True)

    tentative_assignment = sorted([_PlayerGroup(set(elem)) for elem in zip(queens, speed_warriors)], key=_sort_fn)
    print(tentative_assignment)

    objective = sorted(_select_player_role(players, total_teams, PlayerRole.OBJECTIVE), key=_sort_fn)
    assert len(speed_warriors) == total_teams, "fills not yet implemented for objective runners"
    print(f"Got objective runners: {objective}")
    for ind, obj in enumerate(objective):
        tentative_assignment[ind].players.add(obj)

    print(tentative_assignment)
    print([e.score for e in tentative_assignment])

