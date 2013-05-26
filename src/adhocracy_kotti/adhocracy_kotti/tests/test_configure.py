# test kotti configuration


def test_populate(db_session):  # pytest public fixture: kotti.tests.db_session
    from kotti.resources import Document
    import transaction
