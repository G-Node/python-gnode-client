import os, sys

from gnodeclient import GNODECLIENT_VERSION, GNODECLIENT_RELEASE

# general config
sys.path.append(os.path.abspath('../../'))
extensions = ['sphinx.ext.autodoc']
source_suffix = '.rst'
master_doc = 'index'
project = 'Python G-Node Client'
copyright = '2013, Adrian Stoewer, Andrey Sobolev'
version = GNODECLIENT_VERSION
release = GNODECLIENT_VERSION + " " + GNODECLIENT_RELEASE
exclude_patterns = []
pygments_style = 'sphinx'

# html options
html_theme = 'default'
htmlhelp_basename = 'gnodeclient'
