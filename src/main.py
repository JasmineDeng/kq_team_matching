import random

import click

from assignment import assign_players_to_teams
from find_fills import find_fills
from load_data import load_data


@click.command()
@click.option("--file-path", "-f", type=str, required=True, help="File path to csv file with player rankings.")
def cli(file_path: str) -> None:
    all_players = load_data(file_path)
    teams = assign_players_to_teams(all_players)
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

    finalized_teams = [t.total_score for t in teams if not t.needs_fill]
    finalized_score = sum(finalized_teams) / len(finalized_teams)

    for t in teams:
        if t.needs_fill:
            possible_fills = find_fills(t, all_players, finalized_score)
            print(f"For team {t.team_name}, possible fills: {possible_fills}")
            subsample = random.sample(possible_fills, 2)
            print(f"Randomly chosen two fills: {subsample}")


if __name__ == "__main__":
    cli()
