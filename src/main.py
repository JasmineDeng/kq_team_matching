from load_data import load_data
import click
from assignment import assign_players_to_teams


@click.command()
@click.option("--file-path", "-f", type=str, required=True, help="File path to csv file with player rankings.")
def cli(file_path: str) -> None:
    assign_players_to_teams(load_data(file_path))


if __name__ == "__main__":
    cli()
