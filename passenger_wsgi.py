import os
import sys
import importlib.util


# Insert the project directory into the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load the WSGI module using importlib
spec = importlib.util.spec_from_file_location('wsgi', 'olivian_solar/wsgi.py')
wsgi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wsgi)

# Get the application object
application = wsgi.application
