try:
    import simplejson as json
except ImportError:
    import json


def json_to_model(json):
    # TODO implement
    return json


def model_to_json(model):
    # TODO implement
    return model


def str_to_json(string):
    # TODO watch for encoding
    return json.loads(string)
