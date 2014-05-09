import uuid
import os
import h5py


class Dumper(object):
    """ dumps a given Native instance (recursively) to the temp HDF5 file """

    def dump(self, entity):
        name = uuid.uuid1().hex + ".h5"
        path = os.path.join("/tmp", name)  # FIXME get proper temppath

        f = h5py.File(path)

        todo = [entity]  # a stack of objects to submit
        processed = []  # collector of locations of processed objects

        while len(todo) > 0:
            local_native = todo[0]
            local_model = get_model_by_obj(local_native)  # empty model
            if local_model.location is not None:
                if local_model.location in processed:
                    continue  # workaround to avoid duplicate processing for Neo
            else:
                local_model.location = os.path.join(
                    local_model.get_location, id(local_native)
                ) + "/"  # fake location is needed to keep references

            try:
                remote_native = session.set(local_native, avoid_collisions)
                processed.append(remote_native.location)
                # below is a "side-effect" needed to have correct parents for
                # children and to avoid processing the same object twice, in
                # case of a non-tree hierarchies
                local_native.location = remote_native.location

            except HTTPError, e:  # some object fails to sync
                if fail:
                    if hasattr(e, 'response'):
                        raise Exception(e.response.content)
                    raise e
                else:
                    exceptions.append(e)
                    if len(local_model.child_fields) > 0:
                        continue
            finally:
                todo.remove(local_native)  # remove processed object

            todo_ids = [id(obj) for obj in todo]
            for field_name in local_model.child_fields:
                if hasattr(local_native, field_name) and \
                        hasattr(remote_native, field_name):

                    # set difference between the actual remote and local children
                    # references determines the list of children to delete
                    local_children = getattr(local_native, field_name, [])
                    remote_children = getattr(remote_native, field_name, [])
                    to_clean += compare_objs(local_children, remote_children)

                    # skip empty lazy-loaded proxy relations
                    if not (hasattr(local_children, '_is_loaded') and
                                not getattr(local_children, '_is_loaded')) and \
                            (local_children is not None):
                        for obj in local_children:
                            loc = getattr(obj, 'location', None)
                            if not (loc is not None and loc in processed) and \
                                    not id(obj) in todo_ids:
                                todo.append(obj)


    def load(self, path):
        pass