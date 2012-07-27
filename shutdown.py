#!/usr/bin/env python

import pickle

import requests

import utils

url, username, password = utils.load_profile()

cookie_jar = utils.authenticate(url, username, password)

with open('cookie_jar.pkl', 'rb') as pkl_file:
	auth_cookie = pickle.load(pkl_file)

utils.shutdown(auth_cookie)