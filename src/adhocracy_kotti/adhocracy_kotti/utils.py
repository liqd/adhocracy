from kotti.util import title_to_name
from kotti.resources import get_root
from kotti.resources import (
    Document
)


def find_name(context, title):
    """find a valid name, try to use title"""
    name = title_to_name(title, blacklist=context.keys())
    return name


def to_appstruct(context, schema):
    """transform an image object to dictionary"""
    appstruct = schema.deserialize(context.__dict__)
    appstruct["tags"] = context.tags
    return appstruct


def get_image_folder():
    root = get_root()
    if not "mediacenter" in root:
        root["mediacenter"] = Document(title="mediacenter")
    return root["mediacenter"]
