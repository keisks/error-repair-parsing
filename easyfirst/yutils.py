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
##    along with this code.  If not, see <http://www.gnu.org/licenses/>.


from collections import defaultdict

def tokenize_blanks(fh):
   stack = []
   for line in fh:
      line = line.strip().split()
      if not line:
         if stack: yield stack
         stack = []
      else:
         stack.append(line)
   if stack: yield stack

def ngrams(strm,n=2):
    stack = []
    for item in strm:
       if len(stack) == n:
          yield tuple(stack)
          stack = stack[1:]
       stack.append(item)
    if len(stack)==n: yield tuple(stack)

def count(strm,dct=False):
   d = defaultdict(int)
   for item in strm: d[item]+=1
   if dct: return d
   else: return sorted(d.items(),key=lambda x:x[1])
 
def read_words_from_raw_file(filename, tokenizer=lambda line:line.strip().split()):
   for line in file(filename):
      for item in tokenizer(line): 
         yield item

from future import *  # this will get me Counter (python 2.7) and namedtuple (python 2.6)

def Grouper(seq, key=lambda x:x,val=lambda x:x):
   d = defaultdict(Counter)
   for item in seq:
      k = key(item)
      v = val(item)
      d[k][v]+=1
   return dict(d)

class frozendict(dict):
    def _blocked_attribute(obj):
        raise AttributeError, "A frozendict cannot be modified."
    _blocked_attribute = property(_blocked_attribute)

    __delitem__ = __setitem__ = clear = _blocked_attribute
    pop = popitem = setdefault = update = _blocked_attribute

    def __new__(cls, *args):
        new = dict.__new__(cls)
        dict.__init__(new, *args)
        return new

    def __init__(self, *args):
        pass

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(tuple(sorted(self.items())))
            return h

    def __repr__(self):
        return "frozendict(%s)" % dict.__repr__(self)


class Count(Counter):
   def add(self, v): self[v] += 1

class Group(defaultdict):
    def __init__(self, key=lambda x:x, val=lambda x:x, vals_in=Count, seq=[]):
       defaultdict.__init__(self, vals_in)
       self._keyf = key
       self._valf = val
       self._colltype = vals_in
       self.update(seq)
 
    def update(self, seq):
       for k,v in ( (self._keyf(item), self._valf(item)) for item in seq):
          self[k].add(v)
 
    def add(self, item):
       k = self._keyf(item)
       v = self._valf(item)
       self[k].add(v)
 
 
