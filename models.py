#!/usr/bin/env python

import requests
import simplejson as json

import numpy as np
import quantities as pq
import neo
from neo.core import *
from odml.section import BaseSection
from odml.property import BaseProperty
from odml.value import BaseValue
from errors import NotInDataStorage, NotBoundToSession, error_codes

from utils import *

units_dict = {
    'V': pq.V,
    'mV': pq.mV,
    'uV': pq.uV,
    's': pq.s,
    'ms': pq.ms,
    'us': pq.us,
    'MHz': pq.MHz,
    'kHz': pq.kHz,
    'Hz': pq.Hz,
    '1/s': pq.Hz
}

models_map = {
    'section': BaseSection,
    'property': BaseProperty,
    'value': BaseValue,
    'block': Block,
    'segment': Segment,
    'event': Event,
    'eventarray': EventArray,
    'epoch': Epoch,
    'epocharray': EpochArray,
    'unit': Unit,
    'spiketrain': SpikeTrain,
    'analogsignal': AnalogSignal,
    'analogsignalarray': AnalogSignalArray,
    'irsaanalogsignal': IrregularlySampledSignal,
    'spike': Spike,
    'recordingchannelgroup': RecordingChannelGroup,
    'recordingchannel': RecordingChannel
}

supported_models = models_map.values()

class Metadata(object):
    """ class containing metadata property-value pairs for a single object. """

    def __repr__(self):
        out = ''
        for p_name, prp in self.__dict__.items():
            property_out = cut_to_render( p_name, 20 )
            value_out = cut_to_render( str(prp.value.data) )
            out += '%s: %s\n' % ( property_out, value_out )
        return out


class BaseObject(object):
    """ Class containing base methods used by Gnode but not present in NEO """

    def __init__(self, permalink=None, session=None, file_origin_id=None):
        """Init BaseObject, setting attributes necessary for Gnode methods"""
        if permalink:
            self.permalink = permalink
            #permalink to access/update object permissions
            self._permalink_perms = self.permalink + '/acl/'
        
        if session:
            self._session = session

        self._file_origin_id = file_origin_id

        if file_origin_id and session:
            self._file_origin_id = file_origin_id
            self._file_origin = session.files_url+str(file_origin_id)+'/download/'

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

    def download_original_file(self, file_name):
        """Download original data file where object was extracted from.

        Args:
            file_name: string containing name of the file to save
        """
        try:
            resp = requests.get(self.file_origin,
                cookies=self._session.cookie_jar)
        except AttributeError:
            raise errors.NotBoundToSession

        with open(file_name, 'wb') as file:
            file.write(resp.content)

class BaseDataObject(object):
    """ Base Object to be inherited by the objects containing data so that
    they can implement lazy loading and correct representations"""
    
    def __init__(self, datafile_url=None, signal_size=None):
        self._datafile_url = datafile_url

    def __call__(self):
        #we want to support lazy loading here
        if not self:
            data_array = self._get_data_array()
            #this bit was adapted from the NEO way of for example rescaling
            #   arrays
            new = self.__class__(signal=data_array, units=self.units,
                sampling_rate=self.sampling_rate)
            new._copy_data_complement(self)
            new.annotations.update(self.annotations)
            self = new
            return self
        else:
            return self


    def __len__(self):
        #we want to get the right length for that object
        pass

    def _get_data_array(self):
        """Method to retrieve a NumPy array containing the signal data.

        It first checks for the existance of the file in the cache directory.
        """
        file_req = request_file = requests.get(self.datafile_url,
            cookies=session.cookie_jar, prefetch=False)
        
        headers = file_req.headers
        content_disposition = headers['content-disposition']
        filename = content_disposition.split('filename=')[-1]
        
        #do the same trick browsers do to resolve filenames with
        # a forward slash
        filename = filename.replace('/', '_')
        
        try:
            hdf5_file = tables.openFile(os.path.join(session.cache_dir,
                filename), 'r')
            array = np.array(hdf5_file.listNodes('/')[0])
        except:
            filepath = os.path.join(session.cache_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(file_req.content)
            hdf5_file = tables.openFile(os.path.join(session.cache_dir,
                filename), 'r')
            array = np.array(hdf5_file.listNodes('/')[0])
        finally:
            hdf5_file.close()

        return array



class AnalogSignal(neo.core.AnalogSignal, BaseObject, BaseDataObject):
    """ G-Node Client class for managing Block object """
    def __init__(self, signal, units=None, dtype=None, copy=True,
        t_start=0 * pq.s, sampling_rate=None, sampling_period=None,
        name=None, file_origin=None, description=None, permalink=None,
        session=None, file_origin_id=None, datafile_url=None,
        signal__units=None):
        super(AnalogSignal, self).__init__(signal, units=units,
            dtype=dtype, copy=copy, t_start=t_start,
            sampling_rate=sampling_rate, sampling_period=sampling_period,
            name=name, file_origin=file_origin, description=description)
        BaseObject.__init__(self, permalink=permalink, session=session,
            file_origin_id=file_origin_id)
        BaseDataObject.__init__(self, datafile_url=datafile_url,
            signal__units=signal__units)
        self._obj_type = 'analogsignal'
        
    def __repr__(self):
        #TODO have a pretty print here
        return super(AnalogSignal, self).__repr__(self)
    
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

    def __init__(self, times, t_stop, units=None, copy=True,
        sampling_rate=1.0 * pq.Hz, t_start=0.0 * pq.s, waveforms=None,
        left_sweep=None, name=None, file_origin=None, description=None,
        permalink=None, session=None, file_origin_id=None):
        super(neo.core.SpikeTrain, self).__init__(times=times, t_stop=t_stop,
            units=units, copy=copy, sampling_rate=sampling_rate,
            t_start=t_start, waveforms=waveforms, left_sweep=left_sweep,
            name=name, file_origin=file_origin, description=description)
        BaseObject.__init__(self, permalink=permalink, session=session,
            file_origin_id=file_origin_id)

        self._obj_type = 'spiketrain'
        

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
