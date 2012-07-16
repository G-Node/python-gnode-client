import neo
from errors import *


class BaseObject( object ):
    """ Absract class """

    def _is_rel_lazy(self):
        """ indicates whether object relations should be lazy loaded """
        return self._session.rel_mode == 'lazy'

    def _is_data_lazy(self):
        """ indicates whether object relations should be lazy loaded """
        return self._session.data_mode == 'lazy'

    def save(self):
        """ a convenience method to save object from itself """
        self._session.save( obj=self )


class Block( neo.core.Block, BaseObject ):
    """ G-Node Client class for managing Block object """

    def __init__( self, *args, **kwargs ):
        super( Block, self ).__init__( *args, **kwargs )
        # assign the session object
        self._session = kwargs.pop('session')

    @property
    def segments
        """ Extends basic NEO property to enable lazy mode """

        def fget(self):
            if self._segments: # segments already loaded
                return self._segments
            elif self.id:
                segments = self._session.get( 'segment', { 'block': self.id } )
            else:
                return None

        def fset(self, segments):
            try:
                # make an update as one transaction
                self._session.bulk_update('segment', id__in = \
                    [s.id for s in segments] )
                self._segments = segments

            except IOError: # connection error 
                raise ConnectionError # TBD

        def fdel(self):
            del self._segments

        return locals()
