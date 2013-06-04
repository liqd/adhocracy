import formencode
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, model
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import guard
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, redirect, ret_abort
from adhocracy.lib.treatment import (assign_users,
                                     get_assignments_by_source_badge)


class TreatmentCreateForm(formencode.Schema):
    key = formencode.validators.String(not_empty=True)
    source_badges = forms.ValidUserBadges(not_empty=True)
    variant_count = formencode.validators.Int(min=2)
    _tok = formencode.validators.String()


class TreatmentController(BaseController):

    @guard.perm("global.admin")
    def index(self):
        userbadges = [b
                      for b in model.UserBadge.all(include_global=True)
                      if not b.title.startswith('treatment-')]
        treatments = model.Treatment.all()
        data = {
            'treatments': treatments,
            'userbadges': userbadges,
        }
        return render('treatment/index.html', data)

    @guard.perm("global.admin")
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=TreatmentCreateForm(), form='index', post_only=True)
    def create(self):
        t = model.Treatment.create(
            self.form_result['key'],
            self.form_result['source_badges'],
            self.form_result['variant_count'],
        )
        model.meta.Session.commit()
        h.flash(_("Treatment has been created."), 'success')
        return redirect(h.base_url('/admin/treatment/'))

    @guard.perm("global.admin")
    @RequireInternalRequest(methods=['POST'])
    def assign(self, key):
        treatment = model.Treatment.find(key)
        if not treatment:
            return ret_abort(_("Could not find the entity '%s'") % id,
                             code=404)

        if assign_users(treatment):
            model.meta.Session.commit()

            h.flash(_("All users have been assigned to their respective "
                      "treatment badges."), 'success')
        else:
            h.flash(_("All users are already assigned to their respective "
                      "treatment badges."))
        return redirect(h.base_url('/admin/treatment/'))

    @guard.perm("global.admin")
    def assigned(self, key):
        treatment = model.Treatment.find(key)
        if not treatment:
            return ret_abort(_("Could not find the entity '%s'") % id,
                             code=404)

        assignments = [
            {
                'source_badge': source_badge,
                'variants': current_assignment,
            }
            for source_badge, current_assignment, unassigned in (
                get_assignments_by_source_badge(treatment))]

        data = {
            'assignments': assignments,
            'treatment': treatment,
        }
        return render('treatment/assigned.html', data)
