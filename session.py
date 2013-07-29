#!/usr/bin/env python
import os
import sys
import re
import warnings
import errors
import hashlib
try: 
    import simplejson as json
except ImportError: 
    import json

import tables as tb
import numpy as np

import odml.terminology as terminology

from utils import *
from serializer import Serializer
from browser import Browser
from backend.cache import Cache
from backend.local import Local
from backend.remote import Remote
from models import Meta, Metadata, models_map, supported_models, units_dict, get_type_by_obj

#-------------------------------------------------------------------------------
# common factory functions
#-------------------------------------------------------------------------------

def init(config_file='default.json', models_file='requirements.json'):
    """Initialize session using data specified in a JSON configuration files

    Args:
        config_file: name of the configuration file in which the profile
            to be loaded is contained the standard profile is located at
            default.json

        models_file: name of the configuration file defining models structure

        about the model definitions file: FIXME put here the full description!!

        'data_fields': a dict containing names of data fields for an object as
            keys, and a list of attr names as values like
            [<API_attr_name>, <local_name_setter>, <local_name_getter>]
    """

    try:
        # 1. load profile configuration
        with open(str(config_file), 'r') as f:
            profile_data = json.load(f)

        # 2. load apps and models definitions
        with open(str(models_file), 'r') as f:
            model_data = json.load(f)
        
    except IOError as err:
        raise errors.AbsentConfigurationFileError(err)
    except ValueError as err:
        raise errors.MisformattedConfigurationFileError(err)

    return Session(profile_data, model_data)

#-------------------------------------------------------------------------------
# core Client classes
#-------------------------------------------------------------------------------

