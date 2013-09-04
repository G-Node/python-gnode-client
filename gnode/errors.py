#!/usr/bin/env python

#TODO: offer more explanatory error messages by incorporating the object ids
# in the error message

import simplejson as json

#-------------------------------------------------------------------------------
# Operational errors
#-------------------------------------------------------------------------------

class AbsentConfigurationFileError(IOError):
	"""Exception raised when some of the specified config files do not exist """
	def __str__(self):
		return "Please check whether configuration and/or requirements file\
		     exists and is stored in the right directory"

class MisformattedConfigurationFileError(ValueError):
	"""Exception raised when the configuration data cannot be read from the
	JSON configuration files due to a misformatted file."""
	def __str__(self):
		return "Please check whether the configuration and/or requirements file\
		    follows the standard JSON format and contains the mandatory fields"

class FileUploadError( ValueError ):
    """ raised when some upload of the file fails """
    pass

class UnitsError( ValueError ):
    """ raised when units of the array object are not supported """
    pass

class ValidationError( ValueError ):
    """ raised when object validation fails """
    pass

class SyncFailed( ValueError ):
    """ raised when sync request sent but sync fails """
    pass

#-------------------------------------------------------------------------------
# HTTP server responses
#-------------------------------------------------------------------------------

class Error(Exception):
    """Base class for Gnode Client's exceptions."""
    #def __init__(self, message=''):
    #    self.message = message # error message

class BadRequestError(Error):
	"""Exception raised for a 400 "Bad request" server status code."""
	def _definition(self):
		return "Some of the request parameters are not provided correctly"

class UnauthorizedError(Error):
	"""Exception raised for a 401 "Unauthorized" server status code."""
	def _definition(self):
		return "Authorization key not provided"

class ForbiddenError(Error):
	"""Exception raised for a 403 "Forbidden" server status code."""
	def _definition(self):
		return "You don't have access to create, modify or view this object"

class NotFoundError(Error):
	"""Exception raised for a 404 "Not Found" server status code."""
	#TODO: Separate this in two errors
	def _definition(self):
		return "An object with the provided id does not exist or URL is \
		wrong and not supported"

class NotSupportedError(Error):
	"""Exception raised for a 405 "Not Supported" server status code."""
	def _definition(self):
		return "Request is not supported at this URL"

#-------------------------------------------------------------------------------
# Local object-related errors
#-------------------------------------------------------------------------------

class NotBoundToSession(Error):
	"""Error raised when a method or property of a server session is accessed
	when the client is being used in offline mode"""
	def __str__(self):
		return "Method or property not available. Object is not bound to \
		session."

class NotInDataStorage(Error):
	"""Error raised when methods that operate on server objects and the object
	has not yet been saved to the server"""
	def __str__(self):
		return "Object has not yet been saved to the Gnode datastore. Please \
		save object to the datastore before using this method."

class EmptyRequest(Error):
	"""Error raised when a method is called without the necessary parameters"""
	def __str__(self):
		return "Please review the method call and check if necessary \
		arguments were passed."

class ObjectTypeNotYetSupported(Error):
	"""Error raised when requesting object type not yet supported by the
	clien"""
	def __str__(self):
		return "The object type you have requested is not yet supported by \
		this client. Stay tunned!"


error_codes = {
    400:BadRequestError, 
    401:UnauthorizedError, 
    403:ForbiddenError,
    404:NotFoundError, 
    405:NotSupportedError
}
