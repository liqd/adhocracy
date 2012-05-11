from pylons import config, request, tmpl_context as c

from adhocracy.lib.base import BaseController
from adhocracy.lib.helpers import json_loads
from adhocracy.lib.templating import render
from adhocracy.model.meta import engine


class DebugController(BaseController):

    def explain(self):
        if not config.get('adhocracy.debug.sql'):
            raise ValueError('Not in debugging mode')
        statement = request.params.get('statement')
        if not statement.lower().startswith('select'):
            raise ValueError('We explain only select statements')
        parameters = request.params.get('parameters')
        c.parameters = json_loads(parameters)

        # collect explain results
        if engine.name.startswith('sqlite'):
            explain_query = 'EXPLAIN QUERY PLAN %s' % statement
        else:
            explain_query = 'EXPLAIN %s' % statement

        explain_result = engine.execute(explain_query, c.parameters)
        data_result = engine.execute(statement, c.parameters)
        c.results = []
        for (title, result) in (('Explain', explain_result),
                                ('Data', data_result)):
            c.results.append({'title': title,
                              'result': result.fetchall(),
                              'headers': result.keys()})

        # other data to display
        c.statement = statement
        c.duration = float(request.params['duration'])

        return render('/debug/explain.html')
