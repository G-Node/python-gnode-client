#!/usr/bin/env python

import pickle

import requests

import utils

url, username, password = utils.load_profile()

cookie_jar = utils.authenticate(url, username, password)

with open('cookie_jar.pkl', 'wb') as output:
	pickle.dump(cookie_jar, output)