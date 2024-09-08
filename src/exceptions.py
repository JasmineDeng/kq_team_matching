from src.data_types.player import Player, PlayerAssignment, PlayerRole


def assignment_to_names(assignments: list[PlayerAssignment]) -> list[str]:
    return [a.player.name for a in assignments]


def player_to_names(players: list[Player]) -> list[str]:
    return [p.name for p in players]


class WrongNumberOfPlayersException(Exception):
    def __init__(
        self,
        *,
        expected_number: int,
        role: PlayerRole,
        players: list[PlayerAssignment],
        players_in_inclusion: list[PlayerAssignment],
    ) -> None:
        self.expected_number = expected_number
        self.role = role
        # The players list should include players_in_inclusion.
        self.players = players
        self.players_in_inclusion = players_in_inclusion

        if not players_in_inclusion:
            inclusion_set_msg = "No one with that role is in an inclusion set"
            overriden_assignments_msg = "No one's role was overriden in an inclusion set"
        else:
            inclusion_set_msg = (
                f"{', '.join(assignment_to_names(players_in_inclusion))} player(s) are assigned to an inclusion set"
            )
            overriden_assignments_msg = f"{', '.join(assignment_to_names(players_in_inclusion))} player(s) previously had role {role} but were overriden because they are in an inclusion set"

        num_roles_diff = abs(len(players) - expected_number)

        self.msg = (
            f"For role {role.name}, there are {len(players)} player(s), but {expected_number} expected teams."
            f"{inclusion_set_msg}, and in total, we have: {', '.join(assignment_to_names(players))} player(s). "
            f"{overriden_assignments_msg}.\n"
        )

        if len(players) > expected_number:
            self.msg += f"Remove {num_roles_diff} player(s) with role {role.name}."
        else:
            self.msg += f"Add {num_roles_diff} player(s) with role {role.name}."

        super().__init__(self.msg)
