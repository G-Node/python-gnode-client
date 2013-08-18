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
import odml

from utils import *
from serializer import Serializer
from browser import Browser
from backend.cache import Cache
from backend.remote import Remote
from models import Meta, Metadata, models_map, supported_models, units_dict

#-------------------------------------------------------------------------------
# core Client classes
#-------------------------------------------------------------------------------

class Session(object):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, config_file='conf.json'):
        """ creates session using data specified in a JSON configuration files

        config_file: name of the configuration file in which the profile to be 
                     loaded is contained the standard profile is located at
                     default.json

        models_file: name of the configuration file defining models structure"""
        try:
            with open(str(config_file), 'r') as f:
                profile_data = json.load(f)

        except IOError as err:
            raise errors.AbsentConfigurationFileError(err)
        except ValueError as err:
            raise errors.MisformattedConfigurationFileError(err)

        meta = Meta( profile_data )
        self._meta = meta

        self.cache = Cache( meta )
        self._remote = Remote( meta )
        self._remote.open() # authenticate at the remote

        # TODO make odML to load terms into our cache folder, not default /tmp
        terms = odml.terminology.terminologies.load(profile_data['odml_repository'])
        self.terminologies = terms.sections
        self.models = dict( models_map )

        warnings.simplefilter('ignore', tb.NaturalNameWarning)
        print "Session initialized."


    def __del__(self):
        self.cache.save_all()


    def clear_cache(self):
        """ removes all objects from the cache """
        self.cache.clear_cache()


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
        def clean_params(params):
            filt = {}
            for k, v in params.items():
                if v.__class__ in  self._meta.models_map.values():
                    val_descr = self._meta.get_gnode_descr(v)
                    if not val_descr:
                        raise ValidationError('All models need to be synced ' + \
                            'before making a query.')
                    filt[k] = val_descr['id']
                else:
                    filt[k] = v
            return filt

        if model_name in self._meta.cls_aliases.values(): # TODO put into model_safe decorator
            model_name = [k for k, v in self._meta.cls_aliases.items() if v==model_name][0]

        if not model_name in self._meta.models_map.keys():
            raise TypeError('Objects of that type are not supported.')
        if model_name == 'datafile' and not data_load and not mode == 'json':
            raise TypeError('Datafiles cannot be fetched if data_load=False.')
                
        filt = clean_params(params)
        json_objs = self._remote.get_list(model_name, filt)

        if mode == 'json':
            objects = json_objs # return pure JSON (no data) if requested

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

        self.cache.save_data_map() # updates on-disk cache with new datafiles

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
        location = self._meta.parse_location( location )
        supp_models = [k for k in models_map.keys() if \
            not k in ['property', 'value']]
        if not location[1] in supp_models:
            raise TypeError('Objects of that type are not pull-supported.')

        processed = {} # collector of processed objects like
                       # {"metadata/section/2394/": <object..>, ...}
        to_clean = [] # collector of ids of objects to clean parent
        stack = [ location ] # a stack of objects to sync

        while len( stack ) > 0:
            loc = stack[0]

            # find object in cache
            etag = None
            cached_obj = self.cache.get( loc )
            if not type(cached_obj) == type(None):
                obj_descr = self._meta.get_gnode_descr(cached_obj)
                if obj_descr and obj_descr['fields'].has_key('guid'):
                    etag = obj_descr['fields']['guid']

            # request object from the server (with ETag)
            json_obj = self._remote.get(loc, params, etag)

            if json_obj == 304: # get object from cache
                obj = cached_obj
                print_status('%s loaded from cache.' % str(loc))

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
                
                print_status("%s fetched from server." % loc)

            stack.remove( loc ) # not to forget to remove processed object
            processed[ str(loc) ] = obj # add it to processed

            app, cls, lid = loc[0], loc[1], loc[2]
            children = self._meta.app_definitions[cls]['children'] # child object types
            obj_descr = self._meta.get_gnode_descr(obj)
            if cascade and children and obj_descr:
                for child in children: # 'child' is like 'segment', 'event' etc.

                    field_name = child + '_set'
                    if obj_descr['fields'].has_key( field_name ) and \
                        obj_descr['fields'][ field_name ]:

                        for rel_link in obj_descr['fields'][ field_name ]:
                            cl_link = self._meta.parse_location( rel_link )

                            if not str(cl_link) in processed.keys() and not \
                                str(cl_link) in [str(o) for o in stack]:
                                stack.insert( 0, cl_link )

        # building relationships for python objects
        for key, obj in processed.items():
            # TODO make some iterator below to avoid duplicate code
            loc = self._meta.parse_location( key )
            app, cls, lid = loc[0], loc[1], loc[2]
            children = self._meta.app_definitions[cls]['children']
            obj_descr = self._meta.get_gnode_descr(obj)
            if cascade and children and obj_descr:  
                for child in children: # 'child' is like 'segment', 'event' etc.

                    field_name = child + '_set'
                    if obj_descr['fields'].has_key( field_name ) and \
                        obj_descr['fields'][ field_name ]:

                            rel_objs = []

                            for rel_link in obj_descr['fields'][ field_name ]:
                                cl_link = self._meta.parse_location( rel_link )
                                rel_objs.append( processed[str(cl_link)] )

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
                self.cache.push( prp )
                self.cache.push( val )

                setattr( mobj, prp.name, prp )
        """
        obj = processed[ str(location) ]
        self.cache.push(obj)
        self.cache.save_data_map()

        print_status( 'Object(s) loaded.\n' )
        return obj


    @activate_remote
    def push(self, obj_to_sync, cascade=False, force_update=False):
        """ syncs a given object to the server (updates or creates a new one).

        cascade:    True/False

        Arguments:

        obj_to_sync:    a python object to sync. If an object has gnode 
                        attribute, it means it will be updated on the server. If
                        no gnode attribute is found a new object will be 
                        submitted.
        cascade:        sync all children recursively (True/False)
        force_update:   overwrites changes on the remote, if any.
        """
        supp_models = [m for k, m in models_map.items() if \
            not k in ['property', 'value']]
        if not obj_to_sync.__class__ in supp_models:
            raise TypeError('Objects of that type are not supported.')

        processed = [] # collector of permalinks of processed objects
        to_clean = [] # collector of ids of objects to clean parent
        to_update_refs = [] # collector of parent-type objs to update etags
        stack = [ obj_to_sync ] # a stack of objects to sync

        self.cache.push(obj_to_sync) # if not yet there

        while len( stack ) > 0:

            obj = stack[0] # take first object from stack
            success = False # flag to indicate success of the syncing
            cls = self._meta.get_type_by_obj( obj ) # type of the object, like 'segment'

            # bloody workaround for duplications because of NEO
            obj_descr = self._meta.get_gnode_descr(obj)
            if obj_descr and obj_descr['permalink'] in processed:
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
                            if not self._meta.get_gnode_descr(prp.value):
                                to_sync.insert(0, prp.value) # sync value if never synced

                            if not self._meta.get_gnode_descr(prp):
                                to_sync.insert(0, prp) # sync property if never synced
                                if not prp.parent:
                                    print_status('Cannot sync %s for %s: section is not defined.\n' % \
                                        (name, cut_to_render( obj.__repr__() )))
                                    stack.remove( prp )
                                    continue # move to other property

                                if not self._meta.get_gnode_descr(prp.parent):
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

                raw_json = self._remote.save(json_obj, force_update=force_update)

                if not raw_json == 304:
                    # update local in-memory object with newly acquired params
                    self._meta.set_gnode_descr(obj, raw_json)
                    if self._meta.is_container(cls):
                        to_update_refs.append(obj)

                # a list of children in the gnode attribute in all parent 
                # objects for obj must be updated with a newly synced child. it 
                # should be done here, not at the end of the sync, to keep 
                # objects updated in case the sync fails. 
                Serializer.update_parent_children(obj, self._meta)

                success = True
                obj_descr = self._meta.get_gnode_descr(obj)
                processed.append( obj_descr['permalink'] )
                print_status('Object at %s synced.' % obj_descr['location'])

            except (errors.UnitsError, errors.ValidationError, \
                errors.SyncFailed, errors.BadRequestError), e:
                print_status('%s skipped: %s\n' % (cut_to_render(obj.__repr__(), 20), str(e)))

            stack.remove( obj ) # not to forget to remove processed object

            # 5. if cascade put children objects to the stack to sync
            children = self._meta.app_definitions[cls]['children'] # child object types
            obj_descr = self._meta.get_gnode_descr(obj)
            if cascade and children and obj_descr:
                for child in children: # 'child' is like 'segment', 'event' etc.

                    # cached children references
                    child_link_set = list( obj_descr['fields'][ child + '_set' ] )

                    for rel in getattr(obj, get_children_field_name( child )):

                        # detect children of a given type that were removed (using cache)
                        rel_descr = self._meta.get_gnode_descr(rel)
                        if rel_descr and rel_descr['permalink'] in child_link_set:
                            child_link_set.remove( rel_descr['permalink'] )

                        # important to skip already scheduled or processed objs
                        if not (not (rel_descr == None) and rel_descr['permalink'] in processed):
                            # and not obj in stack:
                            # stupid NEO!! NEO object can't be compared with any
                            # other object type (error), so the workaround
                            # would be to check if the object was processed 
                            # before processing
                            stack.append( rel )

                    par_name = get_parent_field_name(cls, child)
                    # collect permalinks of removed objects as (link, par_field_name)
                    to_clean += [(x, par_name) for x in child_link_set]

        # post-processing:
        # clean objects that were removed from everywhere in this scope
        pure_links = [x[0] for x in to_clean]
        removed = list( set(pure_links) - set(processed) )
        to_clean = [x for x in to_clean if x[0] in removed]

        if to_clean:
            print_status('Cleaning removed objects..')
            for link, par_name in to_clean:

                # TODO make in bulk? could be faster
                location = str(self._meta.parse_location(link))
                json_obj = {
                    'location': location,
                    'permalink': link,
                    'fields': {
                        par_name: null
                    }
                }

                self._remote.save(json_obj, force_update=force_update)
                # here is a question: should cleaned objects be deleted? 
                # otherwise they will stay as 'orphaned' and may pollute object
                # space TODO

        # because of the API feature of updating a parent's guid with every 
        # object update 'parent'-type objects after sync may have outdated 
        # guids, which could be solved by pulling all object at the end of the
        # sync (below) or better remove this feature on the API level.
        print_status('updating object references..')
        for obj in to_update_refs:
            self.__update_gnode_attr(obj) # update all eTags from the remote
        self.cache.save_all() # save updated etags etc.

        # final output
        print_status('sync done, %d objects processed.\n' % len( processed ))


    @activate_remote
    def annotate(self, objects, values):
        """ annotates given objects with given values. sends requests to the 
        backend. objects, values - are lists """

        # 1. split given objects by model (class)
        for_annotation = {}
        for obj in objects:
            obj_descr = self._meta.get_gnode_descr(obj)
            if not obj_descr or not obj_descr.has_key('permalink'):
                raise ValidationError('All objects need to be synced ' + \
                    'before annotation.')

            model_name = self._meta.get_type_by_obj( obj )
            if not model_name in for_annotation.keys():
                for_annotation[ model_name ] = [ obj ]
            else:
                for_annotation[ model_name ].append( obj )

        # 2. build values list to POST
        data = {'metadata': []}
        for value in values:
            val_descr = self._meta.get_gnode_descr(value)
            if not val_descr or not self._meta.get_gnode_descr(value.parent):
                raise ValidationError('All properties/values need to be synced before annotation.')
            data['metadata'].append( value._gnode['permalink'] )

        # 3. for every model annotate objects in bulk
        counter = 0
        for model_name, objects in for_annotation.items():

            params = {'id__in': [self._meta.get_gnode_descr(x)['id'] for x in objects]}
            self._remote.save_list(model_name, json.dumps(data), params=params)

            for obj in objects:
                obj_descr = self._meta.get_gnode_descr(obj)

                # 1. update metadata attr in gnode based on values, not 
                # on the response values so not to face the max_results problem
                updated = set(obj_descr['fields']['metadata'] + \
                    [self._meta.get_gnode_descr(v)['permalink'] for v in values])
                obj_descr['fields']['metadata'] = list( updated )

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

        self.cache.save_all()


    #---------------------------------------------------------------------------
    # helper functions that DO send HTTP requests
    #---------------------------------------------------------------------------

    def __push_data_from_obj(self, obj):
        """ saves array data to disk in HDF5s and uploads new datafiles to the 
        server according to the arrays of the given obj. Saves datafile objects 
        to cache """
        data_refs = {} # collects all references to the related data - output
        model_name = self._meta.get_type_by_obj( obj )

        if model_name == 'datafile':
            if not self._meta.get_gnode_descr(obj): # otherwise already uploaded
                json_obj = self._remote.save_data(obj.path)
                
                # update cache data map
                datalink = json_obj['permalink']
                fid = str(get_id_from_permalink( datalink ))
                self.cache.update_data_map(fid, obj.path)
                self._meta.set_gnode_descr(obj, json_obj)
                
            return data_refs

        data_attrs = self._meta.get_array_attr_names( model_name )
        attrs_to_sync = self.cache.detect_changed_data_fields( obj )

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

                datapath = self.cache.save_data(arr)
                json_obj = self._remote.save_data(datapath)

                # update cache data map
                datalink = json_obj['permalink']
                fid = str(get_id_from_permalink( datalink ))

                folder, tempname = os.path.split(datapath)
                new_path = os.path.join(folder, fid + tempname[tempname.find('.'):])
                os.rename(datapath, new_path)
                self.cache.update_data_map(fid, new_path)

                data_refs[ attr ] = {'data': datalink, 'units': units}

            else:
                data_refs[ attr ] = None

        return data_refs


    def __parse_data_from_json(self, json_obj):
        """ parses incoming json object representation and fetches related 
        object data, either from cache or from the server. """
        def fetch_data(location):
            location = self._meta.parse_location(location)
            data_info = self.cache.get_data(location)
            
            if data_info == None: # no local data, fetch from remote
                cache_dir = self.cache._meta.cache_dir
                data_info = self._remote.get_data(location, cache_dir)

                if not data_info == None: # raise error otherwise?
                    # update cache with new file
                    self.cache.update_data_map(data_info['id'], data_info['path'])
            return data_info

        app_name, model_name = parse_model( json_obj )
        data_refs = {} # is a dict like {'signal': <array...>, ...}

        if model_name == 'datafile':
            location = json_obj['permalink']
            data_info = fetch_data(location)
            data_refs['path'] = data_info['path']
        else:
            for data_attr in self._meta.get_array_attr_names( model_name ):
                location = json_obj['fields'][ data_attr ]['data']
                if location == None:
                    continue # no data for this attribute
                data_info = fetch_data(location)
                data_refs[ data_attr ] = data_info['data']

        return data_refs


    def __assign_child(self, child, obj, related):
        """ object type-dependent parser adding children to the given obj """

        if child in ['section', 'property', 'value']: # basically odML case

            attr_name = child + 's'
            if child == 'property':
                attr_name = 'properties'
            for rel in related:
                if not rel in getattr(obj, attr_name): # avoid duplicates
                    obj.append( rel )
                    
        elif child in ['datafile']:
            for rel in related:
                obj.add_file(rel)

        else: # here is basically the NEO case

            # 1. assign children to parent as list
            setattr(obj, child + 's', related) # replace all

            # 2. assign parent to every child
            model_name = self._meta.get_type_by_obj( obj )
            for rel in related:
                setattr(rel, model_name, obj)

        return obj


    def __update_gnode_attr(self, obj):
        """ non-recursive update of a gnode attribute for a given object """
        json_obj = self._meta.get_gnode_descr(obj)
        if not json_obj:
            raise AttributeError("Object %s was never synced. Can't update gnode attribute." % str(obj))
        obj_type = self._meta.parse_location(json_obj['location'])[1]
        new_json = self.select(obj_type, {"id": json_obj['id']}, mode="json")[0]
        self._meta.set_gnode_descr(obj, new_json)
    
    #---------------------------------------------------------------------------
    # experimental functions (in development)
    #---------------------------------------------------------------------------

    @activate_remote
    def delete(self, obj_type, obj_id=None, *kwargs):
        """ delete (archive) one or several objects on the server """
        raise NotImplementedError


    @activate_remote
    def set_permissions(self, location, level=None, acl={}):
        """ updates object acl and / or access level """
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
            self.cache.push( prp )
            self.cache.push( val )

            setattr( mobj, prp.name, prp )

        return mobj # Metadata object with list of properties (tags)



