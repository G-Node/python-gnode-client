import os
import sys


# general config
sys.path.append(os.path.abspath('../../'))
extensions = ['sphinx.ext.autodoc']
source_suffix = '.rst'
master_doc = 'index'
project = 'Python G-Node Client'
copyright = '2013, Adrian Stoewer, Andrey Sobolev'
version = "0.3.1"
release = "0.3.1 Beta"
exclude_patterns = []
pygments_style = 'sphinx'

# html options
html_theme = 'default'
htmlhelp_basename = 'gnodeclient'
