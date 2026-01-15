import os
import sys
import importlib.util
from mimetypes import guess_type

# Static file serving for Passenger
def static_file_handler(environ, start_response):
    static_root = '/home/olivian1/public_html/static'
    path_info = environ.get('PATH_INFO', '')

    if path_info.startswith('/static/'):
        file_path = os.path.join(static_root, path_info[8:])  # Remove /static/
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Determine MIME type
            mime_type, _ = guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Serve the file
            with open(file_path, 'rb') as f:
                content = f.read()

            headers = [
                ('Content-Type', mime_type),
                ('Content-Length', str(len(content))),
                ('Cache-Control', 'public, max-age=31536000'),  # 1 year cache
            ]

            start_response('200 OK', headers)
            return [content]

    # Fall back to Django application
    return django_application(environ, start_response)

# Insert the project directory into the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load the WSGI module using importlib
spec = importlib.util.spec_from_file_location('wsgi', 'olivian_solar/wsgi.py')
wsgi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wsgi)

# Get the Django application
django_application = wsgi.application

# Use our static file handler as the main application
application = static_file_handler
