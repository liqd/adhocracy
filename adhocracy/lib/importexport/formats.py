
from adhocracy.lib.templating import render_real_json

def _render_zip(data, filename):
    with io.BytesIO() as fakeFile:
        zf = zipfile.ZipFile(fakeFile, 'wb')
        for k,v in data.items():
            assert '/' not in k
            zf.writestr(k + '.json', simplejson.dumps(v))
        zf.close()

    if filename is not None:
        response.content_disposition = 'attachment; filename="' + filename.replace('"', '_') + '"'
    response.content_type = 'application/zip'
    return fakeFile.getvalue()

def read_data(f, format):
    TODO_automatic_detection
    TODO_actually read

def render(data, format):
    if format == 'zip':
        return _render_zip(data, filename=title + '.zip')
    elif eFormat == 'json_download':
        return render_real_json(data, filename=title + '.json')
    elif eFormat == 'json':
        return render_real_json(data)
    else:
        raise ValueError('Invalid format')

__all__ = ['read_data', 'render']