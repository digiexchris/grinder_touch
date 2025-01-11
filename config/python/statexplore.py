#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import linuxcnc
try:
    s = linuxcnc.stat() # create a connection to the status channel
    s.poll() # get current values
    # pos = s.getattr("position")
    # print(s.position)
except (linuxcnc.error, detail):
    print("error", detail)
    sys.exit(1)


for x in dir(s):
    if not x.startswith("_"):
        print(x, getattr(s,x))