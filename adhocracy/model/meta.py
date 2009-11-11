"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

import hooks

__all__ = ['Session', 'metadata', 'Base', 'engine']

# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager.  Updated by model.init_model()
Session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
metadata = MetaData()

Base = declarative_base(metadata=metadata)
Base.__mapper_args__ = {'extension': hooks.HookExtension()}