#!/usr/bin/env python
#encoding: utf-8

import sys
import os

for li in open(sys.argv[1], 'r'):
    if li.rstrip() == "":
        print
    else:
        li_i = li.split('\t')
        print li_i[1], li_i[3], "DUMMY"

