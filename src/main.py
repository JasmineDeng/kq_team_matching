import datetime
import os
from typing import Any

import click

from src.assignment import PlayerSamplingStrategy, assign_players_to_teams
from src.cli_utils import prompt_yes_no
from src.data_types.team import TeamComposition, read_teams_from_csv, roles_to_average_score, write_teams_to_csv
from src.find_fills import find_fills
from src.load_data import load_attendance, load_data, load_exclusion_set, load_inclusion_set
from src.visualization.scores import primary_role_score_histogram

DATETIME_FORMAT = "%Y-%m-%d_%H:%M:%S"


def _to_player_sampling_enum(_: Any, __: Any, value: str) -> PlayerSamplingStrategy:
    return PlayerSamplingStrategy[value]


def _parse_datetime(value: str) -> datetime.datetime | None:
    try:
        no_ext_filename = value.rsplit(".")[0]
        return datetime.datetime.strptime(no_ext_filename, DATETIME_FORMAT)
    except Exception:
        return None


@click.group()
def cli() -> None:
    ...


@cli.command("assign")
@click.option(
    "--file-path",
    "-f",
    type=str,
    required=True,
    help="File path to csv file with player rankings.",
)
def assign(file_path: str) -> None:
    player_infos = load_data(file_path)
    player_pool = load_attendance("data/attendance.csv", player_infos)

    inclusion_set = load_inclusion_set("data/inclusion_set.csv", player_pool)
    exclusion_set = load_exclusion_set("data/exclusion_set.csv", player_infos)
    print(f"Loaded exclusion set: {exclusion_set}")
    teams = assign_players_to_teams(player_pool, inclusion_set, exclusion_set)
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
    print(f"All weighted scores (in order): {[t.total_weighted_score for t in teams]}")

    averages = roles_to_average_score(player_pool.players)
    print(f"Summed average: {TeamComposition.total_score_for_ranking(averages)}")
    print(f"Summed weighted average: {TeamComposition.weighted_score_for_ranking(averages)}")

    for t in teams:
        if t.needs_fill:
            possible_fills = find_fills(t, player_pool.players, teams)
            print(f"For team {t.team_name}, possible fills: {possible_fills}")
            subsample = possible_fills[:2]
            print(f"Randomly chosen two fills: {subsample}")

    # Print again, without scores
    print("\n\n\n--------------------------\n\n\n")
    print("Teams, without scores: \n")
    for t in teams:
        print(t.format(hide_scores=True))

    print("Save the teams to a csv?")
    if prompt_yes_no():
        date_str = datetime.datetime.now().strftime(DATETIME_FORMAT)
        output_file_name = os.path.join(os.path.dirname(__file__), "data", "league_night", f"{date_str}.csv")
        write_teams_to_csv(output_file_name, teams)


@cli.command("recompute")
@click.option("--ranking-file-path", "-r", type=str, required=True, help="File path to csv file with player rankings.")
@click.option(
    "--file-path",
    "-f",
    type=str,
    default=None,
    help="File path to csv file with teams. If None, take the most recent team from data/league_night.",
)
def recompute(ranking_file_path: str, file_path: str | None) -> None:
    if file_path is None:
        league_night_dir = os.path.join(os.path.dirname(__file__), "data", "league_night")
        all_league_night_csvs = os.listdir(league_night_dir)
        csv_dates = [csv_file for csv_file in all_league_night_csvs if _parse_datetime(csv_file) is not None]
        file_path = os.path.join(os.path.dirname(__file__), "data", "league_night", sorted(csv_dates)[-1])

    # TODO: make the lowercase more consistent
    players = load_data(ranking_file_path)
    teams = read_teams_from_csv(file_path, players)

    for t in teams:
        print(t)

    print("Overwrite the existing file with new data? If no, then the current scores are not saved.")
    if prompt_yes_no():
        write_teams_to_csv(file_path, teams)


@cli.command("vis-scores")
@click.option(
    "--file-path",
    "-f",
    type=str,
    required=True,
    help="File path to csv file with player rankings.",
)
def vis_scores(file_path: str) -> None:
    player_infos = load_data(file_path)
    all_players = load_attendance("data/attendance.csv", player_infos)
    primary_role_score_histogram(all_players.players)


if __name__ == "__main__":
    cli()
