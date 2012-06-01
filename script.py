#!/usr/bin/env python

cookie = authenticate('bob', 'password')

list_data = requests.get(url+'/electrophysiology/analogsignal/6/',
	cookies=cookie)