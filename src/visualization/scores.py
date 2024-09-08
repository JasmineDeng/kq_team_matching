from typing import Dict, List

import matplotlib.pyplot as plt  # type: ignore

from src.data_types.player import Player, PlayerAssignment, PlayerRole


def primary_role_score_histogram(players: list[Player]) -> None:
    # TODO(jasminedeng): test manually
    bins = list(range(11))  # 0-10 (inclusive) since scores are roughly 1-10

    role_to_scores: Dict[PlayerRole, List[float]] = {role: [] for role in PlayerRole}
    for role in PlayerRole:
        role_to_scores[role] = []
        for player in players:
            assignment = PlayerAssignment(player=player, assigned_role=role)
            role_to_scores[assignment.assigned_role].append(assignment.score)

    scores_and_label = [(scores, role.name.lower()) for role, scores in role_to_scores.items()]
    scores_list, label_list = zip(*scores_and_label)
    most_frequent = max([len(elem) for elem in scores_list])

    plt.xticks(bins)
    plt.yticks(range(most_frequent + 1))

    plt.hist(scores_list, bins, label=label_list)
    plt.legend(loc="upper right")
    plt.show()
