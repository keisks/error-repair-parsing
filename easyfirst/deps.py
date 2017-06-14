## Copyright 2017 Keisuke Sakaguchi
## Copyright 2013 Yoav Goldberg
##
##    This is is free software: you can redistribute it and/or modify
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
import kskutil

from collections import defaultdict

class DependenciesCollection: #{{{
   def __init__(self):
      self.deps = set()
      #self.all_childs = set()
      self._left_child = {}
      self._right_child = {}
      self._left_child2 = {}
      self._right_child2 = {}
      self._num_left_c = {}
      self._num_right_c = {}
      self._parents = {}
      self._labels = {}
      self._childs = defaultdict(list)

   def decrement(self, idx_bound):
       new_dep = set()
       #print self.deps
       for curr_p, curr_c in self.deps:
           new_p = int(curr_p)
           new_c = int(curr_c)
           if curr_p == idx_bound or curr_c == idx_bound:
               pass
           else:
               if curr_p > idx_bound:
                   new_p -= 1
               if curr_c > idx_bound:
                   new_c -= 1
               new_dep.add((new_p, new_c))
       self.deps = new_dep
       #print self.deps

       for k, v in self._left_child.items():
           new_k = int(k)
           if k > idx_bound:
               new_k -= 1
           new_v = kskutil.decrementToken(v, idx_bound)
           self._left_child[new_k] = new_v
       for k, v in self._right_child.items():
           new_k = int(k)
           if k > idx_bound:
               new_k -= 1
           new_v = kskutil.decrementToken(v, idx_bound)
           self._right_child[new_k] = new_v
              
       for k, v in self._left_child2.items():
           if k > idx_bound:
               self._left_child2[k-1] = v

       for k, v in self._right_child2.items():
           if k > idx_bound:
               self._right_child2[k-1] = v

      
       for k, v in self._num_left_c.items():
           if k > idx_bound:
               self._num_left_c[k-1] = v

       for k, v in self._num_right_c.items():
           if k > idx_bound:
               self._num_right_c[k-1] = v

       for k, v in self._parents.items():
           new_k = int(k)
           if k == idx_bound: 
               del self._parents[k]
           if k > idx_bound:
               new_k -= 1
           new_v = kskutil.decrementToken(v, idx_bound)
           self._parents[new_k] = new_v

       for k, v in self._labels.items():
           if k > idx_bound:
               self._labels[k-1] = v

       for k, v in self._childs.items():
           new_k = int(k)
           if k > idx_bound:
               new_k -= 1
           if k == idx_bound:
               del self._childs[k]
           
           new_childs = []
           for j, d_j in enumerate(v):
               new_d_j = kskutil.decrementToken(d_j, idx_bound)
               new_childs.append(new_d_j)
           self._childs[new_k] = new_childs

   def increment(self, idx_bound):
       #print self.deps
       new_dep = set()
       for curr_p, curr_c in self.deps:
           new_p = int(curr_p)
           new_c = int(curr_c)
           if curr_p >= idx_bound:
               new_p += 1
           if curr_c >= idx_bound:
               new_c += 1
           new_dep.add((new_p, new_c))
       self.deps = new_dep
       #print self.deps

       for k in sorted(self._left_child.keys(), reverse=True):
           v = self._left_child[k]
           new_k = int(k)
           if k >= idx_bound:
               new_k += 1
           new_v = kskutil.incrementToken(v, idx_bound)
           self._left_child[new_k] = new_v

       for k in sorted(self._right_child.keys(), reverse=True):
           v = self._right_child[k]
           new_k = int(k)
           if k >= idx_bound:
               new_k += 1
           new_v = kskutil.incrementToken(v, idx_bound)
           self._right_child[new_k] = new_v
              
       for k in sorted(self._left_child2.keys(), reverse=True):
           v = self._left_child2[k]
           if k >= idx_bound:
               self._left_child2[k+1] = v

       for k in sorted(self._right_child2.keys(), reverse=True):
           v = self._right_child2[k]
           if k >= idx_bound:
               self._right_child2[k+1] = v

       for k in sorted(self._num_left_c.keys(), reverse=True):
           v = self._num_left_c[k]
           if k >= idx_bound:
               self._num_left_c[k+1] = v

       for k in sorted(self._num_right_c.keys(), reverse=True):
           v = self._num_right_c[k]
           if k >= idx_bound:
               self._num_right_c[k+1] = v

       for k in sorted(self._parents.keys(), reverse=True):
           v = self._parents[k]
           new_k = int(k)
           if k >= idx_bound:
               new_k += 1
           new_v = kskutil.incrementToken(v, idx_bound)
           self._parents[new_k] = new_v

       for k in sorted(self._labels.keys(), reverse=True):
           v = self._labels[k]
           if k >= idx_bound:
               self._labels[k+1] = v

       for k in sorted(self._childs.keys(), reverse=True):
           v = self._childs[k]
           new_k = int(k)
           if k >= idx_bound:
               new_k += 1
           
           new_childs = []
           for j, d_j in enumerate(v):
               new_d_j = kskutil.incrementToken(d_j, idx_bound)
               new_childs.append(new_d_j)
           self._childs[new_k] = new_childs


   def has_parent(self, child):
      return child['id'] in self._parents

   def add(self, parent, child, label="_"):
      self.deps.add((parent['id'], child['id']))
      self._parents[child['id']]=parent
      self._labels[child['id']] = label
      self._childs[parent['id']].append(child)
      child['pprel'] = label

      pid = parent['id']
      if child['id'] < parent['id']:
         lc = self.left_child(parent)
         if (not lc) or child['id'] < lc['id']:
            if lc: self._left_child2[pid]=lc
            self._left_child[pid]=child
            self._num_left_c[pid] = self._num_left_c.get(pid,0) + 1

      if child['id'] > parent['id']:
         rc = self.right_child(parent)
         if (not rc) or child['id'] > rc['id']:
            if rc: self._right_child2[parent['id']]=rc
            self._right_child[parent['id']]=child
            self._num_right_c[pid] = self._num_right_c.get(pid,0) + 1

   #{{{ remove
   def remove(self, parent, child):
      pid = parent['id']
      cid = child['id']
      children = self.children(parent)
      children.remove(child)
      self.deps.remove((pid,cid))
      del self._parents[cid]
      self._childs[pid].remove(cid)
      if child == self.left_child(parent):
         del self._left_child[pid]
         if children:
            if children[0]['id']<pid: self._left_child[pid]=children[0]
      elif child == self.right_child(parent):
         del self._right_child[pid]
         if children:
            if children[-1]['id']>pid: self._right_child[pid]=children[-1]

   def remove_left_children(self, parent):
      pid = parent['id']
      for c in self.children(parent):
         if c['id']>pid: break
         self.remove(parent,c)

   def remove_right_children(self,parent):
      pid = parent['id']
      for c in self.children(parent):
         if c['id']<pid: continue
         self.remove(parent,c)

   def remove_parent(self,child):
      self.remove(self.parent(child),child)
   #}}}

   def annotate(self, sent):
      for tok in sent:
         try:
            tok['pparent'] = self._parents[tok['id']]['id']
            tok['pprel'] = self._labels[tok['id']]
         except KeyError: 
            sys.stderr.write("defaulting to root-parent")
            print self.deps
            raise
            tok['pparent'] = 0
      return sent

   def annotate_allow_none(self, sent):
      for tok in sent:
         try:
            tok['pparent'] = self._parents[tok['id']]['id']
         except KeyError: 
            tok['pparent'] = -1
      return sent

   def left_child(self, tok):
      if not tok: return None
      return self._left_child.get(tok['id'],None)

   def right_child(self, tok):
      if not tok: return None
      return self._right_child.get(tok['id'],None)

   def left_child2(self, tok):
      if not tok: return None
      return self._left_child2.get(tok['id'],None)

   def right_child2(self, tok):
      if not tok: return None
      return self._right_child2.get(tok['id'],None)

   def num_left_children(self, tok):
      if not tok: return 0
      return self._num_left_c.get(tok['id'],0)

   def num_right_children(self, tok):
      if not tok: return 0
      return self._num_right_c.get(tok['id'],0)

   def children(self, tok):
      if not tok: return []
      return self._childs[tok['id']]

   def get_depth(self, tok):
      children = self.children(tok)
      if not children: return 1
      depths = [self.get_depth(c) for c in self.children(tok)]
      return max(depths)+1

   def left_labels(self, tok):
      if not tok: return None
      children = self.children(tok)
      return "-".join([self.label_for(c) for c in children if c['id'] < tok['id']])
   def right_labels(self, tok):
      if not tok: return None
      children = self.children(tok)
      return "-".join([self.label_for(c) for c in children if c['id'] > tok['id']])

   def label_for(self, tok):
      return self._labels.get(tok['id'],None)

   def sibling(self, tok, i=1):
      if tok==None: return None
      parent = self._parents.get(tok['id'],None)
      if parent: parent = parent['id']
      self._childs[parent].sort(key=lambda x:x['id'])
      siblings = self._childs[parent]
      index = siblings.index(tok)
      if 0 < (index+i) < len(siblings):
         return siblings[index+i]
      return None

   def span(self, tok):
      return self.right_border(tok) - self.left_border(tok)

   def parent(self, tok):
      return self._parents[tok['id']] if tok['id'] in self._parents else None

   def right_border(self,tok):
      r = self.right_child(tok)
      if not r: return int(tok['id'])
      else: return self.right_border(r)

   def left_border(self,tok):
      l = self.left_child(tok)
      if not l: return int(tok['id'])
      else: return self.left_border(l)
#}}}