class Session( Browser ):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, profile_data, model_data):

        # 1. load meta info: store all settings in Meta class as _meta attribute
        meta = Meta( profile_data, model_data )
        self._meta = meta

        # 2. init Cache and Remote backend
        self._cache = Cache( meta )
        self._remote = Remote( meta )
        self._remote.open() # authenticate at the remote

        # 3. load odML terminologies
        # TODO make odML to load terms into our cache folder, not default /tmp
        terms = terminology.terminologies.load(profile_data['odml_repository'])
        self.terminologies = terms.sections

        # 4. attach supported models
        self.models = dict( models_map )

        warnings.simplefilter('ignore', tb.NaturalNameWarning)
        print "Session initialized."


    def clear_cache(self):
        """ removes all objects from the cache """
        self._cache.clear_cache()

    @activate_remote
    def select(self, model_name, params={}, data_load=False, mode='obj'):
        """ requests objects of a given type from server in bulk mode. 

        caching:    caches files only
        cascade:    no
        data_load:  yes/no

        Arguments:

        model_name: type of the object (like 'block', 'segment' or 'section'.)
        params:     dict that can contain several categories of key-value pairs
        data_load:  fetch the data or not (applied if mode == 'obj')
        mode:       'obj' or 'json' - return mode, python object or JSON

        Params can be:

        1. filters, like:
            'owner__username': 'robert'
            'segment__id__in': [19485,56223,89138]
            'n_definition__icontains': 'blafoo' # negative filter! (has 'n_')

        2. common params, like
            'at_time': '2013-02-22 15:34:57'
            'offset': 50
            'max_results': 20

        3. data params, to get only parts of the original object(s). These only 
            work for the data-related objects (like 'analogsignal' or 
            'spiketrain').

            start_time - start time of the required range (calculated
                using the same time unit as the t_start of the signal)
            end_time - end time of the required range (calculated using
                the same time unit as the t_start of the signal)
            duration - duration of the required range (calculated using
                the same time unit as the t_start of the signal)
            start_index - start index of the required datarange (an index
                of the starting datapoint)
            end_index - end index of the required range (an index of the
                end datapoint)
            samples_count - number of points of the required range (an
                index of the end datapoint)
            downsample - number of datapoints. This parameter is used to
                indicate whether downsampling is needed. The downsampling
                is applied on top of the selected data range using other
                parameters (if specified)

        Examples:
        get('analogsignal', params={'id__in': [38551], 'downsample': 100})
        get('analogsignal', params={'segment__id': 93882, 'start_time': 500.0})
        get('section', params={'odml_type': 'experiment', 'date_created': '2013-02-22'})

        """
        if model_name in self._meta.cls_aliases.values(): # TODO put into model_safe decorator
            model_name = [k for k, v in self._meta.cls_aliases.items() if v==model_name][0]

        if not model_name in self._meta.model_names:
            raise TypeError('Objects of that type are not supported.')

        # fetch from remote + save in cache if possible
        json_objs = self._remote.get_list( model_name, params )

        if mode == 'json':
            # return pure JSON (no data) if requested
            objects = json_objs

        else:
            # convert to objects in 'obj' mode
            app = self._meta.app_prefix_dict[ model_name ]
            model = models_map[ model_name ]

            objects = []
            for json_obj in json_objs:
                data_refs = {} # is a dict like {'signal': <array...>, ...}
                if data_load:
                    data_refs = self.__parse_data_from_json( json_obj )

                obj = Serializer.deserialize( json_obj, self._meta, data_refs )
                objects.append( obj )

        # TODO maybe also add json / memory objects to cache here..
        self._cache.save_cache() # updates on-disk cache with new objects

        return objects


    @activate_remote
    def pull(self, location, params={}, cascade=True, data_load=True):
        """ pulls object from the specified location on the server. 

        caching:    yes
        cascade:    True/False
        data_load:  True/False

        Arguments:

        location:   object location as URL like 
                    'http://<host>/metadata/section/2394/', or just a location 
                    '/metadata/section/2394' or a stripped version like 
                    '/mtd/sec/2394'
        params:     dict that can contain several categories of key-value pairs
        cascade:    fetch related objects recursively (True/False)
        data_load:  fetch the data (True/False)

        Params can be:

        1. common params, like
            'at_time': '2013-02-22 15:34:57'

        2. data params, to get only parts of the original object(s). These only 
            work for the data-related objects (like 'analogsignal' or 
            'spiketrain').

            start_time - start time of the required range (calculated
                using the same time unit as the t_start of the signal)
            end_time - end time of the required range (calculated using
                the same time unit as the t_start of the signal)
            duration - duration of the required range (calculated using
                the same time unit as the t_start of the signal)
            start_index - start index of the required datarange (an index
                of the starting datapoint)
            end_index - end index of the required range (an index of the
                end datapoint)
            samples_count - number of points of the required range (an
                index of the end datapoint)
            downsample - number of datapoints. This parameter is used to
                indicate whether downsampling is needed. The downsampling
                is applied on top of the selected data range using other
                parameters (if specified)

        """
        location = self._meta.clean_location( location )

        processed = {} # collector of processed objects like
                       # {"metadata/section/2394/": <object..>, ...}
        to_clean = [] # collector of ids of objects to clean parent
        stack = [ location ] # a stack of objects to sync

        while len( stack ) > 0:
            loc = stack[0]

            # find object in cache
            etag = None
            if loc in self._cache.objs_map.keys():
                etag = self._cache.objs_map[ loc ]

            # request object from the server (with ETag)
            json_obj = self._remote.get(loc, params, etag)

            if json_obj == 304: # get object from cache
                guid = self._cache.objs_map[ loc ]
                obj = self._cache.objs[ guid ]

                print_status('%s loaded from cache.' % loc)

            else: # request from server

                # download related data
                data_refs = {} # is a dict like {'signal': <array...>, ...}
                if data_load:
                    data_refs = self.__parse_data_from_json( json_obj )

                # parse json (+data) into python object
                obj = Serializer.deserialize( json_obj, self._meta, data_refs )

                # put metadata in the stack
                #if json_obj['fields'].has_key('metadata'):
                #    for value in json_obj['fields']['metadata']:
                #        cl_value = self._meta.clean_location( value )
                #        stack.append( cl_value )

                # or just download attached metadata here?
                # metadata = self._fetch_metadata_by_json(cls, json_obj)

                # save it to cache
                self._cache.add_object( obj )

                print_status("%s fetched from server." % loc)

            stack.remove( loc ) # not to forget to remove processed object
            processed[ loc ] = obj # add it to processed
            self._cache.add_object( obj ) # and to the cache

            app, cls, lid = self._meta.parse_location( loc )
            children = self._meta.app_definitions[cls]['children'] # child object types
            if cascade and children and hasattr(obj, '_gnode'):
                for child in children: # 'child' is like 'segment', 'event' etc.

                    field_name = child + '_set'
                    if obj._gnode['fields'].has_key( field_name ) and \
                        obj._gnode['fields'][ field_name ]:

                        for rel_link in obj._gnode['fields'][ field_name ]:
                            cl_link = self._meta.clean_location( rel_link )

                            if not cl_link in processed.keys() and not cl_link in stack:
                                stack.insert( 0, cl_link )

        # building relationships for python objects
        for loc, obj in processed.items():
            # TODO make some iterator below to avoid duplicate code
            app, cls, lid = self._meta.parse_location( loc )
            children = self._meta.app_definitions[cls]['children'] # child object types
            if cascade and children and hasattr(obj, '_gnode'):  
                for child in children: # 'child' is like 'segment', 'event' etc.

                    field_name = child + '_set'
                    if obj._gnode['fields'].has_key( field_name ) and \
                        obj._gnode['fields'][ field_name ]:

                            rel_objs = []

                            for rel_link in obj._gnode['fields'][ field_name ]:
                                cl_link = self._meta.clean_location( rel_link )
                                guid = self._cache.objs_map[ cl_link ]
                                rel_objs.append( self._cache.objs[ guid ] )

                            if rel_objs: # parse children into parent attrs
                                # a way to assign kids depends on object type
                                self.__assign_child( child, obj, rel_objs )

        """ TODO add metadata to objects 
        # parse related metadata
        if not json_obj['fields'].has_key('metadata') or \
            not json_obj['fields']['metadata']:

        else:
            mobj = Metadata()
            for p, v in raw_json['metadata']:
                prp = Serializer.deserialize(p, self)
                val = Serializer.deserialize(v, self)
                prp.append( val )

                # save both objects to cache
                self._cache.add_object( prp )
                self._cache.add_object( val )

                setattr( mobj, prp.name, prp )
        """

        print_status( 'Object(s) loaded.\n' )
        self._cache.save_cache() # updates on-disk cache with new objects

        guid = self._cache.objs_map[ location ]
        return self._cache.objs[ guid ]


    @activate_remote
    def sync(self, obj_to_sync, cascade=False):
        """ syncs a given object to the server (updates or creates a new one).

        cascade:    True/False

        Arguments:

        obj_to_sync:a python object to sync. If an object has _gnode attribute,
                    it means it will be updated on the server. If no _gnode
                    attribute would be found a new object will be submitted.
        cascade:    sync all children recursively (True/False)
        """

        processed = [] # collector of permalinks of processed objects
        to_clean = [] # collector of ids of objects to clean parent
        stack = [ obj_to_sync ] # a stack of objects to sync

        while len( stack ) > 0:

            obj = stack[0] # take first object from stack
            success = False # flag to indicate success of the syncing
            cls = get_type_by_obj( obj ) # type of the object, like 'segment'

            # bloody workaround for duplications because of NEO
            if hasattr(obj, '_gnode') and obj._gnode['permalink'] in processed:
                stack.remove( obj )
                continue

            # 1. validate class type
            if not obj.__class__ in supported_models:
                # skip this object completely
                stack.remove( obj )
                print_status('Object %s is not supported.\n' % cut_to_render( obj.__repr__() ))
                continue

            # 2. pre-push new/changed array data to the server (+put in cache)
            # data_refs is a dict like {'signal': 'http://host:/neo/signal/148348', ...}
            try:
                data_refs = self.__push_data_from_obj( obj )
            except (errors.FileUploadError, errors.UnitsError), e:
                # skip this object completely
                stack.remove( obj )
                print_status('%s skipped: %s\n' % (cut_to_render(obj.__repr__(), 15), str(e)))
                continue

            # 3. pre-sync related metadata if exists (+put in cache)
            if hasattr(obj, 'metadata'):

                metadata = getattr(obj, 'metadata')
                if isinstance(metadata, Metadata):

                    to_sync = []
                    for name, prp in metadata.__dict__.items():
                        if prp.value:
                            if not hasattr(prp.value, '_gnode'):
                                to_sync.insert(0, prp.value) # sync value if never synced

                            if not hasattr(prp, '_gnode'):
                                to_sync.insert(0, prp) # sync property if never synced
                                if not prp.parent:
                                    print_status('Cannot sync %s for %s: section is not defined.\n' % \
                                        (name, cut_to_render( obj.__repr__() )))
                                    stack.remove( prp )
                                    continue # move to other property

                                if not hasattr(prp.parent, '_gnode'):
                                    to_sync.insert(0, prp.parent) # sync parent section

                    if to_sync: # sync what's needed first
                        stack = to_sync + stack
                        continue

            # 4. sync main object
            try:
                json_obj = Serializer.serialize(obj, self._meta, data_refs)

                # TODO ideally the JSON object representation should be unique
                # and this code excluded
                for k in list( json_obj['fields'].keys() ):
                    if k.endswith('_set') or k == 'shared_with':
                        json_obj['fields'].pop( k, None )

                raw_json = self._remote.save( json_obj )

                if not raw_json == 304:
                    # update local in-memory object with newly acquired params
                    setattr(obj, '_gnode', raw_json)

                # a list of children in the _gnode attribute in all parent 
                # objects for obj must be updated with a newly synced child. it 
                # should be done here, not at the end of the sync, to keep 
                # objects updated in case the sync fails.
                Serializer.update_parent_children(obj, self._meta)

                success = True
                processed.append( obj._gnode['permalink'] )
                print_status('Object at %s synced.' % obj._gnode['location'])

            except (errors.UnitsError, errors.ValidationError, \
                errors.SyncFailed, errors.BadRequestError), e:
                print_status('%s skipped: %s\n' % (cut_to_render(obj.__repr__(), 20), str(e)))

            stack.remove( obj ) # not to forget to remove processed object

            # 5. if cascade put children objects to the stack to sync
            children = self._meta.app_definitions[cls]['children'] # child object types
            if cascade and children and hasattr(obj, '_gnode'):
                for child in children: # 'child' is like 'segment', 'event' etc.

                    # cached children references
                    child_link_set = list( obj._gnode['fields'][ child + '_set' ] )

                    for rel in getattr(obj, get_children_field_name( child )):

                        # detect children of a given type that were removed (using cache)
                        if hasattr(rel, '_gnode') and rel._gnode['permalink'] in child_link_set:
                            child_link_set.remove( rel._gnode['permalink'] )

                        # important to skip already scheduled or processed objs
                        if not (hasattr(rel, '_gnode') and rel._gnode['permalink'] in processed):
                            # and not obj in stack:
                            # stupid NEO!! NEO object can't be compared with any
                            # other object type (error), so the workaround
                            # would be to check if the object was processed 
                            # before processing
                            stack.append( rel )

                    par_name = get_parent_field_name(cls, child)
                    # collect permalinks of removed objects as (link, par_field_name)
                    to_clean += [(x, par_name) for x in child_link_set]

            # save to the cache after processing children, so in case of a 
            # new object it goes to the cache with all children already synced
            if success:
                self._cache.add_object( obj )

        # post-processing:
        # clean objects that were removed from everywhere in this scope
        pure_links = [x[0] for x in to_clean]
        removed = list( set(pure_links) - set(processed) )
        to_clean = [x for x in to_clean if x[0] in removed]

        if to_clean:
            print_status('Cleaning removed objects..')
            for link, par_name in to_clean:

                # TODO make in bulk? could be faster
                location = extract_location( link )
                json_obj = {
                    'location': location,
                    'permalink': link,
                    'fields': {
                        par_name: null
                    }
                }

                self._remote.save( json_obj )
                # here is a question: should cleaned objects be deleted? 
                # otherwise they will stay as 'orphaned' and may pollute object
                # space TODO

        # final output
        print_status('sync done, %d objects processed.\n' % len( processed ))


    def annotate(self, objects, values):
        """ annotates given objects with given values. sends requests to the 
        backend. objects, values - are lists """

        # 1. split given objects by model (class)
        for_annotation = {}
        for obj in objects:
            if not hasattr(obj, '_gnode') or not obj._gnode.has_key('permalink'):
                raise ValidationError('All objects need to be synced ' + \
                    'before annotation.')

            model_name = get_type_by_obj( obj )
            if not model_name in for_annotation.keys():
                for_annotation[ model_name ] = [ obj ]
            else:
                for_annotation[ model_name ].append( obj )

        # 2. build values list to POST
        data = {'metadata': []}
        for value in values:
            if not hasattr(value, '_gnode') or not hasattr(value.parent, '_gnode'):
                raise ValidationError('All properties/values need to be synced before annotation.')
            data['metadata'].append( value._gnode['permalink'] )

        # 3. for every model annotate objects in bulk
        counter = 0
        for model_name, objects in for_annotation.items():

            params = {'id__in': [x._gnode['id'] for x in objects]}
            self._remote.save_list(model_name, json.dumps(data), params=params)

            for obj in objects:

                # 1. update metadata attr in obj._gnode based on values, not 
                # on the response values so not to face the max_results problem
                updated = set(obj._gnode['fields']['metadata'] + \
                    [v._gnode['permalink'] for v in values])
                obj._gnode['fields']['metadata'] = list( updated )

                # 2. update .metadata attribute of an object
                if not hasattr(obj, 'metadata'):
                    setattr(obj, 'metadata', Metadata())

                for p, v in [(v.parent, v) for v in values]:
                    if hasattr(obj.metadata, p.name):
                        # add a value to the existing property
                        new = getattr(obj.metadata, p.name)
                        new.append( v )
                        setattr(obj.metadata, p.name, new)

                    else:
                        # clone new property
                        cloned = p.clone(children=False)
                        cloned.append( v.clone() )
                        setattr( obj.metadata, cloned.name, cloned )

            counter += len(objects)
            print_status('%s(s) annotated.' % model_name)

        print_status('total %d object(s) annotated.\n' % counter)


    def shutdown(self):
        """ Logs out and saves cache. """
        if self._remote.is_active:
            self._remote.close()

        self._cache.save_cache()


    #---------------------------------------------------------------------------
    # helper functions that DO send HTTP requests
    #---------------------------------------------------------------------------

    def __push_data_from_obj(self, obj):
        """ saves array data to disk in HDF5s and uploads new datafiles to the 
        server according to the arrays of the given obj. Saves datafile objects 
        to cache """
        data_refs = {} # collects all references to the related data - output
        model_name = get_type_by_obj( obj )

        data_attrs = self._meta.get_array_attr_names( model_name )

        if not hasattr(obj, '_gnode'): # True if object never synced
            # sync all arrays
            attrs_to_sync = data_attrs

        else:
            # sync only changed arrays
            attrs_to_sync = self.__detect_changed_data_fields( obj )

        for attr in data_attrs: # attr is like 'times', 'signal' etc.

            arr = None
            if attr in attrs_to_sync:
                # 1. get current array and units
                fname = self._meta.app_definitions[model_name]['data_fields'][attr][2]
                if fname == 'self':
                    arr = obj # some NEO objects like signal inherit array
                else:
                    arr = getattr(obj, fname)

            if not type(arr) == type(None): # because of NEO __eq__
                units = Serializer.parse_units(arr)

                datapath = self._cache.save_data(arr)
                json_obj = self._remote.save_data(datapath)

                # update cache
                datalink = json_obj['permalink']
                fid = str(get_id_from_permalink( datalink ))
                self._cache.data_map[ fid ] = datapath

                data_refs[ attr ] = {'data': datalink, 'units': units}

            else:
                data_refs[ attr ] = None

        return data_refs


    def __parse_data_from_json(self, json_obj):
        """ parses incoming json object representation and fetches related 
        object data, either from cache or from the server. """
        app_name, model_name = parse_model( json_obj )

        data_refs = {} # is a dict like {'signal': <array...>, ...}
        for array_attr in self._meta.get_array_attr_names( model_name ):
            arr_loc = json_obj['fields'][ array_attr ]['data']
            if arr_loc == None:
                continue # no data for this attribute

            data_info = self._cache.get_data( arr_loc )
            
            if data_info == None: # no local data, fetch from remote
                cache_dir = self._cache._meta.cache_dir
                data_info = self._remote.get_data( arr_loc, cache_dir )

                if not data_info == None: # raise error otherwise?
                    # update cache with new file
                    self._cache.data_map[ data_info['id'] ] = data_info['path']

            data_refs[ array_attr ] = data_info['data']

        return data_refs

    #---------------------------------------------------------------------------
    # helper functions that DO NOT send HTTP requests
    #---------------------------------------------------------------------------

    def __detect_changed_data_fields(self, obj):
        """ compares all current in-memory data fields (arrays) for a given 
        object with cached (on-disk) versions of these data arrays and returns
        names of the fields where arrays do NOT match """

        if not hasattr(obj, '_gnode'):
            raise TypeError('This object was never synced, cannot detect changes')

        attrs_to_sync = []
        model_name = get_type_by_obj( obj )
        data_fields = self._meta.app_definitions[model_name]['data_fields']
        data_attrs = self._meta.get_array_attr_names( model_name )

        for attr in data_attrs:

            data_value = obj._gnode['fields'][ attr ]['data']

            if data_value:
                data_info = self._cache.get_data( data_value )

                if not data_info == None:
                    # get actual array
                    getter = data_fields[attr][2]
                    if getter == 'self':
                        # some NEO objects like signal inherit array
                        curr_arr = obj
                    else:
                        curr_arr = getattr(obj, getter)

                    if len(curr_arr) < 2:
                        # we treat array with < 2 values as when object was 
                        # fetched without data for performance reasons. in this 
                        # case we ignore this data attribute
                        continue

                    # compare cached (original) and current data
                    if not np.array_equal(data_info['data'], curr_arr):
                        attrs_to_sync.append( attr )

                else: # nothing to compare with!
                    # this could happen when an object was fetched without data.
                    # ignore, treat as data was not changed
                    pass

            else: # no real reference! treat as array was changed
                attrs_to_sync.append( attr )

        return attrs_to_sync

    def __assign_child(self, child, obj, related):
        """ object type-dependent parser adding children to the given obj """

        if child in ['section', 'property', 'value']: # basically odML case

            attr_name = child + 's'
            if child == 'property':
                attr_name = 'properties'
            for rel in related:
                if not rel in getattr(obj, attr_name): # avoid duplicates
                    obj.append( rel )

        else: # here is basically the NEO case

            # 1. assign children to parent as list
            setattr(obj, child + 's', related) # replace all

            # 2. assign parent to every child
            model_name = get_type_by_obj( obj )
            for rel in related:
                setattr(rel, model_name, obj)

        return obj

    #---------------------------------------------------------------------------
    # experimental functions (in development)
    #---------------------------------------------------------------------------

    def delete(self, obj_type, obj_id=None, *kwargs):
        """ delete (archive) one or several objects on the server """
        raise NotImplementedError


    def save_session(self, filename):
        """ Save the data necessary to restart current session (cookies, ...)"""
        raise NotImplementedError


    def load_session(self, filename):
        """Load a previously saved session """
        raise NotImplementedError


    def _bulk_update(self, obj_type, *kwargs):
        """ update several homogenious objects on the server """
        raise NotImplementedError


    def _fetch_metadata_by_json(self, json_obj):
        """ parses incoming json object representation and fetches related 
        object metadata from the server. Returns None or the Metadata object.

        This method is called only when core object is not found in cache, and 
        if metadata should be requested anyway, it could be done faster with 
        this method that uses GET /neo/<obj_type>/198272/metadata/

        Currently not used, because inside the pull function (in cascade mode) 
        it may be faster to collect all metadata after the whole object tree is 
        fetched. For situations, when, say, dozens of of objects tagged with the
        same value are requested, it's faster to fetch this value once at the 
        end rather than requesting related metadata for every object.
        """
        if not json_obj['fields'].has_key('metadata') or \
            not json_obj['fields']['metadata']:
            return None # no metadata field or empty metadata

        url = json_obj['permalink']

        # TODO move requests to the remote class
        resp = requests.get( url + 'metadata' , cookies=self._meta.cookie_jar )
        raw_json = get_json_from_response( resp )

        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        if not raw_json['metadata']: # if no objects exist return empty result
            return None

        mobj = Metadata()
        for p, v in raw_json['metadata']:
            prp = Serializer.deserialize(p, self)
            val = Serializer.deserialize(v, self)
            prp.append( val )

            # save both objects to cache
            self._cache.add_object( prp )
            self._cache.add_object( val )

            setattr( mobj, prp.name, prp )

        return mobj # Metadata object with list of properties (tags)



