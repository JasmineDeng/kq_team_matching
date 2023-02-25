from typing import Set

from src.assignment import assign_players_to_teams
from src.data_types import Player, PlayerRanking, PlayerRole, Team
from src.sampling import PlayerSamplingStrategy


def _player_ranking_ignore_secondary(role: PlayerRole, ranking: int) -> PlayerRanking:
    secondary_role = PlayerRole.VANILLA if role != PlayerRole.VANILLA else PlayerRole.OBJECTIVE
    return PlayerRanking(primary_role=role, primary_ranking=ranking, secondary_role=secondary_role, secondary_ranking=1)


def _team_to_player_names(team: Team) -> Set[str]:
    return {p.player.name for p in team.players}


def test_exclusion_assign_players_to_teams() -> None:
    all_players = {
        # Team 1
        Player(name="A", ranking=_player_ranking_ignore_secondary(PlayerRole.QUEEN, 5)),
        Player(name="B", ranking=_player_ranking_ignore_secondary(PlayerRole.SPEED, 5)),
        Player(name="C", ranking=_player_ranking_ignore_secondary(PlayerRole.OBJECTIVE, 5)),
        Player(name="D", ranking=_player_ranking_ignore_secondary(PlayerRole.VANILLA, 5)),
        # Team 2
        Player(name="E", ranking=_player_ranking_ignore_secondary(PlayerRole.QUEEN, 4)),
        Player(name="F", ranking=_player_ranking_ignore_secondary(PlayerRole.SPEED, 4)),
        Player(name="G", ranking=_player_ranking_ignore_secondary(PlayerRole.VANILLA, 5)),
        Player(name="H", ranking=_player_ranking_ignore_secondary(PlayerRole.OBJECTIVE, 5)),
    }
    teams = assign_players_to_teams(all_players, PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE, [])
    assert len(teams) == 2
    # Sort by team name (queen name)
    teams.sort(key=lambda team: team.team_name)
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "F" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "B" in team_player_names

    teams = assign_players_to_teams(all_players, PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE, [{"A", "F"}])
    assert len(teams) == 2
    team_player_names = _team_to_player_names(teams[0])
    assert "A" in team_player_names and "B" in team_player_names
    team_player_names = _team_to_player_names(teams[1])
    assert "E" in team_player_names and "F" in team_player_names
