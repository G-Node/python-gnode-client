#!/usr/bin/env python

import requests
import simplejson as json

import numpy as np
import quantities as pq
import neo

from errors import NotInDataStorage, NotBoundToSession, error_codes
from utils import Property


class BaseObject(object):
    """ Class containing base methods used by Gnode but not present in NEO """

    def __init__(self, permalink=None, session=None):
        """Init BaseObject, setting attributes necessary for Gnode methods"""
        if permalink:
            self.permalink = permalink
            #permalink to access/update object permissions
            self._permalink_perms = self.permalink + '/acl/'
        
        if session:
            self._session = session

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
        self._session.save(obj=self)

    def _fget_permissions(attr):
        def get_any(self):
            """Common getter for attributes safety_level, shared_with, logged_in_as"""
            try:
                return getattr(self, attr)
            except AttributeError:
                try:
                    perms_resp = requests.get(self._permalink_perms, cookies=self._session.cookie_jar)
                    if perms_resp.status_code != 200:
                        raise error_codes[perms_resp.status_code]
                    else:
                        perms_data = perms_resp.json
                        self._logged_in_as = perms_data['logged_in_as']
                        self._safety_level = perms_data['safety_level']
                        self._shared_with = perms_data['shared_with']
                    return getattr(self, attr)
                except AttributeError:
                    if self._session:
                        raise NotInDataStorage
                    else:
                        raise NotBoundToSession
        return get_any

    safety_level = property(fget=_fget_permissions('_safety_level'))
    shared_with = property(fget=_fget_permissions('_shared_with'))
    logged_in_as = property(fget=_fget_permissions('_logged_in_as'))
    


    def set_permissions(self, safety_level=None, shared_with=None, recursive=False,
        notify=False):
        """Change object permissions

        Args:
            safety_level:
                1 -- 'public'
                2 -- 'friendly'
                3 -- 'private'
            shared_with: dictionary with {'user_id' : 'user_permissions'},
                where user_role can be:
                1 -- read-only
                2 -- read and write
        """
        if not safety_level and not shared_with:
            raise errors.EmptyRequest
            
        elif self.permalink and self._session:
            #json.dumps turns True into true, thus respecting the right syntax
            perm_params = {'recursive': json.dumps(recursive),
            'notify': json.dumps(notify)}
            
            perms_data={}
            if safety_level:
                perms_data['safety_level'] = safety_level
            if shared_with:
                perms_data['shared_with'] = shared_with

            resp = requests.post(self._permalink_perms, params=perm_params,
                data=json.dumps(perms_data), cookies=self._session.cookie_jar)

            if resp.status_code != 200:
                raise error_codes[resp.status_code]
            else:
                perms_data = resp.json
                self._logged_in_as = perms_data['logged_in_as']
                self._safety_level = perms_data['safety_level']
                self._shared_with = perms_data['shared_with']
        
        elif self._session:
            raise NotInDataStorage
        else:
            raise NotBoundToSession


class AnalogSignal(neo.core.AnalogSignal, BaseObject):
    """ G-Node Client class for managing Block object """

    def __init__(self, signal, units=None, dtype=None, copy=True,
        t_start=np.array(0.0) * pq.s, sampling_rate=None, sampling_period=None,
        name=None, file_origin=None, description=None, permalink=None,
        session=None):
        super(neo.core.AnalogSignal, self).__init__(signal, units=None,
            dtype=None, copy=True, t_start=np.array(0.0) * pq.s,
            sampling_rate=None, sampling_period=None, name=None,
            file_origin=None, description=None)
        BaseObject.__init__(self, permalink=permalink, session=session)

        self._obj_type = 'analogsignal'
        
        
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