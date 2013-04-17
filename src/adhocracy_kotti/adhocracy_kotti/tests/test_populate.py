from kotti.resources import get_root


def test_populate(populate):
    root = get_root()
    # test keys
    assert root.keys() == [u'mediacenter']
