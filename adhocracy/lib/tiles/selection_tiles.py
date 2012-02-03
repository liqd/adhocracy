from pylons import tmpl_context as c

from adhocracy.lib.auth import can
from util import render_tile, BaseTile


class VariantRow(object):

    def __init__(self, tile, variant, poll):
        self.tile = tile
        self.variant = variant
        self.poll = poll
        if tile.frozen:
            freeze_time = tile.selection.proposal.adopt_poll.begin_time
            self.text = tile.selection.page.variant_at(variant, freeze_time)
        else:
            self.text = tile.selection.page.variant_head(variant)

    @property
    def selected(self):
        return self.tile.selected == self.variant

    @property
    def show(self):
        return not self.tile.frozen or self.selected

    @property
    def can_edit(self):
        return (not self.tile.frozen) and \
            can.variant.edit(self.tile.selection.page, self.variant)

    @property
    def num_comments(self):
        return len(self.tile.selection.page.variant_comments(self.variant))


class SelectionTile(BaseTile):

    def __init__(self, selection):
        self.selection = selection
        self.selected = selection.selected
        self.variant_polls = self.selection.variant_polls

    @property
    def has_variants(self):
        return len(self.selection.page.variants) < 2

    @property
    def num_variants(self):
        return len(self.selection.page.variants) - 1

    @property
    def selected_text(self):
        variant = self.selected
        if self.frozen:
            freeze_time = self.selection.proposal.adopt_poll.begin_time
            return self.selection.page.variant_at(variant, freeze_time)
        else:
            return self.selection.page.variant_head(variant)

    @property
    def selected_num_comments(self):
        return len(self.selection.page.variant_comments(self.selected))

    @property
    def frozen(self):
        return self.selection.proposal.is_adopt_polling()

    def variant_rows(self):
        for (variant, poll) in self.variant_polls:
            row = VariantRow(self, variant, poll)
            yield row

    @property
    def show_new_variant_link(self):
        if self.frozen:
            return False
        return can.norm.edit(self.selection.page, 'any')


def row(selection):
    if not selection or selection.is_deleted():
                return ""
    tile = SelectionTile(selection)
    return render_tile('/selection/tiles.html', 'row', tile,
                       selection=selection, user=c.user, cached=True)


def variants(selection, tile=None):
    if tile is None:
        tile = SelectionTile(selection)
    return render_tile('/selection/tiles.html', 'variants', tile,
                       selection=selection, user=c.user, cached=True)
