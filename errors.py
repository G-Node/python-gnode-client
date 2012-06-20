#!/usr/bin/env python

"""
gnode-client.exceptions
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the set of Gnode Client's exceptions.

"""
#TODO: offer more explanatory error messages by incorporating the object ids
# in the error message

#NOTE!!!!: using simplejson.JSONDecodeError makes simplejson a mandatory
#	requirement since json doesn't have that error!!!
import simplejson as json

#------------------Configuration file errors------------------------
class AbsentConfigurationFileError(IOError):
	"""Exception raised when the specified configuration file does not exist.
	
	Args:
		err: the IOError raised; will be printed and help user recognize e.g.
			a typo in the filename
	"""
	#TODO?: handle the different IOError types using the beginning of the
	#	error message. e.g. [Errno 2], etc...
	#TODO: change 'in the right directory' to something more meaningful once
	#	it is settled which one that should be
	def __init__(self, err=None):
		pass
	def __str__(self):
		if err:
			err_str = err.__str__()
		else:
			err_str = ""

		return err_str + "\n Please check whether configuration file \
		exists and is stored in the right directory"

class MisformattedConfigurationFileError(json.JSONDecodeError):
	"""Exception raised when the configuration data cannot be read from the
	JSON configuration file due to a misformatted file.

	Args:
		err: the JSONDecodeError raised by load_profile()
	"""
	def __init__(self, err):
		pass
	def __str__(self):
		if err:
			err_str = err.__str__()
		else:
			err_str = ""

		return err.__str__() + "\n Please check whether the configuration \
		file follows the standard JSON format and contains the mandatory \
		fields"


#------------------Server request errors------------------------
class Error(Exception):
	"""Base class for Gnode Client's exceptions."""
	pass

class BadRequestError(Error):
	"""Exception raised for a 400 "Bad request" server status code."""
	def __init__(self):
		pass
	def __str__(self):
		return "Some of the request parameters are not provided correctly"

class UnauthorizedError(Error):
	"""Exception raised for a 401 "Unauthorized" server status code."""
	def __init__(self):
		pass
	def __str__(self):
		return "Authorization key not provided"

class ForbiddenError(Error):
	"""Exception raised for a 403 "Forbidden" server status code."""
	def __init__(self):
		pass
	def __str__(self):
		return "You don't have access to create, modify or view this object"

class NotFoundError(Error):
	"""Exception raised for a 404 "Not Found" server status code."""
	#TODO: Separate this in two errors
	def __init__(self):
		pass
	def __str__(self):
		return "An object with the provided id does not exist or URL is \
		wrong and not supported"

class NotSupportedError(Error):
	"""Exception raised for a 405 "Not Supported" server status code."""
	def __init__(self):
		pass
	def __str__(self):
		return "Request is not supported at this URL"

error_codes = {400:BadRequestError, 401:UnauthorizedError, 403:ForbiddenError,
404:NotFoundError, 405:NotSupportedError}