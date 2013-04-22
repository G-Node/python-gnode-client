from utils import *


class Browser(object):
    """ ABSTRACT class, implements cmd-type operations like ls, cd etc."""

    ls_config = {
        'ls_filt': {}, # dispslay filters
        'location': '', # current location, like 'metadata/section/293847/'
        'mode': 'metadata', # browsing by metadata is default
        'modes': ['data', 'metadata'] # could browse in data mode too
    }

    def local(self, location=None, filt={}):
        return self._ls(location, remote=False, filt={})


    def remote(self, location=None, filt={}):
        return self._ls(location, remote=True, filt={})


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


    def _ls(self, location=None, remote=False, filt={}):
        """ cmd-type ls function for both remote and local """
        out = '' # output
        params = dict( self.ls_config['ls_filt'].items() + filt.items() )

        # case a) some model given, output results of the filtered selection 
        if location in self._meta.model_names:
            objs = self.select(location, params=params, remote=remote)
            out = self._render( objs, out )

        # case b) output contents of a given location
        else:
            if not location: # if not given use the current one
                location = self.ls_config['location']

            if location:
                out += 'location %s:\n' % location
                app, cls, lid = self._meta.parse_location( location )

                for child in self._meta.app_definitions[ cls ]['children']:

                    parent_name = get_parent_field_name(cls, child)
                    params[ parent_name + '__id' ] = lid
                    objs = self.select(child, params=params, remote=remote)

                    out = self._render( objs, out )
                    params.pop( parent_name + '__id' )

                # FIXME? exception case for Block -> Section
                if cls == 'section':
                    params[ 'section__id' ] = lid
                    objs = self.select('block', params=params, remote=remote)
                    if objs:
                        out += '\nDATA:\n'
                        out = self._render( objs, out )

            else:
                if self.ls_config['mode'] == 'data':
                    objs = self.select('block', params=params, remote=remote)

                else: # metadata mode otherwise
                    params['parent_section__isnull'] = 1
                    objs = self.select('section', params=params, remote=remote)

                out = self._render( objs, out )

        print_status( out )


    def _render(self, objs, out):
        """ renders a list of objects for a *nice* output """
        for obj in objs:

            # object location
            location = extract_location( obj._gnode['permalink'] )
            out += self._meta.strip_location(location) + '\t'

            # safety level
            out += str(obj._gnode['fields']['safety_level']) + ' '

            # object owner
            out += extract_location( obj._gnode['fields']['owner'] ) + '\t'

            # object __repr__
            out += obj.__repr__()[ : self._meta.max_line_out ] + '\n'

        return out

