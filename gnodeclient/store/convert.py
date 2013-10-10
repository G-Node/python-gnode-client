from __future__ import print_function, absolute_import, division

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
        if 'id' not in obj or 'location' not in obj or 'model' not in obj:
            raise ValueError("Unable to convert json into a model!")

        category, model_name, obj_id = obj['location'].strip('/').split('/')
        model_obj = Model.create(model_name)

        for field_name in model_obj:
            field = model_obj.get_field(field_name)

            # FIXME ugly workaround that is necessary because of inconsistent naming schema
            if field.is_child:
                if model_obj.model == Model.RECORDINGCHANNEL and field_name == "recordingchannelgroups":
                    obj_field_name = "recordingchannelgroup"
                else:
                    obj_field_name = field.type_info + '_set'
            else:
                obj_field_name = field_name

            if obj_field_name in obj:
                field_val = obj[obj_field_name]
            elif 'fields' in obj and obj_field_name in obj['fields']:
                field_val = obj['fields'][obj_field_name]
            else:
                field_val = None

            if field_val is not None:
                if field.type_info == 'datafile':
                    # TODO handle datafiles here
                    pass
                elif field.type_info == 'data':
                    if field_val['data'] is not None:
                        field_val['data'] = float(field_val['data'])
                elif field_name == 'model':
                    field_val = model_name

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
    for name in model:
        value = model[name]
        field = model.get_field(name)

        if isinstance(value, Model):
            value = model_to_collections(value)

        # FIXME ugly workaround that is necessary because of inconsistent naming schema
        if field.is_child:
            if (hasattr(model, "model") and model["model"] == Model.RECORDINGCHANNEL and
                    name == "recordingchannelgroups"):
                name = "recordingchannelgroup"
            else:
                name = field.type_info + "_set"

        result[name] = value
    return result


def model_to_json_response(model, exclude=("location", "model", "guid", "permalink", "id")):
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
    for name in model:
        if exclude is not None and name not in exclude:
            field = model.get_field(name)
            value = model[name]
            if field.type_info == "data":
                result[name] = {"units": value["units"], "data": value["data"]}
            elif field.type_info == "datafile":
                # TODO add support for data files
                pass
            elif field.is_child:
                # FIXME ugly workaround that is necessary because of inconsistent naming schema
                new_name = False
                if model.model == Model.RECORDINGCHANNELGROUP and name == "recordingchannels":
                    new_name = field.type_info + "_set"
                elif model.model == Model.RECORDINGCHANNEL and name == "recordingchannelgroups":
                    new_name = "recordingchannelgroup"
                if new_name:
                    new_value = []
                    for i in value:
                        new_value.append(i.split("/")[-1])
                    result[new_name] = value
            elif field.is_parent:
                if value is not None:
                    result[name] = value.split("/")[-1]
                else:
                    result[name] = value
            else:
                result[name] = value
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
