

def kotti_configure(settings):

    settings['kotti.asset_overrides'] = 'adhocracy_kotti:kotti-overrides/'


def includeme(config):

    config.include("cornice")
    config.scan(__name__)
