#!/usr/bin/env python
# encoding: utf-8
"""
debug

Created by Brennan Chapman on 2012-10-04.
Copyright (c) 2012 Moonbot Studios. All rights reserved.

Set of tools to assist in script debugging.
"""

import profile
import gprof2dot

def reloadAll():
	import profile
	reload(profile)
	import gprof2dot
	reload(gprof2dot)