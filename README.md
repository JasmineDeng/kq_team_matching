# kq_team_matching

## Setup 

To setup the project, run `./setup.sh`.

Once you have run setup, you can enter the virtualenv by doing `kq_env`.

If you encounter errors about missing packages, make sure you are in the virtualenv.

If you encounter errors about a missing directory `src`, you need to ensure your `PYTHONPATH`
environment variable contains `/path/to/kq_team_maching`.

Note the script assumes you are running on a Macbook and have Python3.11 installed.
If you do not have Python3.11, visit https://www.python.org/downloads/macos/ to download the latest release.

If you want to do any development in the repository, we have some precommit hooks! Install those by using
```commandline
pre-commit install
```

## Assigning teams

To do a player assignment, after setting up and entering the virtualenv, enter the `kq_team_matching/src` directory and run:
```commandline
python main.py assign -f data/test_data.csv
```
foo

Note that if you want to use a team composition with 3 flex warriors instead of the default, which is 2 flex warriors
and 1 speed warrior, pass in `--use-flex-role-for-speed` like below

```commandline
python main.py assign -f data/test_data.csv --use-flex-role-for-speed
```

If you want to recompute a preexisting assignment, you can run:
```commandline
python main.py recompute -r data/test_data.csv
```
This by default recomputes the most recently computed assignment (which is determined
by the timestamp in the filename under `data/league_night`). Note that when editing a preexisting
team assignment, the blank lines ",,,," denoting Phils are important and should not be deleted
in the process of swapping players around. It is also important to preserve team composition, i.e.,
a team must always have a Queen, an Objective, and a Speed player.

## Visualizing scores

Score distributions can be visualized in the `visualizations` directory, but require additionally
installed matplotlib, which is not included in requirements.txt by default.

For example, you can run the below command from the `visualizations` directory.

```commandline
python main.py vis-scores -f data/test_data.csv
```