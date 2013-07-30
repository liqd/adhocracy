import contextlib
import json
import zipfile


def detect_format(f):
    firstBytes = f.read(4)
    f.seek(0)
    if firstBytes[:1] == b'{':
        return 'json'
    if firstBytes == b'PK\x03\x04':
        return 'zip'
    return 'unknown'


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
