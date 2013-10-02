from gnodeclient.model.rest_model import Models, Model, RestResult, QuantityModel

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
    :rtype: RestResult|list

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

        category, model, id = obj['location'].strip('/').split('/')
        model_obj = Models.create(model)

        for field_name in model_obj:
            field = model_obj.get_field(field_name)

            if field.is_child:
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
                    field_val = QuantityModel(units=field_val['units'], data=field_val['data'])
                elif field.type_info == 'data':
                    data = None if field_val['data'] is None else float(field_val['data'])
                    field_val = QuantityModel(units=field_val['units'], data=data)
                elif field_name == 'model':
                    field_val = model

                model_obj[field_name] = field_val

        models.append(model_obj)

    if not as_list:
        if len(models) > 0:
            models = models[0]
        else:
            models = None

    return models


def model_to_collections(model, exclude=('model', 'location')):
    """
    Converts a single model into a dict representation of this model.

    :param model: The model to convert.
    :type model: Model

    :returns: A dictionary that represents this model.
    :rtype: dict
    """
    # TODO the implementation of model_to_collections() may need to be improved
    result = {}
    for name in model:
        if exclude is None or name not in exclude:
            value = model[name]
            if isinstance(value, Model):
                value = model_to_collections(value)
            result[name] = value
    return result


def model_to_json_response(model):
    raise NotImplementedError()


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
