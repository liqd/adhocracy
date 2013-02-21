from util import render_tile

from delegateable_tiles import DelegateableTile


class PageTile(DelegateableTile):

    def __init__(self, page):
        self.page = page
        DelegateableTile.__init__(self, page)


def row(page):
    return render_tile('/page/tiles.html', 'row', PageTile(page),
                       page=page, cached=True)


def smallrow(page):
    return render_tile('/page/tiles.html', 'smallrow', PageTile(page),
                       page=page, cached=True)


def select_page(field_name='page', select=None, exclude=[], functions=[],
                list_limit=500, allow_empty=True):
    return render_tile('/page/tiles.html', 'select_page', None, select=select,
                       exclude=exclude, field_name=field_name,
                       functions=functions,
                       list_limit=list_limit, allow_empty=allow_empty)


def inline(page, tile=None, text=None, subpages_pager=None,
           hide_discussion=False):
    if tile is None:
        tile = PageTile(page)
    if text is None:
        text = page.head
    return render_tile('/page/tiles.html', 'inline', tile, page=page,
                       hide_discussion=hide_discussion, text=text,
                       subpages_pager=subpages_pager)


def header(page, tile=None, active='goal', text=None, variant=None):
    if tile is None:
        tile = PageTile(page)
    if text is None:
        text = page.head
    if variant is None:
        variant = text.variant
    return render_tile('/page/tiles.html', 'header', tile,
                       page=page, text=text, variant=variant, active=active)
