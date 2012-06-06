#!/usr/bin/env python

"""
gnode-client.exceptions
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the set of Gnode Client's exceptions.

"""

class Error(Exception):
	"""Base class for Gnode Client's exceptions."""
	pass

class NotSupportedError(Error):
	"""Exception raised for a 405 "Not Supported" server status code."""
	def __init__(self):
		pass
	def __str__(self):
		return "Request is not supported at this URL"

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