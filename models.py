#!/usr/bin/env python

import requests
import neo

from errors import NotInDataStorage, NotBoundToSession
from utils import Property


def Property(func):
    return property(**func())

class BaseObject(object):
    """ Class containing base methods used by Gnode but not present in NEO """
    
    def __init__(self, *args, **kwargs):
        #load to the object the data fields used by the Gnode repo but not by
        # the NEO format
        
        #property from which to derive permalink, used in some of gnode responses
        self._gnode_neo_id = None
        self.permalink = None
        self._permalink_perms = self.permalink + '/acl/'

    #This bit is not really necessary because now these properties assume
    #boolean values; only later on for more sophisticated automatic behavior
    # def _is_instant_change(self):
    #     """ indicates whether object properties are updated immediately or
    #     only upon issuing the save command """
    #     return self._session.instant_change == 'lazy'

    # def _is_rel_lazy(self):
    #     """ indicates whether object relations should be lazy loaded """
    #     return self._session.rel_mode == 'lazy'

    # def _is_data_lazy(self):
    #     """ indicates whether object data should be lazy loaded """
    #     return self._session.data_mode == 'lazy'

    def save(self):
        """ a convenience method to save object from itself """
        self._session.save( obj=self )

    @property
    def permissions(self):
        """Get safety level and list of shared users of an object"""
        if self._safety_level:
            return self._safety_level
        elif self.permalink and self._session:
            perms_resp = requests.get(self._permalink_perms, cookies=self._session.cookie_jar)
            if perms_resp.status_code != 200:
                raise errors.error_codes[perms_resp.status_code]
            else:
                perms_data = perms_resp.json
                self._logged_in_as = perms_data['logged_in_as']
                self._safety_level = perms_data['safety_level']
                self._shared_with = perms_data['shared_with']
            return self._safety_level
        elif self._session:
            raise NotInDataStorage
        else:
            raise NotBoundToSession

    def set_permissions(self, value, recursive=False, notify=False):
        requests.post(self._permalink_perms+'cascade='+str(recursive).lower()+
            '&notify='+int(notify), cookies=auth_cookie)
        self._safety_level = value


    """
    @Property
    def shared_with(self):
        doc = "Information about sharing of the object with other users"

        def fget(self):
            #TODO: use permissions.get_permissions
            pass

        return locals()
    """

class AnalogSignal(neo.core.AnalogSignal, BaseObject):
    """ G-Node Client class for managing Block object """

    self.obj_type = 'analogsignal'

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
    def segments():
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