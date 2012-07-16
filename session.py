from utils import load_profile


def init( *args, **kwargs ):
    """ some easy to remember function to start g-node session """
    return Session( *args, **kwargs )


class Session( object ):
    """ Object to handle connection and client-server data transfer """

    def __init__(self, *args, **kwargs ):
        self.cookie_jar = utils.authenticate( load_profile() )
        # TODO of course make it more flexible


    def get(self, obj_type, obj_id=None, *kwargs):
        """ get one or several objects from the server """

        # send appropriate GET request to get objects from the server

        # deserialize received JSON object
        pass


    def create(self, obj, *kwargs):
        """ saves new object to the server """

        # serialize to JSON

        # send POST to create using API
        pass


    def bulk_update(self, obj_type, *kwargs):
        """ update several homogenious objects on the server """
        pass


    def delete(self, obj_type, obj_id=None, *kwargs):
        """ delete (archive) one or several objects on the server """
        pass
