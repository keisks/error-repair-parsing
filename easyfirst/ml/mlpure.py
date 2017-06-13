## Copyright 2010,2011,2013 Yoav Goldberg
##
##    This code is free software: you can redistribute it and/or modify
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
##    along with this code.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import sys
print >> sys.stderr,"""
Using the pure-python prediction moule.  This is slow, and can not be used for training.

Much faster parsing is possible using the compiled module.  See code/ml/INSTALL for details.
"""

class MulticlassModel: 
   __slots__ = "W biases nclas probs_output".split()

   def load(self,fname):
      sys.stderr.write("loading model %s" % fname)
      fh = codecs.open(fname,encoding="utf8")
      line = fh.next()
      nclasses = len(line.strip().split())-1
      _WS = [dict() for i in xrange(nclasses)]
      while True:
         f,ws = line.strip().split(None,1)
         ws = [float(w) for w in ws.split()]
         for w,d in zip(ws,_WS):
            d[f]=w
         try:
            line = fh.next()
         except StopIteration: break
      if not '**BIAS**' in _WS[0]:
         for d in _WS: d['**BIAS**']=0

      self.nclas = nclasses
      self.WS=_WS
      print >> sys.stderr, "done loading"

   def __init__(self, fname, probs_output=False):
      self.W = {}
      self.probs_output=probs_output
      self.load(fname)
      sys.stderr.write(" done\n")

   def predict(self,features):
      scores=[]
      features = ['**BIAS**']+features
      for i,w in enumerate(self.WS):
         scores.append(sum((w.get(f,0)) for f in features))
      if self.probs_output:
         scores = [math.exp(s) for s in scores]
         tot = sum(scores)
         scores = [s/tot for s in scores]
      scores = [(s,i) for i,s in enumerate(scores)]
      best = max([(s,i) for i,s in enumerate(scores)])
      return best[1],scores

   def get_scores(self,features):
      scores=[]
      features = ['**BIAS**']+features
      for i,w in enumerate(self.WS):
         scores.append(sum((w.get(f,0)) for f in features))
      return scores

   #}}}
