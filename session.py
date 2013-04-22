#!/usr/bin/env python
import os, sys
import re

import hashlib
try: 
    import simplejson as json
except ImportError: 
    import json

import tables as tb
import numpy as np

import odml.terminology as terminology

import warnings
import errors
from utils import *
from serializer import Serializer
from browser import Browser
from cache import Cache
from backend.backends import Local, Remote
from models import Metadata, models_map, supported_models, units_dict, get_type_by_obj


#-------------------------------------------------------------------------------
# common wrapper functions
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

class Meta( object ):
    """ abstract class to handle settings, auth information for Session """

    def get_array_attr_names(self, model_name):
        """ return attr names that are arrays with ndim > 0 """
        data_fields = self.app_definitions[model_name]['data_fields']

        # FIXME dirty alternative
        names = [n for n in data_fields if n in ['times', 'durations', \
            'signal', 'waveform', 'waveforms']]

        return names

    def restore_location(self, location):
        """ restore a full version of the location using alias_map, like
        'mtd/sec/293847/' -> 'metadata/section/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        almap = dict(self.app_aliases.items() + self.cls_aliases.items())
        for name, alias in almap.items():
            if l.find(alias) > -1 and l[l.find(alias)-1] == '/' and \
                l[l.find(alias) + len(alias)] == '/':
                l = l.replace(alias, name)

        l = l[1:] # remove preceeding slash
        if not l.endswith('/'):
            l += '/'

        return l

    def strip_location(self, location):
        """ make a shorter version of the location using alias_map, like
        'metadata/section/293847/' -> 'mtd/sec/293847/' """
        l = str( location )
        if not l.startswith('/'):
            l = '/' + l

        almap = dict(self.app_aliases.items() + self.cls_aliases.items())
        for name, alias in almap.items():
            if l.find(name) > -1 and l[l.find(name)-1] == '/' and\
                l[l.find(name) + len(name)] == '/':
                l = l.replace(name, alias)

        return l

    def parse_location(self, location):
        """ extracts app name and object type from the current location, e.g.
        'metadata' and 'section' from 'metadata/section/293847/' """
        def is_valid_id( lid ):
            try:
                int( lid )
                return True
            except ValueError:
                return False

        l = self.restore_location( location )

        if l.startswith('/'):
            l = l[ 1 : ]
        if not l.endswith('/'):
            l += '/'

        res = []
        while l:
            item = l[ : l.find('/') ]
            res.append( item ) # e.g. 'metadata' or 'section'
            l = l[ len(item) + 1 : ]

        try:
            app, model_name, lid = res
        except ValueError:
            raise ReferenceError('Cannot parse object location %s. The format \
                should be like "metadata/section/293847/"' % str(res))

        if not app in self.app_prefix_dict.values():
            raise TypeError('This app is not supported: %s' % app)
        if not model_name in self.model_names:
            raise TypeError('This type of object is not supported: %s' % model_name)
        if not is_valid_id( lid ):
            raise TypeError('ID of an object must be of "int" type: %s' % lid)

        return app, model_name, int(lid)

    def is_modified(self, json_obj):
        """ checks if object was modified locally by validating that object
        references are permalinks """

        # 1. check permalink
        if not is_permalink( json_obj['permalink'] ):
            return True

        app_name, model_name = parse_model( json_obj )

        # 2. check data fields
        for attr in self.get_array_attr_names( model_name ):
            data = json_obj['fields'][ attr ]['data']
            if data: # should not be null
                if not is_permalink( data ):
                    return True

        # 3. check parent fields
        for attr in self.app_definitions[model_name]['parents']:
            parent = json_obj['fields'][ attr ]
            if parent: # should not be null
                if not is_permalink( parent ):
                    return True

        return False
        


class Session( Browser ):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, profile_data, model_data):

        # 1. load meta info: store all settings in Meta class as _meta attribute
        meta = Meta()
        meta.username = profile_data['username']
        meta.password = profile_data['password']
        meta.temp_dir = os.path.abspath( profile_data['tempDir'] )
        meta.max_line_out = profile_data['max_line_out']
        meta.verbose = bool( profile_data['verbose'] )
        meta.host = build_hostname( profile_data )
        meta.port = profile_data['port']
        meta.app_definitions, meta.model_names, meta.app_prefix_dict = \
            load_app_definitions(model_data)
        # a) app_definitions is a dict parsed from requirements.json
        # b) model names is a list like ['segment', 'event', ...]
        # c) app_prefix_dict is like {'section': 'metadata', 'block': 'electrophysiology', ...}

        meta.app_aliases, meta.cls_aliases = build_alias_dicts( profile_data['alias_map'] )
        meta.cache_dir = os.path.abspath( profile_data['cacheDir'] )
        meta.cache_path = os.path.join( profile_data['cacheDir'], profile_data['cache_file_name'] )
        self._meta = meta

        # 2. init Local/Remote backends
        self._local = Local( meta )
        self._remote = Remote( meta )
        self._remote.open() # authenticate at the remote

        # 3. load odML terminologies
        # TODO make odML to load terms into our cache folder, not default /tmp
        terms = terminology.terminologies.load(profile_data['odml_repository'])
        self.terminologies = terms.sections

        warnings.simplefilter('ignore', tb.NaturalNameWarning)
        print "Session initialized."


    def select(self, model_name, params={}, data_load=False, remote=False, mode='obj'):
        """ 
        requests objects of a given type from remote in bulk mode. 

        Args:
        model_name: type of the object (like 'block', 'segment' or 'section')

        params:     dict that can contain several categories of key-value pairs
        data_load:  fetch the data or not (applied if mode == 'obj')
        remote:     whether remote backend is used to get/save data
        mode:       return mode, python object or JSON
        """
        if model_name in self._meta.cls_aliases.values(): # FIXME put into model_safe decorator
            model_name = [k for k, v in self._meta.cls_aliases.items() if v==model_name][0]

        if not model_name in self._meta.model_names:
            raise TypeError('Objects of that type are not supported.')

        self._local.open()
        if remote and not self._remote.is_active:
            self._remote.open()

        if remote: # fetch from remote + save in cache if possible
            json_objs = self._remote.get_list( model_name, params )

            for json_obj in json_objs:
                local_obj = self._local.get( json_obj['permalink'] )

                if local_obj == None: # new object, save
                    self._local.save( json_obj )

                elif self._meta.is_modified( local_obj ):
                    print "object %s has local changes and was not modified." % \
                        json_obj['location']

                else: # exists but not modified, update
                    self._local.save( json_obj )

        else: # fetch from local
            json_objs = self._local.get_list( model_name, params )

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
                    for array_attr in self._meta.get_array_attr_names( model_name ):
                        arr_loc = json_obj['fields'][ array_attr ]['data']
                        data = self._local.get_data( arr_loc )

                        # no local data, fetch from remote
                        if remote and data == None:
                                data = self._remote.get_data( arr_loc )
                                if not data == None:
                                    self._local.save_data( data, arr_loc )

                        if not data == None:
                            data_refs[ array_attr ] = data

                obj = Serializer.deserialize( json_obj, self._meta, data_refs )
                objects.append( obj )

        self._local.close()
        return objects


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------


    def pull(self, location, params={}, cascade=True, data_load=True, _top=True):
        """ pulls object from the specified location on the server. 
        caching:    yes
        cascade:    yes
        data_load:  yes

        _top:       reserved parameter used to detect the top function call in
                    cascade (recursive) mode. This is needed to save cache and
                    make correct printing after new objects are fetched.
        """
        if is_permalink( location ):
            location = extract_location( location )
        location = self._meta.restore_location( location )
        app, cls, lid = self._meta.parse_location( location )

        headers = {} # request headers
        params['q'] = 'full' # always operate in full mode, see API specs

        url = '%s%s/%s/%s/' % (self._meta.host, app, cls, str(lid))

        # find object in cache
        if location in self._cache.objs_map.keys():
            headers['If-none-match'] = self._cache.objs_map[ location ]

        # request object from the server (with ETag)
        resp = requests.get(url, params=params, headers=headers, cookies=self._meta.cookie_jar)

        if resp.status_code == 304: # get object from cache
            guid = self._cache.objs_map[ location ]
            obj = self._cache.objs[ guid ]

            print_status('%s loaded from cache.' % location)

        else: # request from server

            # parse response json
            raw_json = get_json_from_response( resp )
            if not resp.status_code == 200:
                message = '%s (%s)' % (raw_json['message'], raw_json['details'])
                raise errors.error_codes[resp.status_code]( message )

            if not raw_json['selected']:
                raise ReferenceError('Object does not exist.')

            json_obj = raw_json['selected'][0] # should be single object 

            # download attached data if requested
            data_refs = self._parse_data_from_json(cls, json_obj, data_load=data_load)

            # download attached metadata if exists
            metadata = self._fetch_metadata_by_json(cls, json_obj)

            # parse json (+data) into python object
            obj = Serializer.deserialize(json_obj, self, data_refs, metadata)

            # save it to cache
            self._cache.add_object( obj )

            print_status("%s fetched from server." % location)

        children = self._meta.app_definitions[cls]['children'] # child object types
        if cascade and self._meta.app_definitions[cls]['children']:
            for child in children: # 'child' is like 'segment', 'event' etc.

                field_name = child + '_set'
                if obj._gnode['fields'].has_key( field_name ) and \
                    obj._gnode['fields'][ field_name ]:
                    rel_objs = []

                    for rel_link in obj._gnode['fields'][ field_name ]:
                        # fetching *child*-type objects
                        ch = self.pull( rel_link, params=params, data_load=data_load, _top=False )
                        rel_objs.append( ch )

                    if rel_objs: # parse children into parent attrs
                        # a way to assign kids depends on object type
                        self._assign_child( child, obj, rel_objs )

        if _top: # end of the function call if run in recursive mode
            print_status( 'Object(s) loaded.\n' )
            self._cache.save_cache() # updates on-disk cache with new objects

        return obj


    def gselect(self, model_name, params={}, cascade=False, data_load=False, _top=True):
        """ requests objects of a given type from server in bulk mode. 
        caching:    no
        cascade:    yes
        data_load:  yes

        Args:
        model_name: type of the object (like 'block', 'segment' or 'section'.)

        params: dict that can contain several categories of key-value pairs:

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

        _top:       reserved parameter used to detect the top function call in
                    cascade (recursive) mode. This is needed to save cache and
                    make correct printing after new objects are fetched.
        Examples:
        get('analogsignal', params={'id__in': [38551], 'downsample': 100})
        get('analogsignal', params={'segment__id': 93882, 'start_time': 500.0})
        get('section', params={'odml_type': 'experiment', 'date_created': '2013-02-22'})

        """
        # resolve alias - short model name like 'rcg' -> 'recordingchannelgroup'
        if model_name in self._meta.cls_aliases.values():
            model_name = [k for k, v in self._meta.cls_aliases.items() if v==model_name][0]

        if not model_name in self._meta.model_names:
            raise TypeError('Objects of that type are not supported.')

        objects = [] # resulting objects set
        params['q'] = 'full' # always operate in full mode, see API specs
        # convert all values to string for a correct GET behavior (encoding??)
        get_params = dict( [(k, str(v)) for k, v in params.items()] )

        url = '%s%s/%s/' % (self._meta.host, self._meta.app_prefix_dict[model_name], str(model_name))

        # do fetch list of objects from the server
        resp = requests.get(url, params=get_params, cookies=self._meta.cookie_jar)
        raw_json = get_json_from_response( resp )

        if not resp.status_code == 200:
            message = '%s (%s)' % (raw_json['message'], raw_json['details'])
            raise errors.error_codes[resp.status_code]( message )

        if not raw_json['selected']: # if no objects exist return empty result
            return []

        for json_obj in raw_json['selected']:

            # download attached data if requested
            data_refs = self._parse_data_from_json(model_name, json_obj, data_load=data_load)

            # parse json (+data) into python object
            obj = Serializer.deserialize(json_obj, self, data_refs)

            objects.append(obj)

        print_status('%s(s) fetched.' % model_name)

        # fetch children 'in bulk'
        children = self._meta.app_definitions[model_name]['children'] # child object types
        if cascade and self._meta.app_definitions[model_name]['children']:
            parent_ids = [obj._gnode['id'] for obj in objects]

            for child in children: # 'child' is like 'segment', 'event' etc.

                # filter to fetch objects of type child for ALL parents
                # FIXME dirty fix!! stupid data model inconsistency
                parent_name = model_name
                if (model_name == 'section' and child == 'section') or \
                    (model_name == 'property' and child == 'value'):
                    parent_name = 'parent_' + parent_name

                filt = { parent_name + '__id__in': parent_ids }
                if params.has_key('at_time'): # proxy time if requested
                    filt = dict(filt, **{"at_time": params['at_time']})

                # fetching *child*-type objects
                rel_objs = self.select( child, params=filt, data_load=data_load, _top=False )

                if rel_objs:
                    for obj in objects: # parse children into parent attrs
                        related = [x for x in rel_objs if \
                            getattr(x, '_gnode')['fields'][parent_name + '_id'] == obj._gnode['id']]
                        # a way to assign kids depends on object type
                        self._assign_child( child, obj, related )

                # FIXME make a special processing for the Block object to avoid
                # downloading some objects twice

        if _top: # end of the function call if run in recursive mode
            #print_status( 'Object(s) loaded.\n' )
            self._cache.save_cache() # updates on-disk cache with new objects

        return objects


    def sync(self, obj_to_sync, cascade=False):
        """ bla bla """

        processed = [] # collector of permalinks of processed objects
        to_clean = [] # collector of ids of objects to clean parent
        stack = [ obj_to_sync ] # a stack of objects to sync

        while len( stack ) > 0:

            obj = stack[0] # take first object from stack
            success = False # flag to indicate success of the syncing
            cls = None # type of the object like 'segment' or 'section'

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

            # 2. detect create/update and set request params
            cls = get_type_by_obj( obj )
            app = self._meta.app_prefix_dict[cls]
            
            if hasattr(obj, '_gnode'): # existing object, sync if possible
                # update object on the server (with ETag)
                headers = {'If-Match': obj._gnode['fields']['guid']}
                params = {'m2m_append': 0}
                lid = obj._gnode['id'] # get the full permalink from _gnode?
                url = '%s%s/%s/%s/' % (self._meta.host, app, cls, str(lid))
                status = 200

            else: # new object, create
                headers, params = {}, {} # not needed for new objects
                url = '%s%s/%s/' % (self._meta.host, app, cls)
                status = 201

            # 3. pre-push new/changed array data to the server (+put in cache)
            # data_refs is a dict like {'signal': 'http://host:/neo/signal/148348', ...}
            try:
                data_refs = self._push_related_data( obj )
            except (errors.FileUploadError, errors.UnitsError), e:
                # skip this object completely
                stack.remove( obj )
                print_status('%s skipped: %s\n' % (cut_to_render(obj.__repr__(), 15), str(e)))
                continue

            # 4. pre-sync related metadata if exists (+put in cache)
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

            # 5. sync main object
            try:
                json_obj = Serializer.serialize(obj, self, data_refs)

                # sync main object on server (create / update)
                resp = requests.post(url, data=json.dumps(json_obj), \
                    headers=headers, params=params, cookies=self._meta.cookie_jar)

                if resp.status_code in [status, 304]:

                    if resp.status_code == status:
                        raw_json = get_json_from_response( resp )

                        # update local in-memory object with newly acquired params
                        setattr(obj, '_gnode', raw_json['selected'][0])

                    # update parent children list
                    Serializer.update_parent_children(obj, self)

                    success = True
                    processed.append( obj._gnode['permalink'] )
                    print_status('Object at %s synced.' % obj._gnode['location'])

                else:
                    if resp.status_code == 412:
                        message = 'it was changed. please pull current version first.'

                    else:
                        try:
                            raw_json = get_json_from_response( resp )
                            message = '%s (%s)' % (raw_json['message'], \
                                raw_json['details'])

                        except ValueError:
                            message = 'unknown reason. contact developers!'

                    raise errors.SyncFailed( message )

            except (errors.UnitsError, errors.ValidationError, errors.SyncFailed), e:
                print_status('%s skipped: %s\n' % (cut_to_render(obj.__repr__(), 15), str(e)))

            stack.remove( obj ) # not to forget to remove processed object

            # if cascade put children objects to the stack to sync
            children = self._meta.app_definitions[cls]['children'] # child object types
            if cascade and children and hasattr(obj, '_gnode'):

                for child in children: # 'child' is like 'segment', 'event' etc.

                    # cached children references
                    child_link_set = list( obj._gnode['fields'][ child + '_set' ] )

                    for rel in getattr(obj, get_children_field_name( child )):

                        # detect children of that type that were removed (using cache)
                        if hasattr(rel, '_gnode') and rel._gnode['permalink'] in child_link_set:
                            child_link_set.remove( rel._gnode['permalink'] )

                        # prepare to sync child object (skip already scheduled or processed)
                        if not (hasattr(rel, '_gnode') and rel._gnode['permalink'] in processed):
                            # and not obj in stack:
                            # stupid NEO!! this raises error, so the workaround
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

        # post-processing
        # 1. clean objects that were removed from everywhere in this scope
        pure_links = [x[0] for x in to_clean]
        removed = list( set(pure_links) - set(processed) )
        to_clean = [x for x in to_clean if x[0] in removed]

        if to_clean:
            print_status('Cleaning removed objects..')
            for link, par_name in to_clean: # TODO make in bulk? could be faster

                json_data = '{"%s": null}' % par_name
                requests.post(link, data=json_data, cookies=self._meta.cookie_jar)

        # 2. final output
        print_status('sync done, %d objects processed.\n' % len( processed ))


    def annotate(self, objects, values):
        """ annotates given objects with given values. sends requests to the 
        backend. objects, values - are lists """

        # 1. split given objects by model (class)
        for_annotation = {}
        for obj in objects:
            model_name = get_type_by_obj( obj )
            if not hasattr(obj, '_gnode'):
                raise ValidationError('All objects need to be synced before annotation.')

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
            url = '%s%s/%s/' % (self._meta.host, self._meta.app_prefix_dict[model_name], str(model_name))
            params = {'id__in': [x._gnode['id'] for x in objects], 'bulk_update': 1}

            resp = requests.post(url, data=json.dumps(data), params=params, \
                cookies=self._meta.cookie_jar)

            # parse response json
            if not resp.status_code in [200, 304]:
                raw_json = get_json_from_response( resp )
                message = '%s (%s)' % (raw_json['message'], raw_json['details'])
                raise errors.error_codes[resp.status_code]( message )

            if resp.status_code == 200:

                for obj in objects:

                    # 1. update metadata attr in obj._gnode (based on values, not 
                    # on the response values so not to face the max_results problem)
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


    def delete(self, obj_type, obj_id=None, *kwargs):
        """ delete (archive) one or several objects on the server """
        raise NotImplementedError


    def save_session(self, filename):
        """ Save the data necessary to restart current session (cookies, ...)"""
        raise NotImplementedError


    def load_session(self, filename):
        """Load a previously saved session """
        raise NotImplementedError


    def shutdown(self):
        """ Logs out and saves cache. """
        # M.Pereira:
        #TODO: which other actions should be accomplished?
        # Notes: does not seem to be necessary to GC, close sockets, etc...
        # Requests keeps connections alive for performance increase but doesn't
        # seem to have a method to close a connection other than disabling this
        # feature all together
        #s = requests.session()
        #s.config['keep_alive'] = False
        requests.get(self._meta.host + 'account/logout/', cookies=self._meta.cookie_jar)

        self._cache.save_cache()

        del(self._meta.cookie_jar)

    #---------------------------------------------------------------------------
    # helper functions that DO send HTTP requests
    #---------------------------------------------------------------------------

    def _push_related_data(self, obj):
        """ saves array data to disk in HDF5 and uploads new datafiles to the 
        server according to the arrays of the given obj. Saves datafile objects 
        to cache """
        data_refs = {} # collects all updated references to the related data
        model_name = get_type_by_obj( obj )

        data_attrs = self._meta.get_array_attr_names( obj ) # all array-type attrs

        if not hasattr(obj, '_gnode'): # True if object never synced
            # sync all arrays
            attrs_to_sync = data_attrs

        else:
            # sync only changed arrays
            attrs_to_sync = self.detect_changed_data_fields( obj )

        for attr in data_attrs: # attr is like 'times', 'signal' etc.

            if attr in attrs_to_sync:
                # 1. get current array and units
                fname = self._meta.app_definitions[model_name]['data_fields'][attr][2]
                if fname == 'self':
                    arr = obj # some NEO objects like signal inherit array
                else:
                    arr = getattr(obj, fname)

                units = Serializer.parse_units(arr)

                # 2. save it to the cache_dir as HDF5 file
                cache_dir = self._cache.cache_dir
                temp_name = hashlib.sha1( arr ).hexdigest()
                with tb.openFile( cache_dir + temp_name + '.h5', "w" ) as f:
                    f.createArray('/', 'gnode_array', arr)

                # 3. upload to the server
                print_status('uploading datafile for %s attr of %s...' % \
                    (attr, cut_to_render(obj.__repr__(), 15)))

                url = self._meta.host + 'datafiles/'
                files = {'raw_file': open(cache_dir + temp_name + '.h5', 'rb')}
                resp = requests.post(url, files=files, cookies=self._meta.cookie_jar)
                raw_json = get_json_from_response( resp )

                if resp.status_code == 201:

                    # save filepath to the cache
                    link = raw_json['selected'][0]['permalink']
                    fid = str(get_id_from_permalink( link ))
                    self._cache.data_map[ fid ] = cache_dir + temp_name + '.h5'

                    print 'done.'
                    data_refs[ attr ] = {'data': link, 'units': units}

                else:
                    raise errors.FileUploadError('error. file upload failed: %s\nmaybe sync again?' % resp.content)
            else:
                data_refs[ attr ] = None

        return data_refs


    def _fetch_metadata_by_json(self, model_name, json_obj):
        """ parses incoming json object representation and fetches related 
        object metadata from the server. Returns None or the Metadata object """
        if not json_obj['fields'].has_key('metadata') or not json_obj['fields']['metadata']:
            return None # no metadata field or empty metadata

        url = json_obj['permalink']

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

        """ 
        # an alternative way to fetch metadata - just use pull for all related 
        # values and properties (performance down!!). Not needed here because 
        # this func is called only when core object is not found in cache, means
        # metadata should be requested from the server anyway and it can be done
        # faster with GET /neo/<obj_type>/198272/metadata/
        mobj = Metadata()
        for vlink in json_obj['fields']['metadata']:
            val = self.pull( vlink, cascade=False, data_load=False )
            prp = self.pull( val._gnode['parent_property'], cascade=False, \
                data_load=False )
            prp.append( val )

            setattr( mobj, prp.name, prp )
        """ 

        return mobj # Metadata object with list of properties (tags)

    def _parse_data_from_json(self, model_name, json_obj, data_load=True):
        """ parses incoming json object representation and fetches related 
        object data, either from cache or from the server. """

        # collects downloaded datafile on-disk references 
        data_refs = {} # a dict like {'signal': '/cache/187283.h5', ...}

        data_links = Serializer.parse_data_permalinks(json_obj, self)

        for attr, data_link in data_links.items():

            fid = str(get_id_from_permalink( data_link ))

            if data_load:
                if fid in self._cache.data_map.keys(): # get data from cache
                    data_refs[ attr ] = (fid, self._cache.data_map[ fid ])

                else: # download related datafile

                    print_status('loading datafile %s from server...' % fid)

                    r = requests.get(data_link, cookies=self._meta.cookie_jar)

                    temp_name = str(get_id_from_permalink( data_link )) + '.h5'
                    with open( self._cache.cache_dir + temp_name, "w" ) as f:
                        f.write( r.content )

                    if r.status_code == 200:
                        # save filepath to the cache
                        self._cache.data_map[ fid ] = self._cache.cache_dir + temp_name

                        print 'done.'

                        # collect path to the downloaded datafile
                        data_refs[ attr ] = (fid, self._cache.cache_dir + temp_name)

                    else:
                        print 'error. file was not fetched. maybe pull again?'
                        data_refs[ attr ] = None
            else:
                data_refs[ attr ] = None

        return data_refs

    #---------------------------------------------------------------------------
    # helper functions that DO NOT send HTTP requests
    #---------------------------------------------------------------------------

    def _detect_changed_data_fields(self, obj):
        """ compares all current in-memory data fields (arrays) for a given 
        object with cached (on-disk) versions of these data arrays and returns
        names of the fields where arrays do NOT match """

        if not hasattr(obj, '_gnode'):
            raise TypeError('This object was never synced, cannot detect changes')

        attrs_to_sync = []
        model_name = get_type_by_obj( obj )
        data_fields = self._meta.app_definitions[model_name]['data_fields']
        data_attrs = self._meta.get_array_attr_names( obj )

        for attr in data_attrs:

            fname = attr + '_id'
            if obj._gnode['fields'].has_key( fname ) and obj._gnode['fields'][ fname ]:
                # id of the cached file
                fid = get_id_from_permalink(obj._gnode['fields'][ fname ])

                if fid in self._cache.data_map.keys():

                    # get actual array
                    getter = data_fields[attr][2]
                    if getter == 'self':
                        curr_arr = obj # some NEO objects like signal inherit array
                    else:
                        curr_arr = getattr(obj, getter)

                    if len(curr_arr) < 2:
                        # we treat array with < 2 values as when object was 
                        # fetched without data for performance reasons. in this 
                        # case we ignore this data attribute
                        continue

                    # get array from cache
                    filename = self._cache.data_map[ fid ]
                    with tb.openFile(filename, 'r') as f:
                        carray = f.listNodes( "/" )[0]
                        init_arr = np.array( carray[:] )

                    # compare cached (original) and current data
                    if not np.array_equal(init_arr, curr_arr):
                        attrs_to_sync.append( attr )

                else: # nothing to compare with!
                    # this could happen when an object was fetched without data.
                    # ignore, treat as data was not changed
                    pass

            else: # no real reference! treat as array was changed
                attrs_to_sync.append( attr )

        return attrs_to_sync

    def _assign_child(self, child, obj, related):
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


    def _bulk_update(self, obj_type, *kwargs):
        """ update several homogenious objects on the server """
        raise NotImplementedError




