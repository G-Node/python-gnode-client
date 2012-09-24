#!/usr/bin/env python

import unittest

import socket
import requests

import session, utils

"""
Tests to be implemented:
-
"""

#TODO: use this method somewhere to check that the server is reachable

class TestServerIsAlive(unittest.TestCase):

	@classmethod
	def setUpClass(self):
		self.host, self.port, self.https, self.prefix, self.username, self.password, self.cache_dir = utils.load_profile()

	@staticmethod
	def is_open(ip, port):
		"""code obtained from http://snipplr.com/view/19639/
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect((ip, int(port)))
			s.shutdown(2)
			return True
		except:
			return False

	def test_server_has_open_port(self):
		self.assertTrue(self.is_open(self.host, self.port))

	def test_prefix_is_correct(self):
		pass
		
	def test_is_gnode_server(self):
		pass


class BaseTest(unittest.TestCase):
	"""BaseTest class for all tests"""
	
	@classmethod
	def setUpClass(self):
		self.ses = session.init()

	@classmethod
	def tearDownClass(self):
		self.ses.shutdown()


class TestSessionInit(BaseTest):

	def test_has_cookie(self):
		self.assertTrue(self.ses.cookie_jar)

	

class TestGetAnalogSignal(BaseTest):

	def test_get_analogsignal(self):
		pass

if __name__ == '__main__':
	unittest.main()
