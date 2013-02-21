from util import render_tile, BaseTile


class TagTile(BaseTile):

    def __init__(self, tag):
        self.tag = tag


def row(tag):
    return render_tile('/tag/tiles.html', 'row', TagTile(tag),
                       tag=tag, cached=True)


def cloud(tags, plain=True, show_count=False, link_more=True):
    from adhocracy.lib.templating import render_def
    return render_def('/tag/tiles.html', 'cloud', tags=tags, plain=plain,
                      show_count=show_count, link_more=link_more, cached=True)


def sidebar(delegateable):
    from adhocracy.lib.templating import render_def
    return render_def('/tag/tiles.html', 'sidebar',
                      delegateable=delegateable, cached=True)
