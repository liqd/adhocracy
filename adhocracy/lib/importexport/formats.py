
import contextlib
import io
import json
import zipfile

from adhocracy.lib.templating import render_json
from pylons import response


def detect_format(f):
    firstBytes = f.read(4)
    f.seek(0)
    if firstBytes[:1] == b'{':
        return 'json'
    if firstBytes == b'PK\x03\x04':
        return 'zip'
    return 'unknown'


def _render_zip(data, filename, response=response):
    with io.BytesIO() as fakeFile:
        with contextlib.closing(zipfile.ZipFile(fakeFile, 'w')) as zf:
            for k, v in data.items():
                assert '/' not in k
                zf.writestr(k + '.json', json.dumps(v))
        res = fakeFile.getvalue()

    if filename is not None:
        response.content_disposition = 'attachment; filename="'\
            + filename.replace('"', '_') + '"'
    response.content_type = 'application/zip'
    return res


def _read_zip(f):
    res = {}
    with contextlib.closing(zipfile.ZipFile(f, 'r')) as zf:
        for fn in zf.namelist():
            if fn.endswith('.json') and '/' not in fn:
                res[fn[:-len('.json')]] = json.loads(zf.read(fn))
    return res


def read_data(f, format='detect'):
    if format == 'detect':
        format = detect_format(f)

    if format == 'zip':
        return _read_zip(f)
    elif format == 'json':
        return json.load(f)
    else:
        raise ValueError('Invalid import format')


def render(data, format, title, response=response):
    if format == 'zip':
        return _render_zip(data, filename=title + '.zip', response=response)
    elif format == 'json_download':
        return render_json(data, filename=title + '.json', response=response)
    elif format == 'json':
        return render_json(data, response=response)
    else:
        raise ValueError('Invalid export format')
