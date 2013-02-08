"""
Helper functions for human-readable and interoperable formats for adhocracy's
data.
"""

import logging
import email.utils
import time
import zipfile

from . import formats
from . import transforms

from adhocracy import model
from pylons import config


def export_data(opts):
    data = {}
    data['metadata'] = {
        'type': 'normsetting-export',
        'version': 4,
        'time': email.utils.formatdate(time.time()),
        'adhocracy_options': opts,
    }
    for transform in transforms.gen_active(opts):
        data[transform.public_name] = transform.export_all()
    return data


def export(opts):
    timeStr = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
    title = config.get('adhocracy.site.name', 'adhocracy') + '-' + timeStr
    format = opts.get('format', 'json')
    return formats.render(export_data(opts), format, title)


def import_(opts, f):
    data = formats.read_data(f, opts.get('filetype'))
    import_data(opts, data)
    model.meta.Session.commit()


def convert_legacy(data):
    if data.get('metadata', {}).get('version') == 2:
        data['user'] = data['users']
    return data


def import_data(opts, data):
    data = convert_legacy(data)
    for transform in transforms.gen_active(opts):
        idata = data.get(transform.public_name, {})
        transform.import_all(idata)

# TODO merge with csv user import
