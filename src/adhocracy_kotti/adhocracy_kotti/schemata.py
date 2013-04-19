import colander


class Tags(colander.SequenceSchema):

    tag = colander.SchemaNode(colander.String())


class TagsList(colander.MappingSchema):

    tags = Tags(missing=[], default=[], location="querystring")


class Identifier(colander.SchemaNode):
    """Alpha/numeric/_-  String, encoding utf-8

       A unique identifier.

       Example value: bluABC_1-23
    """
    schema_type = colander.String
    validator = colander.Regex(u'^[a-zA-Z0-9_-]+$')


class ImageScale(colander.SchemaNode):
    """Predefined image scale String, encoding utf-8

       value: icon | thumb | logo | middle | large
    """
    schema_type = colander.String
    validator = colander.OneOf([u'icon',
                                u'thumb',
                                u'logo',
                                u'middle',
                                u'large',
                                ])


class ImagePOST(colander.MappingSchema):

    filename = colander.SchemaNode(colander.String())
    mimetype = colander.SchemaNode(colander.String(),
                                   validator=colander.OneOf(['image/jpeg',
                                                             'image/png']))
    tags = Tags(missing=[], default=[])
    data = colander.SchemaNode(colander.String())


class ImageGET(colander.MappingSchema):

    name = Identifier()
    tags = Tags(missing=[], default=[])
    filename = colander.SchemaNode(colander.String(), default=u"", missing=u"")
    mimetype = colander.SchemaNode(colander.String(), default=u"", missing=u"")
    size = colander.SchemaNode(colander.Integer(), missing=0, default=0)


class ImageGETDATA(colander.MappingSchema):

    name = Identifier(location="path")
    scale = ImageScale(missing=u"large", default=u"large", location="path",)
