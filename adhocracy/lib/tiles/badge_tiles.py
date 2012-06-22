def badge(badge):
    from adhocracy.lib.templating import render_def
    return render_def('/badge/tiles.html', 'badge', badge=badge,
                      cached=True)


def badges(badges):
    from adhocracy.lib.templating import render_def
    return render_def('/badge/tiles.html', 'badges', badges=badges,
                      cached=True)


def badge_styles():
    '''
    Render a <style>-block with dyamic badge styles
    '''
    from adhocracy.lib.templating import render_def
    from adhocracy.model import Badge
    badges = Badge.all_q().all()
    return render_def('/badge/tiles.html', 'badge_styles', badges=badges,
                      cached=True)
