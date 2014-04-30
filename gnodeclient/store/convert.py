# Python G-Node Client
#
# Copyright (C) 2013  A. Stoewer
#                     A. Sobolev
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License (see LICENSE.txt).

from __future__ import print_function, absolute_import, division

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import gnodeclient.util.helper as helper
from gnodeclient.model.models import Model

try:
    import simplejson as json
except ImportError:
    import json


def collections_to_model(collection, as_list=False):
    """
    Converts objects of nested collections (list, dict) as produced by the json module
    into a model object.

    :param collection: The object or list of objects to convert.
    :type collection: dict|list
    :param as_list: If True the result is always a list.
    :type as_list: bool

    :returns: The converted object or a list of converted objects.
    :rtype: Model|list

    :raises: ValueError
    """
    def clean(ref):
        if ref.lower().startswith('http'):
            return urlparse.urlparse(ref).path
        return ref

    models = []

    # adjust json object
    if isinstance(collection, list):
        objects = collection
    elif 'selected' in collection:
        objects = collection['selected']
    else:
        objects = [collection]

    # convert
    for obj in objects:
        if 'resource_uri' not in obj:
            raise ValueError("Object identifier is missing")

        location = urlparse.urlparse(obj['resource_uri']).path
        api, version, category, model_name, obj_id = location.strip('/').split('/')
        model_obj = Model.create(model_name)

        for field_name in model_obj:
            field = model_obj.get_field(field_name)

            if field.is_child:
                obj_field_name = field.name_mapping or field.type_info + '_set'
            else:
                obj_field_name = field.name_mapping or field_name

            if not obj_field_name in obj:
                continue

            if field.type_info in ['data', 'datafile']:
                value = obj[obj_field_name]
                field_val = {
                    "units": obj.get(obj_field_name + '__unit', None),
                    "data": float(value) if field.type_info == 'data' else value
                }
            elif field_name == 'model':
                field_val = model_name
            elif field.is_child and obj[obj_field_name] is not None:
                field_val = [clean(ref) for ref in obj[obj_field_name]]
            else:
                field_val = obj[obj_field_name]

            if field_val is not None:
                model_obj[field_name] = field_val

        models.append(model_obj)

    if not as_list:
        if len(models) > 0:
            models = models[0]
        else:
            models = None

    return models


def model_to_collections(model):
    """
    Converts a single model into a dict representation of this model.

    :param model: The model to convert.
    :type model: Model

    :returns: A dictionary that represents this model.
    :rtype: dict
    """
    result = {}
    for field_name in model:
        value = model[field_name]
        field = model.get_field(field_name)

        if isinstance(value, Model):
            value = model_to_collections(value)
        elif model.model in (Model.EVENTARRAY, Model.EPOCHARRAY) and field_name == "labels":
            if value is not None:
                value = value["data"]
        elif field.type_info in ["data", "datafile"]:
            result[field_name + '__unit'] = value["units"]
            value = value["data"]

        if field.is_child:
            field_name = field.name_mapping or field.type_info + "_set"
        else:
            field_name = field.name_mapping or field_name

        result[field_name] = value
    return result


def model_to_json_response(model, exclude=("location", "model", "guid", "resource_uri", "id")):
    """
    Converts a single model into a json encodes string that can be used as a
    response body for the G-Node REST API.

    :param model: The model to convert
    :type model: Model
    :param exclude: Excluded field names
    :type exclude: tuple

    :returns: A json encoded string representing the model.
    :rtype: str
    """
    result = {}
    for field_name in model:
        if exclude is not None and field_name not in exclude:
            field = model.get_field(field_name)
            value = model[field_name]

            if field.type_info == "data":
                if value is None:
                    result[field_name] = None
                else:
                    result[field_name] = value["data"]
                    result[field_name + '__unit'] = value["units"]

            elif field.type_info == "datafile":
                if value is not None:  # TODO clean this up
                    #if model.model in (Model.EPOCHARRAY, Model.EPOCHARRAY) and field_name == "labels":
                    #    new_value = helper.id_from_location(value["data"])
                    #else:
                    #    new_value = {"units": value["units"], "data": helper.id_from_location(value["data"])}
                    result[field_name + '__unit'] = value["units"]

            elif field.is_child:
                if model.model == Model.RECORDINGCHANNEL and field_name == "recordingchannelgroups":
                    field_name = field.name_mapping or field.type_info + "_set"
                    new_value = []
                    if value is not None:
                        for i in value:
                            new_value.append(helper.id_from_location(i))
                    result[field_name] = new_value

            elif field.is_parent:
                field_name = field.name_mapping or field_name
                if value is None:
                    result[field_name] = None
                else:
                    result[field_name] = helper.id_from_location(value)

            else:
                field_name = field.name_mapping or field_name
                result[field_name] = value

    json_response = json.dumps(result)

    return json_response


def json_to_collections(string, as_list=False):
    """
    Converts a json string from the REST API into a collection (list, dict) that
    represents the content of the json string.

    :param string: The json encoded string from the REST API.
    :type string: str
    :param as_list: If True the result is always a list, otherwise it depends on the content of string.
    :type as_list: bool

    :returns: A list or dict that represents the parsed string.
    :rtype: dict|list
    """
    collection = json.loads(string, encoding='UTF-8')

    if 'selected' in collection:
        collection = collection['selected']

    if as_list:
        if not isinstance(collection, list):
            if collection is None:
                collection = []
            else:
                collection = [collection]
    else:
        if isinstance(collection, list):
            if len(collection) > 0:
                collection = collection[0]
            else:
                collection = None

    return collection


def permissions_to_json(permissions):
    """
    :param permissions: permission settings to convert, like
        [{
           "user": "/api/v1/user/user/neo/",
           "access_level": 1  # 1-read-only
        },
        {
           "user": "/api/v1/user/user/bob/",
           "access_level": 2  # 2-read-write
        }]
    :type permissions: list

    :return: string with permissions ready to be sent to the G-Node service
    :rtype: string
    """
    return json.dumps(permissions)


def json_to_permissions(string):
    """
    :param string: The json encoded string from the REST API.
    :type string: str

    :return: a list representing permissions
        [{
           "user": "/api/v1/user/user/neo/",
           "access_level": 1  # 1-read-only
        },
        {
           "user": "/api/v1/user/user/bob/",
           "access_level": 2  # 2-read-write
        }]
    :rtype: list
    """
    return json.loads(string, encoding='UTF-8')