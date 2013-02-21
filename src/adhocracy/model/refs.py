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

from inspect import isclass
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
from milestone import Milestone


log = logging.getLogger(__name__)
undef_marker = object()

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
         Milestone,
         Tagging]


def entity_type(entity):
    return cls_type(type(entity))


def cls_type(cls):
    return unicode(cls.__name__.lower())


TYPES_MAP = dict((cls_type(t), t) for t in TYPES)


def entity_ref_attr_name(entity):
    '''
    Return the name of the attribute to use in references
    '''
    return getattr(entity, '_index_id_attr', 'id')


def ref_attr_value(entity_or_cls):
    '''
    Return the value (unicode) of the reference attribute (for model
    objects) or the :class:`sqlalchemy.orm.attributes.InstrumenteAttribute`
    object (for model classes)
    '''
    id_attr = entity_ref_attr_name(entity_or_cls)
    attr_value = getattr(entity_or_cls, id_attr, undef_marker)
    if attr_value is undef_marker:
            raise KeyError('Wrong index id attribute for object/class "%s": %s'
                           % (entity_or_cls, id_attr))
    if isclass(entity_or_cls):
        return attr_value
    else:
        return unicode(attr_value)


def to_ref(entity):
    '''Generate a string reference to a model object.
    The reference has the format `@[<entity_type>:<id>]`.
    Parameters:
    `entity`
       A model object that has a method `_index_id()` which returns
       a unique id across all instances of its model class. The object
       has to be an instance of one of the model classes in
       :data:`TYPES`
    Returns a `unicode` string reference if one can be generated
    or the passed in `entity` object if not.
    '''
    for cls in TYPES:
        if isinstance(entity, cls):
            return u"@[%s:%s]" % (entity_type(entity),
                                  ref_attr_value(entity))
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


def to_entities(refs):
    '''
    Return the entities referenced by refs (see :func:`to_ref`).
    The entities are returned in the same order as refs

    *refs' (list of strings)
        A List of references

    Returns
        A list of Entities

    Raises
        :exc:`ValueError` if the refs do not reference the same entity
        type
    '''
    ids = {}
    for ref in refs:
        match = FORMAT.match(unicode(ref))
        if not match:
            continue
        refcls = match.group(1)
        refid = match.group(2)
        ids.setdefault(refcls, []).append(refid)

    all = {}
    for cls in ids:
        entity_class = TYPES_MAP[cls]
        entities = get_entities(entity_class, ids[cls], order=False)
        for entity in entities:
            all[to_ref(entity)] = entity

    return [all[ref] for ref in refs if ref in all]


def get_entities(entity_class, ids, order=True):
    '''
    Return all entities of the type *entity_class* where id is
    in *ids*.

    *entity_class*
       An slqalchemy model class.
    *ids* (list of int)
       A list of ids.
    *order* (boolean)
       Return the entities in the same order as *ids* (default: True)
    Returns
       A list of model objects
    '''

    if ids == []:
        return []

    from meta import Session
    db_mapper_attr = ref_attr_value(entity_class)
    q = Session.query(entity_class).filter(db_mapper_attr.in_(ids))

    if not order:
        return q.all()

    # order == True: get and order the results
    all_map = dict((str(ref_attr_value(entity)), entity) for entity in q.all())
    ordered_results = []
    for id_ in ids:
        entity = all_map.get(str(id_))
        if entity is not None:
            ordered_results.append(entity)
    return ordered_results


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
