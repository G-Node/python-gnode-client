from utils import *

# TODO configure logger to print to the stdout


class Browser(object):
    """ 
    use this class to browse objects at the remote with cmd-type operations
    like 'ls'and 'cd'. No objects are returned, only nice output.
    """

    def __init__(self, session):
        self.session = session
        self.ls_config = {
            'ls_filt': {}, # dispslay filters
            'location': '', # current location, like 'metadata/section/293847/'
            'mode': 'metadata', # browsing by metadata is default
            'modes': ['data', 'metadata'] # can browse in data mode too
        }

    def cd(self, location=''):
        """ cmd-type 'cd' function to change the current location """
        if location == '':
            self.ls_config['location'] = ''
            print 'back to root'

        else:
            url = str( location )
            if is_permalink( location ):
                url = url.replace(self.session._meta.host, '')

            obj = self.session.pull(url, cascade=False, data_load=False)

            self.ls_config['location'] = url
            print "entered %s" % url


    def ls(self, location=None, filt={}):
        """ cmd-type 'ls' function to browse objects at the remote """
        meta = self.session._meta
        select = self.session.select
        out = '' # output
        params = dict( self.ls_config['ls_filt'].items() + filt.items() )

        # case a) some model given, output results of the filtered selection 
        if location in meta.model_names:
            objs = select(location, params=params, mode='json')
            out = self._render( objs, out )

        # case b) output contents of a given location
        else:
            if not location: # if not given use the current one
                location = self.ls_config['location']

            if location:
                out += 'location %s:\n' % location
                loc = meta.parse_location( location )
                app, cls, lid = loc[0], loc[1], loc[2]

                for child in meta.app_definitions[ cls ]['children']:
                    # TODO fetch children only if not empty? can be done by 
                    # pre-fetching location and parsing children attrs. makes
                    # sense only for more than one children objects, like
                    # segment, section, etc.

                    parent_name = get_parent_field_name(cls, child)
                    params[ parent_name + '__id' ] = lid
                    objs = select(child, params=params, mode='json')

                    out = self._render( objs, out )
                    params.pop( parent_name + '__id' )

                # TODO exception case for Block -> Section
                if cls == 'section':
                    params[ 'section__id' ] = lid
                    objs = select('block', params=params, mode='json')
                    if objs:
                        out += '\nDATA:\n'
                        out = self._render( objs, out )

            else:
                if self.ls_config['mode'] == 'data':
                    objs = select('block', params=params, mode='json')

                else: # metadata mode otherwise
                    params['parent_section__isnull'] = 1
                    objs = select('section', params=params, mode='json')

                out = self._render( objs, out )

        print_status( out )


    def __tree(self, location=None, filt={}):
        raise NotImplementedError
        out = '' # output
        tree = {} # json-type object tree

        # filters could be also applicable
        #params = dict( self.ls_config['ls_filt'].items() + filt.items() )

        if not location: # if not given use the current one
            location = self.ls_config['location']

        if location:
            out += 'tree at %s:\n' % location

            app, cls, lid = self._meta.parse_location( location )
            obj = self.select(cls, {"id__in": [lid]})

            for child in self._meta.app_definitions[ cls ]['children']:
                # TODO fetch children only if not empty? can be done by 
                # pre-fetching location and parsing children attrs. makes
                # sense only for more than one children objects, like
                # segment, section, etc.

                parent_name = get_parent_field_name(cls, child)
                params[ parent_name + '__id' ] = lid
                objs = self.select(child, params=params)

                out = self._render( objs, out )
                params.pop( parent_name + '__id' )

            # FIXME? exception case for Block -> Section
            if cls == 'section':
                params[ 'section__id' ] = lid
                objs = self.select('block', params=params)
                if objs:
                    #out += '\nDATA:\n'
                    out = self._render( objs, out )

        else:
            print "you're at the root. some location has to be specified."


    def _render(self, objs, out):
        """ renders a list of objects for a *nice* output """
        for obj in objs:
            fields = obj['fields']

            # object location
            out += self.session._meta.parse_location( obj['location'] ).stripped + ' '

            # safety level
            out += str( fields['safety_level'] ) + ' '

            # object owner
            out += extract_location( fields['owner'] ) + '\t'

            # object size
            obj_size = str( obj ).__sizeof__()
            if fields.has_key( 'data_size' ) and fields['data_size']:
                obj_size += int( fields['data_size'] )

            out += sizeof_fmt( obj_size ) + '\t'
            if fields.has_key( 'name' ):
                name = fields['name']
            else:
                name = obj.__repr__()
            out += name[ : self.session._meta.max_line_out ] + '\n'

        return out

