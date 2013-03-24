def get_parent_badges(badge):
    """Returns a generator with all parent badges
       in hierachical order (root last)
    """
    if hasattr(badge, "parent") and badge.parent:
        parent = badge.parent
        yield parent
        for p in get_parent_badges(parent):
            yield p
