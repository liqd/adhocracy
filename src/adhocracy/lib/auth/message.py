from authorization import has


def create(check, instance):

    if has('global.message'):
        return
    check.other('is_not_authenticated', not instance.is_authenticated)
    check.perm('instance.message')
