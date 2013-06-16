from utils import *


class Browser(object):
    """ ABSTRACT class, implements cmd-type operations like ls, cd etc."""

    ls_config = {
        'ls_filt': {}, # dispslay filters
        'location': '', # current location, like 'metadata/section/293847/'
        'mode': 'metadata', # browsing by metadata is default
        'modes': ['data', 'metadata'] # could browse in data mode too
    }

    def cd(self, location=''):
        """ changes the current location within the data structure """
        if location == '':
            self.ls_config['location'] = ''
            print 'back to root'

        else:
            # 1. compile url
            url = str( location )
            if is_permalink( location ):
                url = url.replace(self._meta.host, '')

            # 2. get the object at the location
            obj = self.pull(url, cascade=False, data_load=False)

            self.ls_config['location'] = url
            print "entered %s" % url


    def ls(self, location=None, filt={}):
        """ cmd-type ls function to browse objects at the remote """
        out = '' # output
        params = dict( self.ls_config['ls_filt'].items() + filt.items() )

        # case a) some model given, output results of the filtered selection 
        if location in self._meta.model_names:
            objs = self.select(location, params=params)
            out = self._render( objs, out )

        # case b) output contents of a given location
        else:
            if not location: # if not given use the current one
                location = self.ls_config['location']

            if location:
                out += 'location %s:\n' % location
                app, cls, lid = self._meta.parse_location( location )

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
                        out += '\nDATA:\n'
                        out = self._render( objs, out )

            else:
                if self.ls_config['mode'] == 'data':
                    objs = self.select('block', params=params)

                else: # metadata mode otherwise
                    params['parent_section__isnull'] = 1
                    objs = self.select('section', params=params)

                out = self._render( objs, out )

        print_status( out )


    def __tree(self, location=None, filt={}):
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
                    out += '\nDATA:\n'
                    out = self._render( objs, out )

        else:
            print "you're at the root. some location has to be specified."



    def _render(self, objs, out):
        """ renders a list of objects for a *nice* output """
        for obj in objs:
            fields = obj._gnode['fields']

            # object location
            out += self._meta.strip_location( obj._gnode['location'] ) + '\t'

            # safety level
            out += str( fields['safety_level'] ) + ' '

            # object owner
            out += extract_location( fields['owner'] ) + '\t'

            # object size
            obj_size = str( obj._gnode ).__sizeof__()
            if fields.has_key( 'data_size' ):
                obj_size += int( fields['data_size'] )

            out += sizeof_fmt( obj_size ) + '\t'

            # object __repr__
            out += obj.__repr__()[ : self._meta.max_line_out ] + '\n'

        return out

