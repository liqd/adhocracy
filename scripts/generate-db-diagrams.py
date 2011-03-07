from sqlalchemy.orm import class_mapper
from sqlalchemy_schemadisplay import create_schema_graph, create_uml_graph

from adhocracy import model


# create a diagram of all tables

graph = create_schema_graph(
    metadata=model.meta.data,
    show_datatypes=True,
    show_indexes=False,
    rankdir='LR',
    concentrate=False   # Don't try to join the relation lines together
)

graph.write_png('adhocracy-tables.png')


# create an uml diagramm of all mapped classes

mappers = []
for attr in dir(model):
    if attr[0] == '_':
        continue
    try:
        cls = getattr(model, attr)
        mappers.append(class_mapper(cls))
    except:
        pass

graph = create_uml_graph(mappers,
                         show_operations=False,
                         show_multiplicity_one=True)

graph.write_png('adhocracy-classes.png')
