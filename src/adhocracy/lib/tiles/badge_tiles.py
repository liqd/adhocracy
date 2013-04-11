def badge(badge, force_visible=False):
    from adhocracy.lib.templating import render_def
    return render_def('/badge/tiles.html', 'badge', badge=badge,
                        force_visible=force_visible, cached=True)


def badges(badges):
    from adhocracy.lib.templating import render_def
    return render_def('/badge/tiles.html', 'badges', badges=badges,
                      cached=True)

def badge_selector(badges, field_name):
    from adhocracy.lib.templating import render_def
    return render_def('/badge/tiles.html', 'badge_selector',
                    badges=badges, field_name=field_name)

def badge_styles():
    '''
    Render a <style>-block with dyamic badge styles
    '''
    from adhocracy.lib.templating import render_def
    from adhocracy.model import Badge
    badges = Badge.all_q().all()
    return render_def('/badge/tiles.html', 'badge_styles', badges=badges,
                      cached=True)
