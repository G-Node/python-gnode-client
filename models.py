#!/usr/bin/env python

import requests
import neo

from errors import *
from utils import Property

class BaseObject(object):
    """ Abstract class """

    def __init__(self, *args, **kwargs):
        #load to the object the data fields used by the Gnode repo but not by
        # the NEO format

    def _is_instant_change(self):
        """ update object properties immediately
        """
        return

    def _is_rel_lazy(self):
        """ indicates whether object relations should be lazy loaded """
        return self._session.rel_mode == 'lazy'

    def _is_data_lazy(self):
        """ indicates whether object data should be lazy loaded """
        return self._session.data_mode == 'lazy'

    def save(self):
        """ a convenience method to save object from itself """
        self._session.save( obj=self )

    @Property
    def safety_level(self):
        doc = "Object's safety level"

        #TODO: 

        def fget(self):
            if self._session:
                return self._safety_level
            else:
                raise NotBoundToSession

        def fset(self, value):
            requests.post(self._session.data_url+str(resource_type)+'/'+str(resource_id)+'/acl/?'+
        'cascade='+str(recursive).lower()+'&notify='+int(notify), cookies=auth_cookie))

    @Property
    def shared_with(self):
        doc = "Information about sharing of the object with other users"

        def fget(self):
            #TODO: use permissions.get_permissions
            pass

class AnalogSignal(neo.core.AnalogSignal, BaseObject):
    """ G-Node Client class for managing Block object """

    def __init__(self, *args, **kwargs):
        super(AnalogSignal, self).__init__(*args, **kwargs)

        # assign the session object
        #TODO!: self._session = kwargs.pop('session')

    def __todict__(self):
        """Convert the object into a dictionary that can be passed on to
        the JSON library.
        """
        pass

    @Property
    def segments(self):
        doc = 'Extends basic NEO property to enable lazy mode'

        def fget(self):
            if self._segments: # segments already loaded
                return self._segments
            elif self.id:
                segments = self._session.get('segment', { 'block': self.id })
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

class Block(neo.core.Block, BaseObject):
    """ G-Node Client class for managing Block object """

    def __init__(self, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        # assign the session object
        self._session = kwargs.pop('session')

    def __todict__(self):
        """Convert the object into a dictionary that can be passed on to
        the JSON library.
        """
        pass

    @property
    def segments(self):
        """ Extends basic NEO property to enable lazy mode """

        def fget(self):
            if self._segments: # segments already loaded
                return self._segments
            elif self.id:
                segments = self._session.get('segment', { 'block': self.id })
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

class SpikeTrain(neo.core.SpikeTrain, BaseObject):
    """ G-node Client class for managing a SpikeTrain object """

    def __init__(self, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        self._session = kwargs.pop('session')