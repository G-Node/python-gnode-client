#!/usr/bin/env python

import pickle

import requests

import utils, files, permissions

url, username, password = utils.load_profile()

# cookie_jar = utils.authenticate(url, username, password)

with open('cookie_jar.pkl', 'rb') as pkl_file:
	auth_cookie = pickle.load(pkl_file)

list_data = requests.get(url+'/electrophysiology/analogsignal/6/',
	cookies=auth_cookie)

list_files = requests.get(url+'datafiles/', cookies=auth_cookie)

permissions.get_permissions(auth_cookie, 'section', 1)