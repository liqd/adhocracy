import logging 
import hashlib
from solr import SolrConnection # == solrpy 

import adhocracy.model as model
import adhocracy.model.refs as refs

log = logging.getLogger(__name__)

def get_connection():
    from pylons import config 
    solr_url = config.get('adhocracy.solr.url', 'http://localhost:8983/solr')
    #log.debug('Connecting to Solr at %s...' % solr_url)
    return SolrConnection(solr_url)

def gen_id(entity):
    ref = refs.to_ref(entity)
    return hashlib.sha1(ref).hexdigest()

def update(entity):
    if not isinstance(entity, model.meta.Indexable):
        return
    index = entity.to_index()
    index['id'] = gen_id(entity)
    if index.get('skip', False):
        return
    else:
        del index['skip']
    conn = get_connection()
    try:
        print "ADDING", index
        conn.add(**index)
        conn.commit()
    except Exception, e:
        log.exception(e)
    finally:
        conn.close()

def delete(entity):
    conn = get_connection()
    try:
        index_id = gen_id(entity)
        conn.delete_query('+id:%s' % index_id)
        conn.commit()
    except Exception, e:
        log.exception(e)
    finally:
        conn.close()
    