import random

import click

from src.assignment import PlayerSamplingStrategy, assign_players_to_teams
from src.find_fills import find_fills
from src.load_data import load_attendance, load_data, load_exclusion_set


def _to_player_sampling_enum(_, __, value: str) -> PlayerSamplingStrategy:
    return PlayerSamplingStrategy[value]


@click.command()
@click.option(
    "--file-path",
    "-f",
    type=str,
    required=True,
    help="File path to csv file with player rankings.",
)
@click.option(
    "--player-sampling-strategy",
    "-s",
    type=click.Choice([e.name for e in PlayerSamplingStrategy]),
    default=PlayerSamplingStrategy.PRIORITIZE_HIGHEST_SCORE.name,
    callback=_to_player_sampling_enum,
    help="The sampling strategy to use.",
)
def cli(file_path: str, player_sampling_strategy: PlayerSamplingStrategy) -> None:

    player_infos = load_data(file_path)
    all_names = set(player_infos.keys())
    all_players = load_attendance("data/attendance.csv", player_infos)

    exclusion_set = load_exclusion_set("data/exclusion_set.csv", all_names)
    teams = assign_players_to_teams(all_players, exclusion_set)
    teams = sorted(teams, key=lambda t: t.total_score)
    for t in teams:
        print(t)

    summary_str = ""
    for t in teams:
        summary_str += f"{t.total_score}"
        if t.needs_fill:
            summary_str += "(F), "
        else:
            summary_str += ", "
    print(f"All scores (in order): {summary_str}")

    finalized_team_scores = [t.total_score for t in teams if not t.needs_fill]
    all_team_scores = [t.total_score for t in teams]
    # If no finalized teams, just aim for any average player, so long as they're all roughly equal in skill?
    if len(finalized_team_scores) > 0:
        finalized_score = sum(finalized_team_scores) / len(finalized_team_scores)
    else:
        print("No finalized teams, we can use any fill so long as the players are roughly equal in skill")
        finalized_score = sum(all_team_scores) / len(all_team_scores) + 2.5

    for t in teams:
        if t.needs_fill:
            possible_fills = find_fills(t, all_players, finalized_score)
            print(f"For team {t.team_name}, possible fills: {possible_fills}")
            subsample = random.sample(possible_fills, 2)
            print(f"Randomly chosen two fills: {subsample}")


if __name__ == "__main__":
    cli()
