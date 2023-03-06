# kq_team_matching

To setup the project, run `./setup.sh`.

Once you have run setup, you can enter the virtualenv by doing `kq_env`.

Note the script assumes you are running on a Macbook and have Python3.11 installed.
If you do not have Python3.11, visit https://www.python.org/downloads/macos/ to download the latest release.

To do a player assignment, after setting up and entering the virtualenv, enter the `kq_team_matching/src` directory and run:
```commandline
python main.py assign -f data/test_data.csv
```
