
import sys
import pygccxml

def _withplatform(f, platform):
    def g(*args, **kwargs):
        orig = sys.platform
        sys.platform = platform
        try:
            return f(*args, **kwargs)
        finally:
            sys.platform = orig
    return g

if sys.platform == 'cli':
    # claim we're on win32
    conf_t = pygccxml.parser.config.gccxml_configuration_t
    conf_t.raise_on_wrong_settings = _withplatform(conf_t.raise_on_wrong_settings, 'win32')


from pygccxml.parser.config import config_t
from pygccxml.parser.source_reader import source_reader_t

def read_gccxml(path):
    reader = source_reader_t(config_t())
    return reader.read_xml_file(path)[0]


