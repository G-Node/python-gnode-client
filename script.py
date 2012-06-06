#!/usr/bin/env python

url, username, password = load_profile()

auth_cookie = authenticate(url, username, password)

list_data = requests.get(url+'/electrophysiology/analogsignal/6/',
	cookies=auth_cookie)