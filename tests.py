#!/usr/bin/env python

import unittest
import quantities as pq
import session, utils


class BaseTest(unittest.TestCase):
	"""BaseTest class for all tests"""
	
	def setUp(self):
		self.s = session.init()

	def tearDown(self):
		self.s.shutdown()



class Tests( BaseTest ):

    def zztest_ls(self):
        self.s.ls()

    def zztest_pull(self):
        s1 = self.s.pull('/mtd/sec/1')

    def test_sync(self):
        #s1 = self.s.pull('/mtd/sec/1')
        #self.s.sync( s1, cascade=True )
        a1 = self.s.pull('/eph/seg/15')
        #a1 += 1*pq.V
        self.s.sync( a1, cascade=True )


if __name__ == '__main__':
	unittest.main()
