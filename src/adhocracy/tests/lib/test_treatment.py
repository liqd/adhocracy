
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user, tt_make_str
from adhocracy.model import UserBadge, Treatment

from adhocracy.lib.treatment import (get_assignments_by_source_badge,
                                     assign_users)


class TreatmentTest(TestController):
    def test_assignment(self):
        b = UserBadge.create(u'all users - ' + tt_make_str(), u'', False, u'')

        t = Treatment.create(tt_make_str(), source_badges=[b], variant_count=2)
        sb, assignments, unassigned = get_assignments_by_source_badge(t)[0]
        assert sb == b
        ass1, ass2 = assignments
        assert len(ass1) == 0
        assert len(ass2) == 0
        assert len(unassigned) == 0

        first_users = [tt_make_user() for _ in range(5)]
        for u in first_users:
            b.assign(u, u)
        # sanity check
        assert set(u.id for u in b.users) == set(u.id for u in first_users)

        sb, assignments, unassigned = get_assignments_by_source_badge(t)[0]
        assert sb == b
        ass1, ass2 = assignments
        assert len(ass1) == 0
        assert len(ass2) == 0
        assert len(unassigned) == len(first_users)

        assert assign_users(t)
        sb, assignments, unassigned = get_assignments_by_source_badge(t)[0]
        assert sb == b
        ass1, ass2 = assignments
        assert len(ass1) + len(ass2) == len(first_users)
        assert (len(ass1) == len(ass2) - 1) or (len(ass1) == len(ass2) + 1)
        assert len(unassigned) == 0

        assert not assign_users(t)

        new_users = [tt_make_user() for _ in range(5)]
        for u in new_users:
            b.assign(u, u)
        sb, assignments, unassigned = get_assignments_by_source_badge(t)[0]
        assert sb == b
        ass1, ass2 = assignments
        assert len(ass1) + len(ass2) == len(first_users)
        assert (len(ass1) == len(ass2) - 1) or (len(ass1) == len(ass2) + 1)
        assert len(unassigned) == len(new_users)

        assert assign_users(t)
        sb, assignments, unassigned = get_assignments_by_source_badge(t)[0]
        assert sb == b
        ass1, ass2 = assignments
        assert len(ass1) + len(ass2) == len(first_users) + len(new_users)

        # The following assert is disabled as it fails non-deterministically
        # (see #601). It can be reenabled once this issue is fixed.

        # assert len(ass1) == len(ass2)

        assert len(unassigned) == 0

        assert not assign_users(t)
