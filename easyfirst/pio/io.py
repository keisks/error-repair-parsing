## Copyright Keisuke Sakaguchi (2017)
## Originally under GPL by Yoav Goldberg (2013)
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

import sys
import yutils
from collections import defaultdict

sys.path.append("..")
import common

def to_tok(line):
   if line[4]=="_": line[4]=line[3]
   return {"parent": int(line[-4]),
           "prel"  : line[-3],
           "form"  : line[1], 
           "lem"  : line[2], 
           "id"    : int(line[0]), 
           "tag"   : line[4],
           "ctag"   : line[3],
           "morph" : line[-5],
           "extra" :  line[-1],
           }

def to_tok_str(line):
   if line[4]=="_": line[4]=line[3]
   return {"parent": line[-4],
           "prel"  : line[-3],
           "form"  : line[1], 
           "lem"  : line[2], 
           "id"    : line[0], 
           "tag"   : line[4],
           "ctag"   : line[3],
           "morph" : line[-5],
           "extra" :  line[-1],
           }

def conll_to_sents(fh,ignore_errs=True):
   for sent in yutils.tokenize_blanks(fh):
      if ignore_errs and sent[0][0][0]=="@": continue
      yield [to_tok(l) for l in sent]

def conll_to_sents_strids(fh,ignore_errs=True):
   for sent in yutils.tokenize_blanks(fh):
      if ignore_errs and sent[0][0][0]=="@": continue
      yield [to_tok_str(l) for l in sent]

def ann_conll_to_sents(fh):
   sent=[]
   for line in fh:
      line = line.strip()
      if not line: 
         if sent:
            yield [to_tok(l) for l in sent]
            sent = []
      elif line.startswith("@@"):
         if sent:
            yield sent
            sent = []
         yield line
      else:
         sent.append(line.split())
   if sent:
      yield [to_tok(l) for l in sent]

def conll_to_sents2(fh,ignore_errs=True):
   from common import ROOT
   for sent in yutils.tokenize_blanks(fh):
      if ignore_errs and sent[0][0][0]=="@": continue
      sent = [to_tok(l) for l in sent]
      for tok in sent:
         par = tok['parent']
         if par==0: tok['partok']=ROOT
         elif par==-1: tok['partok']=None
         else: tok['partok']=sent[par-1]
      yield sent

def read_dep_trees(fh,ignore_errs=True):
   for sent in conll_to_sents(fh, ignore_errs): 
      yield DepTree(sent)

def kbest_conll_to_sents(fh,ignore_errs=True):
   while True:
      count = int(fh.next().strip())
      k=[]
      for i,sent in zip(xrange(count), yutils.tokenize_blanks(fh)):
         if ignore_errs and sent[0][0][0]=="@": continue
         k.append( [to_tok(l) for l in sent] )
      yield k

class DepTree:
   def __init__(self, sent):
      self.toks=sent[:]
      self._tok_by_id=dict([(t['id'],t) for t in sent])
      self._tok_by_id[0]=common.ROOT
      self._childs=defaultdict(list)
      self._parents={}
      for tok in sent:
         self._childs[tok['parent']].append(tok)
         self._parents[tok['id']] = self._tok_by_id[tok['parent']]

   def itertokens(self):
      for t in self.toks: yield t

   def parent(self, tok):
      return self._parents[tok['id']]

   def childs(self, tok):
      return self._childs[tok['id']]

def out_conll(sent,out=sys.stdout,parent='parent',form='form',prel='prel'):
   for tok in sent:
      try:
         out.write("%s\n" % "\t".join(map(str, [tok['id'], tok[form], tok['lem'],tok['tag'],tok['tag'],"_",tok[parent],tok[prel],"_",tok.get('extra','_')])))
      except KeyError,e:
         print e
         print tok
         raise e
   out.write("\n") 

def add_parents_annotation(sents, parents_file):
   sents = list(sents)
   parents_annotations = list(yutils.tokenize_blanks(file(parents_file)))
   assert len(sents)==len(parents_annotations)
   for s,p in zip(sents, parents_annotations):
      assert len(s)==len(p)
      for tok,parents in zip(s,p):
         id = int(parents[0])
         pars = [int(x.split(":")[0]) for x in parents[1:]]
         scrs = [x.split(":")[1] for x in parents[1:]]
         assert(id==tok['id'])
         tok['cand_parents'] = pars
   return sents


