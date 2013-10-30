# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

"""
Very simple configuration file handling.
"""

import os
import appdirs

try:
    import simplejson as json
except ImportError:
    import json


class Configuration(dict):
    """
    A configuration class that extends dictionary
    """

    NAME = 'gnodeclient'

    def __init__(self, options=None, file_name=None, persist_options=False):
        """
        The init function is the only feature that is overridden by this class. The init function
        loads options from a file ('file_name') and updates them with the options ('options') that
        are passed directly as a parameter. I some important options are still missing it will set
        useful defaults for them.

        :param options: A dict of key value pairs, that will complement or override options from the file.
        :type options: dict
        :param file_name: The name of the JSON configuration file.
        :type file_name: str
        :param persist_options: If True, update the configuration file.
        :type persist_options: bool
        """
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
        self['version'] = "0.1.0"
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
            except IOError as e:
                raise e
            finally:
                if fhandle is not None:
                    fhandle.close()
