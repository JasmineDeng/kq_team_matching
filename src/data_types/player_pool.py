from typing import List, Set

from src.data_types.player import Player

NAME_ALIASES: List[Set[str]] = [
    {"Matt", "Matthew", "Matt Wu"},
    {"Chris", "Blue Chris"},
    {"Maureen", "Mo"},
    {"Blee", "Brian Lee"},
    {"BrianM", "Brian M"},
    {"DerekM", "Derek M"},
]
"""A list of aliases that people can be called by.

The actual name comparison is case- and whitespace-insensitive. I.e., 'Matt ', 'mAtt', and ' MATT ' are treated as the
same name.
"""


class PlayerPool:
    """A pool of players to assign to teams.

    In the 'pool', the lower-cased, whitespace-stripped name of the player is treated as the unique identifier. At a
    high level, the pool can be treated as a basic in-memory database of players, where we only index on name.
    """

    def __init__(self, players: list[Player], name_aliases: list[set[str]] | None = None) -> None:
        self._name_aliases = name_aliases or NAME_ALIASES

        all_names = set([p.name for p in players])
        if len(all_names) != len(players):
            raise ValueError(
                f"Duplicate player names found in player pool. Had {len(players)} players, but only {len(all_names)} unique, case-insensitive names. All names were: {[p.name for p in players]}"
            )
        # Store players in a dict with lowercase names/whitespace stripped names as keys
        self._name_to_players = {self._get_cleaned_key(p.name): p for p in players}
        # All the names, NOT processed.
        self._all_names = [p.name for p in players]

    def _get_aliased_key(self, name: str) -> str:
        """Process a name to be used as a key, with alias, in the player pool."""
        possible_alias = self._convert_alias_to_name(name)
        return possible_alias.lower().strip()

    def _get_cleaned_key(self, name: str) -> str:
        """Process a name to be used as a key in the player pool."""
        return name.lower().strip()

    @property
    def num_players(self) -> int:
        return len(self._name_to_players)

    @property
    def players(self) -> list[Player]:
        return list(self._name_to_players.values())

    def get_player(self, name: str) -> Player:
        name_key = self._get_aliased_key(name)
        if name_key not in self._name_to_players:
            raise ValueError(
                f"Could not find player with name {name}, possible aliases: {self._name_aliases} and possible names: {self._all_names}"
            )
        return self._name_to_players[name_key]

    def _convert_alias_to_name(self, name: str) -> str:
        """Given a set of all player names, check if the name is an alias and, if so, convert to the name in the set.

        This ensures that we refer to someone by only one name throughout the assignment, excluding nicknames.
        """
        name_key = self._get_cleaned_key(name)
        cleaned_aliases = [[self._get_cleaned_key(alias) for alias in alias_set] for alias_set in self._name_aliases]

        alias_list: list[str] = []
        for elem in cleaned_aliases:
            if name_key in elem:
                alias_list = elem
                break

        # All aliases should be cleaned, aka lowercase and stripped
        for alias in alias_list:
            if alias in self._name_to_players:
                return self._name_to_players[alias].name
        return name

    def contains_player(self, name: str) -> bool:
        """Return True if the player pool contains a player with the given name."""
        name_key = self._get_aliased_key(name)
        return name_key in self._name_to_players

    def contains_pool(self, other_pool: "PlayerPool") -> bool:
        """Return True if this pool contains all players in the other pool."""
        return all([self.contains_player(p.name) for p in other_pool.players])
