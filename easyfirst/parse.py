#!/usr/bin/env python

## Copyright 2017 Keisuke Sakaguchi
## Copyright 2013 Yoav Goldberg
##
##    This is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This code is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with This code.  If not, see <http://www.gnu.org/licenses/>.


import sys
from pio import io
from easyfirst import test,parse,Model

from optparse import OptionParser

usage="""usage: %prog -m model [options] input_file """ 

parser = OptionParser(usage)
parser.add_option("-m","--model",dest="model_file")
parser.add_option("--iter",dest="iter",default="FINAL")
parser.add_option("-e","--eval",action="store_true",dest="eval",default=False)
parser.add_option("--nopunct",action="store_true",dest="ignore_punc",default=False)
parser.add_option("-t",dest="tagged",action="store_true",default=False)

opts, args = parser.parse_args()

def read_tagged(fh):
   for line in fh:
      res = (x.rsplit("_",1) for x in line.strip().split())
      res = [{'form':f,'id':id,'tag':t} for id,(f,t) in enumerate(res,1)]
      yield res
      

if (not opts.model_file) or (len(args)!=1):
   parser.print_usage()
   sys.exit()

TEST_FILE = args[0]


if opts.tagged:
   reader=read_tagged
else:
   reader=io.conll_to_sents

model = Model.load("%s" % opts.model_file, opts.iter)

test_sents = [s for s in reader(file(TEST_FILE))]


attachonly = False
if "E00" in opts.model_file: 
    attachonly = True

if opts.eval:
   test(test_sents, model, opts.iter, quiet=False, ignore_punc=opts.ignore_punc, labeled=False)
else:
   parse(attachonly, test_sents, model, opts.iter)


