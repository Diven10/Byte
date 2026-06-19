import os
import sys

# Add the byte_project directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'byte_project'))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'byte.settings')

app = get_wsgi_application()
