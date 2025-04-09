import logging

import click

from src.load_data import load_data
from src.visualization.scores import role_score_histogram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_matplotlib_installed() -> bool:
    try:
        return True
    except ModuleNotFoundError:
        return False


@click.command("vis-scores")
@click.option(
    "--file-path",
    "-f",
    type=str,
    required=True,
    help="File path to csv file with player rankings.",
)
def vis_scores(file_path: str) -> None:
    if not _is_matplotlib_installed():
        logger.error("Matplotlib is not installed. Please install it from `vis-requirements.txt` to visualize scores.")
        return

    player_infos = load_data(file_path)
    role_score_histogram(player_infos.players)


if __name__ == "__main__":
    vis_scores()
