#!/usr/bin/env python

"""odML models"""

import odml

class BaseObject(object):
	"""Base Object class for G-node odML classes."""
	global_attr = ('permalink', 'safety_level', 'owner',
		'last_modified', 'date_created')

	def __init__(self, permalink=None, safety_level=None, parent_property=None):
		"""Init method"""
		for a in ('permalink', 'safety_level'):
			setattr(self, a, eval(a))
    	#TODO: What to do with datecreated, lastmodified, owner?

	def save(self):
		"""Method to save the Metadata Object"""
		pass



class Value(odml.value.BaseValue, BaseObject):
	"""G-node implementation of the odML Value class
	"""
	_local_attr = ('data', 'parent_property')

	def __init__(self, data, parent_property=None, permalink=None):
		super(odml.Value, self).__init__(data=data)
		super(BaseObject, self).__init__(permalink=permalink)
		#This will be used in the serialization
		self._parent_property = parent_property



class Property(odml.property.BaseProperty, BaseObject):
	"""G-node implementation of the odML Property class
	"""
	_local_attr = ('name', 'definition', 'dependency', 'dependency_value',
		'mapping', 'unit', 'dtype', 'uncertainty', 'comment', 'section')

	def __init__(self, name, value, definition=None, dependency=None,
		dependency_value=None, mapping=None, unit=None, dtype=None,
		uncertainty=None, comment=None, section=None, permalink=None):

		super(odml.Property, self).__init__(name=name, value=value,
		definition=definition, dependency=dependency,
		dependency_value=dependency_value, mapping=mapping, unit=unit,
		dtype=dtype, uncertainty=uncertainty)
		super(BaseObject, self).__init__(permalink=permalink)

		self._section = section		
		#Where does comment come from? It is not implemented by python-odML
		self._comment = comment

class Section(odml.section.BaseSection, BaseObject):
	"""G-node implementation of the odML Property class
	"""
	_local_attr = ('name', 'description', 'odml_type', 'parent_section',
		'tree_position', 'is_template', 'user_custom')
	#TODO:
	#Is type (odML __init__() argument) the same as odml_type ?
	#if so change in super(odml.Section, self).__init__ type=type to 
	#type=odml_type

	#Parent Section is a Gnode reference, whereas parent is odML.
	# Is it necessary to keep both?
	def __init__(self, name, type='undefined', parent=None, mapping=None, 
		parent_section=None, tree_position=None, is_template=None,
		user_custom=None, permalink=None):

		#TODO!: Get, parent, deserialize it and pass it as an argument
		#to  super(odml.Section, self).__init__()
		super(odml.Section, self).__init__(name=name, type=type,
			mapping=mapping)
		super(BaseObject, self).__init__(permalink=permalink)

		self._parent_section = parent_section
		self._is_template = is_template
		self._user_custom = user_custom
		self._tree_position = tree_position


class Document(odml.doc.BaseDocument, BaseObject):
	"""G-node implementation of the odML Document class
	"""

	#TODO!: Couldn't find out which properties are already supported by
	# the Gnode
	_local_attr = ('data', 'parent_property')

	def __init__(self, author=None, date=None, version=None, repository=None,
		permalink=None):
		super(odml.Document, self).__init__(author=author, date=date,
			version=version, repository=repository)
		super(BaseObject, self).__init__(permalink=permalink)
