import uuid
from kotti.util import title_to_name
from kotti.resources import get_root
from kotti.resources import (
    Document
)


def generate_image_name(binarydata):
    """find a valid name based on the binarydata hash"""
    name_uid = uuid.uuid3(uuid.NAMESPACE_DNS, binarydata)
    name = u"".join(name_uid.urn)
    name = title_to_name(u"".join(name_uid.urn))
    return name


def to_appstruct(context, schema):
    """transform an image object to dictionary"""
    appstruct = schema.deserialize(context.__dict__)
    appstruct["tags"] = context.tags.copy()
    return appstruct


def get_image_folder():
    root = get_root()
    if not "mediacenter" in root:
        root["mediacenter"] = Document(title="mediacenter")
    return root["mediacenter"]
