# test kotti configuration


def test_configure_image_scales(config):
    from adhocracy_kotti import kotti_configure
    from adhocracy_kotti import schemata
    from kotti.util import extract_from_settings
    settings = config.registry.settings
    kotti_configure(settings)
    available_scales = extract_from_settings('kotti.image_scales.',
                                             settings).keys().sort()
    needed_scales = schemata.ImageScale.validator.choices.sort()
    assert available_scales == needed_scales
