
import collections
import contextlib
import gzip
import io
import json
import tarfile
import zipfile

from pylons import response


def _render_json(obj):
    return json.dumps(obj, 'utf-8', indent=2)


def _render_data(data):
    result = {}
    for k, v in data.iteritems():
        assert '/' not in k
        result[k + u'.json'] = _render_json(v)
    return result


def _render_zip(data):
    with io.BytesIO() as fake_file:
        with contextlib.closing(zipfile.ZipFile(fake_file, 'a')) as zf:
            for k, v in _render_data(data).iteritems():
                zf.writestr(k, v)
        return fake_file.getvalue()


def _render_json_gzip(data):
    with io.BytesIO() as fake_file:
        with gzip.GzipFile(fileobj=fake_file, mode="w") as zf:
            json.dump(data, zf, indent=2)
        return fake_file.getvalue()


def _render_tar(data, compression=None):
    mode = 'w'
    if compression:
        mode += ':' + compression

    with io.BytesIO() as fake_file:
        otf = tarfile.open(fileobj=fake_file, mode=mode)
        with contextlib.closing(otf) as tf:
            for k, v in _render_data(data).iteritems():
                info = tarfile.TarInfo(name=k)
                info.size = len(v)
                with io.BytesIO() as entry_file:
                    entry_file.write(v)
                    entry_file.seek(0)
                    tf.addfile(tarinfo=info, fileobj=entry_file)
        return fake_file.getvalue()


def _render_tar_gz(data):
    return _render_tar(data, 'gz')


def _render_tar_bz2(data):
    return _render_tar(data, 'bz2')


Renderer = collections.namedtuple(
    'Renderer',
    ('func', 'ext', 'mimetype', 'encoding')
)
RENDERERS = {
    'json': Renderer(
        _render_json, None, 'application/json', 'utf-8'),
    'json_download': Renderer(
        _render_json, '.json', 'application/json', 'utf-8'),
    'json_gzip': Renderer(
        _render_json_gzip, '.json.gz', 'application/gzip', 'binary'),
    'tar': Renderer(
        _render_tar, '.tar', 'application/x-tar', 'binary'),
    'tar_gz': Renderer(
        _render_tar, '.tar.gz', 'application/gzip', 'binary'),
    'tar_bz2': Renderer(
        _render_tar, '.tar.bz2', 'application/x-bzip2', 'binary'),
    'zip': Renderer(
        _render_zip, '.zip', 'application/zip', 'binary'),
}


def render(data, format, title, response=response):
    try:
        r = RENDERERS[format]
    except KeyError:
        raise ValueError('Invalid export format')

    response.content_type = r.mimetype
    response.content_encoding = r.encoding
    if r.ext is not None:
        response.content_disposition = 'attachment; filename="{0}"'.format(
            title + r.ext
        )

    return r.func(data)
