def badges(badges):
    from adhocracy.lib.templating import render_def
    return render_def('/badge/tiles.html', 'badges', badges=badges,
                      cached=True)
