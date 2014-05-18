import tempfile as tmp
import uuid
import os
import h5py

from gnodeclient.store import convert


class Dumper(object):
    """ dumps a given Model instance (recursively) to the temp HDF5 file """

    def __init__(self, driver):
        """
        Constructor

        :param driver: A Native driver instance
        :type driver: NativeDriver
        """
        self.__driver = driver

    def dump(self, entity):

        def get_children_fields(native, local):
            child_field_names = filter(
                lambda x: hasattr(native, x), local.child_fields
            )
            child_fields = [
                getattr(native, x, []) for x in child_field_names
            ]
            return filter(lambda x: (x is not None) and
                not (hasattr(x, '_is_loaded') and not getattr(x, '_is_loaded')),
                child_fields
            )

        name = uuid.uuid1().hex + ".h5"
        path = os.path.join(tmp.gettempdir(), name)  # FIXME get proper temppath

        f = h5py.File(path)

        todo = [entity]  # a stack of objects to submit
        processed = []  # collector of locations of processed objects
        to_clean = []  # collector of objects to clean their fake IDs

        while len(todo) > 0:
            current_native = todo[0]
            model = self.__driver.get_model_by_obj(current_native)

            location = getattr(current_native, 'location', None)
            if location is not None:
                if location in processed:
                    continue  # workaround to avoid duplicate processing for Neo
            else:
                location = os.path.join(
                    model.get_location(model.model),
                    "TEMP" + str(id(current_native))
                ) + "/"  # fake location is needed to keep references
                setattr(current_native, 'location', location)
                to_clean.append(current_native)

            current_local = self.__driver.to_model(current_native, in_memory=True)

            current_group = f.create_group(name=location.replace("/", "-"))
            current_group.create_dataset(
                name="json", data=convert.model_to_json_response(current_local)
            )

            for field_name in current_local.datafile_fields:
                field_val = current_local[field_name]
                if field_val is not None and field_val["data"] is not None:
                    current_group.create_dataset(
                        name=field_name, data=field_val["data"]
                    )

            processed.append(location)
            todo.remove(current_native)

            todo_ids = [id(obj) for obj in todo]
            for children in get_children_fields(current_native, current_local):
                for obj in children:
                    loc = getattr(obj, 'location', None)
                    if not (loc is not None and loc in processed) and \
                            not id(obj) in todo_ids:
                        todo.append(obj)

        f.close()
        for obj in to_clean:
            delattr(obj, 'location')

        return path

    def load(self, path):
        pass