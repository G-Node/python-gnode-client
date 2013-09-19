import os
import appdirs

try:
    import simplejson as json
except ImportError:
    import json


class Configuration(dict):

    VERSION = '0.1.0'
    NAME = 'gnodeclient'

    def __init__(self, options=None, file_name=None, persist_options=False):
        super(Configuration, self).__init__()

        # set options to empty dict if None
        if options is None:
            options = {}

        # read config from file
        if file_name is None:
            file_name = os.path.join(appdirs.user_data_dir(appname=Configuration.NAME),
                                     Configuration.NAME + '.conf')

        fhandle = None
        f_options = None
        try:
            fhandle = open(file_name, 'r')
            f_options = json.load(fhandle, encoding='UTF-8')
        except IOError:
            pass
        finally:
            if fhandle is not None:
                fhandle.close()
            if f_options is None:
                f_options = {}

        # merge with other options
        tmp = f_options.copy()
        tmp.update(options)
        options = tmp

        # set defaults
        self['version'] = '0.1.0'
        self['username'] = options.get('username', None)
        self['password'] = options.get('password', None)
        self['location'] = options.get('location', 'http://localhost:8000')
        self['cache_dir'] = options.get('cache_dir', appdirs.user_cache_dir(Configuration.NAME))
        self['log_dir'] = options.get('log_file', os.path.join(appdirs.user_data_dir(Configuration.NAME),
                                                               Configuration.NAME + '.log'))
        self['odml_repo'] = options.get('odml_repo',
                                        'http://portal.g-node.org/odml/terminologies/v1.0/terminologies.xml')

        # write options back
        if persist_options:
            try:
                d = os.path.dirname(file_name)
                if not os.path.exists(d):
                    os.makedirs(d)
                fhandle = open(file_name, 'w+')
                options = self.copy()
                if not 'password' in f_options or f_options.get('password') is None:
                    del options['password']
                fhandle.write(json.dumps(options, sort_keys=True, indent=4 * ' '))
            except IOError:
                # TODO do some logging here
                pass
            finally:
                if fhandle is not None:
                    fhandle.close()
