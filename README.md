# kq_team_matching

## Setup 

To setup the project, run `./setup.sh`.

Once you have run setup, you can enter the virtualenv by doing `kq_env`.

If you encounter errors about missing packages, make sure you are in the virtualenv.

If you encounter errors about a missing directory `src`, you need to ensure your `PYTHONPATH`
environment variable contains `/path/to/kq_team_maching`.

Note the script assumes you are running on a Macbook and have Python3.11 installed.
If you do not have Python3.11, visit https://www.python.org/downloads/macos/ to download the latest release.

## Assigning teams

To do a player assignment, after setting up and entering the virtualenv, enter the `kq_team_matching/src` directory and run:
```commandline
python main.py assign -f data/test_data.csv
```

If you want to recompute a preexisting assignment, you can run:
```commandline
python main.py recompute -r data/test_data.csv
```
This by default recomputes the most recently computed assignment (which is determined
by the timestamp in the filename under `data/league_night`). Note that when editing a preexisting
team assignment, the blank lines ",,,," denoting Phils are important and should not be deleted
in the process of swapping players around. It ialso important to preserve team composition, i.e.,
a team must always have a Queen, an Objective, and a Speed player.