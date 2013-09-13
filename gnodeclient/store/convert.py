from gnodeclient.model.rest_model import Models, ValueModel

try:
    import simplejson as json
except ImportError:
    import json


def json_to_model(json):
    """
    Exceptions: ValueError
    """
    models = []

    # adjust json object
    if isinstance(json, list):
        objects = json
    elif 'selected' in json:
        objects = json['selected']
    else:
        objects = [json]

    # convert
    for obj in objects:
        if 'id' not in obj or 'location' not in obj or 'model' not in obj:
            raise ValueError("Unable to convert json into a model!")

        category, model, id = obj['location'].strip('/').split('/')
        model_obj = Models.create(model)

        for field_name in model_obj:
            if field_name in obj:
                field_val = obj[field_name]
            elif 'fields' in obj and field_name in obj['fields']:
                field_val = obj['fields'][field_name]
            else:
                field_val = None

            if field_val is not None:
                field = model_obj.get_field(field_name)
                if field.type_info == 'datafile':
                    field_val = ValueModel(units=field_val['units'], data=field_val['data'])
                elif field.type_info == 'data':
                    field_val = ValueModel(units=field_val['units'], data=float(field_val['data']))
                elif field_name == 'model':
                    field_val = model

                print field_name
                model_obj[field_name] = field_val

        models.append(model_obj)

    # TODO implement
    return models if len(models) > 1 else models[0]


def model_to_json(model):
    # TODO implement
    return model


def str_to_json(string):
    # TODO watch for encoding
    return json.loads(string)

