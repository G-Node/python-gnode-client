#!/usr/bin/env python

import simplejson as json
import odml

from .models import Value, Section, Property

class odMLSerializer(object):
	"""Class of odML deserialzers"""
	
	@classmethod
	def deserialize(cls, json_dict, session):
		"""Meta function to deserialize any metadata object"""
		#TODO: handle lists as well
		try:
			model = json_dict['selected']['model']
		except:
			raise ValueError

		if model == 'metadata.value':
			return cls.value(json_dict)
		elif model == 'metadata.property':
			return cls.property(json_dict)
		elif model == 'metadata.section':
			return cls.section(json_dict)

	@staticmethod
	def value(json_dict, session):
		permalink = json_dict['selected']
		fields = json_dict['selected']['fields']

		data = fields['data']
		parent_property = fields['parent_property']

		obj = Value(data=data, parent_property=parent_property,
			permalink=permalink)
		return obj

	@staticmethod
	def section(json_dict, session):
		permalink = json_dict['selected']
		fields = json_dict['selected']['fields']

		name = fields['name']
		parent_section = fields['parent_section']
		is_template = fields['is_template']
		user_custom = fields['user_custom']
		tree_position = fields['tree_position']

		#TODO: What to do with odml_type?

		obj = Section(name=name, parent_section=parent_section,
			is_template=is_template, user_custom=user_custom,
			tree_position=tree_position, permalink=permalink)

		#TODO: Probably parent_section and tree_position shouldn't be in
		# __init__ but used to further processing of the object

		return obj

	@staticmethod
	def property(json_dict, session):
		
		pass