from gnodeclient.model.rest_model import Models, QuantityModel

try:
    import simplejson as json
except ImportError:
    import json


def collections_to_model(collection):
    """
    Exceptions: ValueError
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
                    field_val = QuantityModel(units=field_val['units'], data=float(field_val['data']))
                elif field_name == 'model':
                    field_val = model

                model_obj[field_name] = field_val

        models.append(model_obj)

    return models if len(models) > 1 else models[0]


def model_to_collections(model):
    # TODO implement
    return model


def json_to_collections(string):
    collection = json.loads(string, encoding='UTF-8')

    if 'selected' in collection:
        collection = collection['selected']

    return collection if len(collection) > 1 else collection[0]
