import itertools
import random


def _iter_assignments_by_source_badge(treatment):
    assigned_ids = [set(u.id for u in aul)
                    for aul in treatment.get_assigned_users()]

    for b in treatment.source_badges:
        current_assignment = [[] for i in range(len(assigned_ids))]
        unassigned = []
        for u in b.users:
            for uids, assignment in zip(assigned_ids, current_assignment):
                if u.id in uids:
                    assignment.append(u)
                    break
            else:
                unassigned.append(u)
        yield (b, current_assignment, unassigned)


def get_assignments_by_source_badge(treatment):
    return list(_iter_assignments_by_source_badge(treatment))


def pick_user_assignments(treatment):
    for source_badge, current_assignment, unassigned in (
            _iter_assignments_by_source_badge(treatment)):

        # Determine how often we should pick from which variants
        possible_assignments = []
        assignment_counts = list(map(len, current_assignment))
        mx = max(assignment_counts)

        for i, ac in enumerate(assignment_counts):
            possible_assignments.extend([i] * (mx - ac))

        needed_count = len(unassigned) - len(possible_assignments)
        if needed_count > 0:
            needed_rounds = needed_count // treatment.variant_count + 1
            possible_assignments.extend(range(treatment.variant_count) *
                                        needed_rounds)

        random.shuffle(possible_assignments)

        for user, variant_id in zip(unassigned, possible_assignments):
            badge = treatment.get_variant_badge(variant_id)
            yield (user, badge)


def assign_users(treatment):
    """ Assigns each unassigned user matched by the source badges a
    treatment variant badge """

    changed = False
    for user, badge in pick_user_assignments(treatment):
        changed = True
        badge.assign(user=user, creator=user)
    return changed
