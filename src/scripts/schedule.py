from itertools import combinations

N = 7
MAX_UNRECORDED_PLAYS = 4
MAX_RECORDED_PLAYS = 4
MAX_CONSECUTIVE_UPTIME = 2

# WLOG, suppose (0, 1) and (2, 3) are the first 2 matches, with (0, 1) on cab 1
remaining_matches = list(combinations(range(N), 2))
remaining_matches.remove((0, 1))
remaining_matches.remove((2, 3))
current_time_slots = [((0, 1), (2, 3))]


def fill_remaining_slots(
    current_time_slots,
    remaining_matches,
    remaining_empty_slots,
    current_uptimes,
    current_unrecorded_plays,
    current_recorded_plays,
):
    if not remaining_matches:
        return [current_time_slots]
    possible_solutions = []
    # Try 1 match for this slot
    if remaining_empty_slots > 0:
        for m in range(len(remaining_matches)):
            match = remaining_matches[m]
            team_a, team_b = match
            updated_recorded_plays = current_recorded_plays[:]
            updated_recorded_plays[team_a] += 1
            updated_recorded_plays[team_b] += 1
            if max(updated_recorded_plays) > MAX_RECORDED_PLAYS:
                continue
            updated_uptimes = current_uptimes[:]
            updated_uptimes[team_a] += 1
            updated_uptimes[team_b] += 1
            for t in range(N):
                if t not in (team_a, team_b):
                    updated_uptimes[t] = 0
            if max(updated_uptimes) > MAX_CONSECUTIVE_UPTIME:
                continue
            possible_solutions.extend(
                fill_remaining_slots(
                    current_time_slots=current_time_slots + [(match, None)],
                    remaining_matches=remaining_matches[0:m] + remaining_matches[m + 1 :],
                    remaining_empty_slots=remaining_empty_slots - 1,
                    current_uptimes=updated_uptimes,
                    current_unrecorded_plays=current_unrecorded_plays,
                    current_recorded_plays=updated_recorded_plays,
                )
            )
    # Try 2 matches for this slot
    if len(remaining_matches) >= 2:
        # m1 goes on cab 1, m2 goes on cab 2
        for m1 in range(len(remaining_matches)):
            for m2 in range(len(remaining_matches)):
                if m1 == m2:
                    continue
                match_1, match_2 = remaining_matches[m1], remaining_matches[m2]
                team_a, team_b = match_1
                team_c, team_d = match_2
                if team_a in (team_c, team_d) or team_b in (team_c, team_d):
                    continue
                updated_recorded_plays = current_recorded_plays[:]
                updated_recorded_plays[team_a] += 1
                updated_recorded_plays[team_b] += 1
                if max(updated_recorded_plays) > MAX_RECORDED_PLAYS:
                    continue
                updated_unrecorded_plays = current_unrecorded_plays[:]
                updated_unrecorded_plays[team_c] += 1
                updated_unrecorded_plays[team_d] += 1
                if max(updated_unrecorded_plays) > MAX_UNRECORDED_PLAYS:
                    continue
                updated_uptimes = current_uptimes[:]
                for i in range(N):
                    if i not in (team_a, team_b, team_c, team_d):
                        updated_uptimes[i] = 0
                    else:
                        updated_uptimes[i] += 1
                if max(updated_uptimes) > MAX_CONSECUTIVE_UPTIME:
                    continue
                new_remaining_matches = (
                    remaining_matches[0 : min(m1, m2)]
                    + remaining_matches[min(m1, m2) + 1 : max(m1, m2)]
                    + remaining_matches[max(m1, m2) + 1 :]
                )
                possible_solutions.extend(
                    fill_remaining_slots(
                        current_time_slots=current_time_slots + [(match_1, match_2)],
                        remaining_matches=new_remaining_matches,
                        remaining_empty_slots=remaining_empty_slots,
                        current_uptimes=updated_uptimes,
                        current_unrecorded_plays=updated_unrecorded_plays,
                        current_recorded_plays=updated_recorded_plays,
                    )
                )
    return possible_solutions


solutions = fill_remaining_slots(
    current_time_slots=current_time_slots,
    remaining_matches=remaining_matches,
    remaining_empty_slots=1,
    current_uptimes=[1, 1, 1, 1, 0, 0, 0],
    current_unrecorded_plays=[0, 0, 1, 1, 0, 0, 0],
    current_recorded_plays=[1, 1, 0, 0, 0, 0, 0],
)

best_max_uptime = 2
best_max_uptime_count = N
best_solutions = []
best_from_end_empty_slot = 10
for solution in solutions:
    max_downtimes = [0 for _ in range(N)]
    current_downtimes = [0 for _ in range(N)]
    max_uptimes = [0 for _ in range(N)]
    current_uptimes = [0 for _ in range(N)]
    from_end_empty_slot = 10
    for time_slot_index, time_slot in enumerate(solution):
        teams_playing = []
        for match in time_slot:
            if match:
                teams_playing.extend(match)
            else:
                from_end_empty_slot = len(solution) - time_slot_index - 1
        for i in range(N):
            if i in teams_playing:
                current_uptimes[i] += 1
                current_downtimes[i] = 0
            else:
                current_uptimes[i] = 0
                current_downtimes[i] += 1
        for i in range(N):
            max_uptimes[i] = max(max_uptimes[i], current_uptimes[i])
            max_downtimes[i] = max(max_downtimes[i], current_downtimes[i])
    max_downtime = max(max_downtimes)
    if max_downtime > 1:
        continue
    max_uptime = max(max_uptimes)
    max_uptime_count = len([x for x in max_uptimes if x == max_uptime])
    if (max_uptime, max_uptime_count, from_end_empty_slot) < (
        best_max_uptime,
        best_max_uptime_count,
        best_from_end_empty_slot,
    ):
        best_max_uptime, best_max_uptime_count, best_from_end_empty_slot = (
            max_uptime,
            max_uptime_count,
            from_end_empty_slot,
        )
        best_solutions = [solution]
    elif (max_uptime, max_uptime_count, from_end_empty_slot) == (
        best_max_uptime,
        best_max_uptime_count,
        best_from_end_empty_slot,
    ):
        best_solutions.append(solution)

print(len(best_solutions))

for solution in best_solutions:
    for row in solution:
        print(row)
    print()
