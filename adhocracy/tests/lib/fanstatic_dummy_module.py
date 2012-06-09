from fanstatic import Resource, Group, Library

library = Library('dummy', '.')
library.need = lambda: 'No, sorry, that is a Library.'

resource = Resource(library, 'fanstatic_dummy_resource.css')
resource.need = lambda: 'needed resource'

group = Group([resource])
group.need = lambda: 'needed group'
