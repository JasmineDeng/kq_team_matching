import datetime
import os

import click

from src.assignment import assign_players_to_teams
from src.cli_utils import prompt_yes_no
from src.data_types.parseable_datetime import ParseableDatetime
from src.data_types.team import TeamComposition, read_teams_from_csv, roles_to_average_score, write_teams_to_csv
from src.find_fills import find_fills
from src.load_data import load_attendance, load_data, load_exclusion_set, load_inclusion_set


def _parse_datetime(value: str) -> datetime.datetime | None:
    try:
        no_ext_filename = value.rsplit(".")[0]
        return ParseableDatetime.deserialize(no_ext_filename).datetime_obj
    except Exception:
        return None


def _assign(
    file_path: str, auto_yes_prompt: bool, data_dir: str | None = None, output_dir: str | None = None
) -> str | None:
    """End-to-end assign teams, find fills, and output teams.

    Returns the file path to the output csv file, if it was saved.
    """
    default_dir = os.path.join(os.path.dirname(__file__), "data")
    if data_dir is None:
        data_dir_to_use = default_dir
        output_dir_to_use = data_dir_to_use
    else:
        data_dir_to_use = data_dir
        output_dir_to_use = default_dir

    player_infos = load_data(file_path)
    player_pool = load_attendance(
        os.path.join(data_dir_to_use, "attendance.csv"), player_infos, scores_csv_path=file_path
    )

    inclusion_set = load_inclusion_set(os.path.join(data_dir_to_use, "inclusion_set.csv"), player_infos)
    exclusion_set = load_exclusion_set(os.path.join(data_dir_to_use, "exclusion_set.csv"), player_infos)
    print(f"Loaded exclusion set: {', '.join([str(e) for e in exclusion_set])}")
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
    if auto_yes_prompt or prompt_yes_no():
        date_str = ParseableDatetime(datetime.datetime.now()).serialize()
        output_file_name = os.path.join(output_dir_to_use, "league_night", f"{date_str}.csv")
        write_teams_to_csv(output_file_name, teams)
        return output_file_name

    return None


def _recompute(file_path: str | None, ranking_file_path: str, auto_yes_prompt: bool) -> None:
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
    if auto_yes_prompt or prompt_yes_no():
        write_teams_to_csv(file_path, teams)


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
    _assign(file_path, auto_yes_prompt=False)


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
    _recompute(file_path, ranking_file_path, auto_yes_prompt=False)


if __name__ == "__main__":
    cli()
