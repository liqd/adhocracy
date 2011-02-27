"""SQLAlchemy Metadata and Session object"""

from sqlalchemy import MetaData
import hooks

__all__ = ['Session', 'data', 'extension', 'engine']

# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager.  Updated by model.init_model()
# REFACT: this is an instance, not a class - so it should be lowercased
Session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
data = MetaData()

extension = hooks.HookExtension()


class Indexable(object):

    def to_index(self):
        import refs
        index = dict(
            ref=refs.to_ref(self),
            doc_type=refs.entity_type(self))
        if hasattr(self, 'is_deleted'):
            index['skip'] = self.is_deleted()
        if hasattr(self, 'create_time'):
            index['create_time'] = self.create_time.strftime("%s")
        return index
