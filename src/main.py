import click

from src.assignment import PlayerSamplingStrategy, assign_players_to_teams
from src.data_types.team import TeamComposition, roles_to_average_score
from src.find_fills import find_fills
from src.load_data import load_attendance, load_data, load_exclusion_set, load_inclusion_set
from src.visualization.scores import primary_role_score_histogram


def _to_player_sampling_enum(_, __, value: str) -> PlayerSamplingStrategy:
    return PlayerSamplingStrategy[value]


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
    all_names = set(player_infos.keys())
    all_players = load_attendance("data/attendance.csv", player_infos)

    inclusion_set = load_inclusion_set("data/inclusion_set.csv", player_infos)
    exclusion_set = load_exclusion_set("data/exclusion_set.csv", all_names)
    teams = assign_players_to_teams(all_players, inclusion_set, exclusion_set)
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

    averages = roles_to_average_score(all_players)
    print(f"Summed average: {TeamComposition.total_score_for_ranking(averages)}")
    print(f"Summed weighted average: {TeamComposition.weighted_score_for_ranking(averages)}")

    for t in teams:
        if t.needs_fill:
            possible_fills = find_fills(t, all_players, teams)
            print(f"For team {t.team_name}, possible fills: {possible_fills}")
            subsample = possible_fills[:2]
            print(f"Randomly chosen two fills: {subsample}")

    # Print again, without scores
    print("\n\n\n--------------------------\n\n\n")
    print("Teams, without scores: \n")
    for t in teams:
        print(t.format(hide_scores=True))


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
    primary_role_score_histogram(all_players)


if __name__ == "__main__":
    cli()
