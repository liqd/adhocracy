
import contextlib
import os
import io
import json
import tarfile

from tempfile import NamedTemporaryFile
from pprint import pformat
from zipfile import ZipFile
from gzip import GzipFile
from pylons import response


def detect_format(f):
    firstBytes = f.read(4)
    f.seek(0)
    if firstBytes[:1] == b'{':
        return 'json'
    if firstBytes == b'PK\x03\x04':
        return 'zip'
    return 'unknown'

def _render_json(obj, encoding='utf-8'):
    return json.dumps(obj, encoding)

def _render_data(data, renderer=_render_json, encoding='utf-8'):
    result = {}
    for k, v in data.items():
        assert '/' not in k
        result[k] = renderer(v, encoding)
    return result

def _render_zip(data, renderer=_render_json, encoding='utf-8'):
    with io.BytesIO() as fake_file:
        with contextlib.closing(ZipFile(fake_file, 'a')) as zf:
            for k, v in _render_data(data, renderer, encoding).items():
                zf.writestr(k, v)
        return fake_file.getvalue()

def _render_tar(data, renderer=_render_json, encoding='utf-8', compression=None):
    compression = "gz" if compression == "gzip" else "bz2"

    with io.BytesIO() as t_fake_file:
        if compression:
            tf = tarfile.open(fileobj=t_fake_file, mode="w:{}".format(compression))
        else:
            tv = tarfile.open(fileobj=t_fake_file, mode="w")

        for k, v in _render_data(data, renderer, encoding).iteritems():
            with NamedTemporaryFile(delete=False) as v_file:
                v_file.write(v)
            with open(v_file.name) as f:
                tarinfo = tf.gettarinfo(fileobj=f)
                tarinfo.name = k
                tf.addfile(tarinfo, f)
            os.remove(v_file.name)

        tf.close()
        return t_fake_file.getvalue()

def _render_tgz(data, renderer=_render_json, encoding='utf-8'):
    return _render_tar(data, renderer, encoding, "gzip")

def _render_tbz(data, renderer=_render_json, encoding='utf-8'):
    return _render_tar(data, renderer, encoding, "bzip2")

def _render_gzip(data, renderer=_render_json, encoding='utf-8'):
    with io.BytesIO() as fake_file:
        with GzipFile(fileobj=fake_file, mode="w") as zf:
                zf.write(renderer(_render_data(data, renderer, encoding)))
        return fake_file.getvalue()

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

def render(data, format, deliver, title, response=response):
    try:
        renderer = globals()["_render_{}".format(format)]
    except KeyError:
        raise ValueError('Invalid export format')

    if deliver in ["site", "file"]:
        response.content_encoding = "utf-8"
        result = pformat(_render_data(data, renderer))
    else:
        try:
            result = globals()["_render_{}".format(deliver)](data, renderer)
        except KeyError:
            raise ValueError("Invalid deliver format")

    if deliver != 'site':
        if deliver == "file":
            filename = "{0}.{1}".format(title.replace('"', '_'), format)
            response.content_type = "text/{0}".format(format)
        elif deliver == "gzip":
            response.content_type = "application/x-gzip"
            filename = "{0}.gz".format(title.replace('"', '_'))
        elif deliver == "tgz":
            filename = "{0}.{1}".format(title.replace('"', '_'), deliver)
            response.content_type = "application/x-gzip"
        elif deliver == "tbz":
            filename = "{0}.{1}".format(title.replace('"', '_'), deliver)
            response.content_type = "application/x-bzip"
        else:
            filename = "{0}.{1}".format(title.replace('"', '_'), deliver)
            response.content_type = "application/{}".format(deliver)

        response.content_disposition = 'attachment; filename="{0}"'.format(filename)

    return result

