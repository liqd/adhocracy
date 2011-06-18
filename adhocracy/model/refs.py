'''
Printable string references for model objects.

Functions to generate string references to model objects
(`@[<entity_type>:<id>]`) and resolve them back, where
`entity_type`
  is a string identifying the model class.
`id`
  is an id uniqe for a model instance within the entity_type

The module also provides helpers to work with url encoded
references and lists or dicts of references or model objects.
'''

import logging
import re
import base64

from pylons.i18n import _

from comment import Comment
from delegation import Delegation
from group import Group
from instance import Instance
from page import Page
from permission import Permission
from poll import Poll
from proposal import Proposal
from revision import Revision
from selection import Selection
from tag import Tag
from tagging import Tagging
from text import Text
from user import User
from vote import Vote

log = logging.getLogger(__name__)

FORMAT = re.compile("@\[(.*):(.*)\]")

TYPES = [Vote,
         User,
         Group,
         Permission,
         Comment,
         Revision,
         Delegation,
         Proposal,
         Poll,
         Instance,
         Tag,
         Page,
         Selection,
         Text,
         Tagging]


def entity_type(entity):
    return cls_type(type(entity))


def cls_type(cls):
    return unicode(cls.__name__.lower())


def to_ref(entity):
    '''Generate a string reference to a model object.
    The reference has the format `@[<entity_type>:<id>]`.
    Parameters:
    `entity`
       An model object that has a method `_index_id()` which returns
       an uniqe id across all instances of it's model class. The object
       has to be an instance of one of the model classes in
       :data:`TYPES`
    Returns a `unicode` string reference if one can be generated
    or the passed in `entity` object if not.
    '''
    for cls in TYPES:
        if isinstance(entity, cls):
            return u"@[%s:%s]" % (entity_type(entity),
                                  unicode(entity._index_id()))
    return None


def to_id(ref):
    match = FORMAT.match(unicode(ref))
    return match.group(2) if match else None


def ref_type(ref):
    match = FORMAT.match(unicode(ref))
    return match.group(1) if match else None


def to_entity(ref, instance_filter=False, include_deleted=True):
    '''Resolve a model object from a reference in the format
    `@[<entity_type>:<id>]`.
    `instance_filter`
       If `True` limit the search for the model instance to the
       `current` instance. The instance is determinated by
       :module:`adhocracy.model.instance_filter`.
    `include_deleted`
       If True also resolve to model objects that are already deleted.
    '''
    match = FORMAT.match(unicode(ref))
    if not match:
        return ref
    for cls in TYPES:
        if match.group(1) == cls_type(cls):
            entity = cls.find(match.group(2),
                              instance_filter=instance_filter,
                              include_deleted=include_deleted)
            #log.debug("entityref reloaded: %s" % repr(entity))
            return entity
    log.warn("No typeformatter for: %s" % ref)
    return ref


def to_url(entity):
    '''
    Generate a reference that encodes the reference to use in urls.
    See :func:`to_ref`.
    '''
    return base64.urlsafe_b64encode(str(to_ref(entity)))


def from_url(url):
    '''
    Resolve an url friendly encoded reference (see :func:`to_url`).
    See :func:`to_entity`. Note that default parameters of
    :func:`to_entity` are used.
    '''
    return to_entity(base64.urlsafe_b64decode(str(url)))


def _ify(fun, obj):
    if isinstance(obj, type([])):
        return [_ify(fun, e) for e in obj]
    elif isinstance(obj, type({})):
        return dict([(k, _ify(fun, v)) for k, v in obj.items()])
    else:
        if obj:
            obj = fun(obj)
            if not obj:
                obj = _("(Undefined)")
        return obj


def complex_to_refs(obj):
    '''Generate string references for list or dict containing model
    objects.
    `obj`
       A single model object or a lists or dicts of model objects.
    Returns a single reference or a list or dict of references.
    For details see :func:`to_ref`
    '''
    return _ify(to_ref, obj)


def complex_to_entities(refs):
    '''Resolve model instances from a list or dict of references.
    `refs`
      A list or dict of references.
    For details see :func:`to_entity'. Note that the default values
    for the additional parameter of `to_entity` will be used.
    '''
    return _ify(to_entity, refs)
