from authorization import has


def create(check):

    if has('global.message'):
        return
    check.perm('instance.message')
