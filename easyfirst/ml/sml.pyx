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

"""
Sparse versions of MulticlassParamData and MultitronParameters.
These are sparse in the sense that (param,class) pairs which did not participate in
an update do not take-up space.
"""
import sys
from stdlib cimport *

## These are used for training.

cdef struct Param:
   int clas
   double acc
   double w
   int lastUpd

cdef class SparseMulticlassParamData:
   cdef Param *params
   cdef int current_size
   def __cinit__(self):
      cdef int i
      cdef int initial_size = 2
      self.params = <Param *>malloc(initial_size*sizeof(Param))
      self.current_size = initial_size
      for i in range(self.current_size):
         self.params[i].clas=-1
         self.params[i].lastUpd=0
         self.params[i].acc=0
         self.params[i].w=0
   
   cdef double w_for_clas(self, int clas):
      for i in xrange(self.current_size):
         if self.params[i].clas == -1:
            return 0
         elif self.params[i].clas == clas:
            return self.params[i].w
      return 0

   cdef void multiply_w_by(self, double scalar):  
      for i in xrange(self.current_size):
         if self.params[i].clas == -1:
            return
         self.params[i].w*=scalar

   cdef int get_param_index_for(self, int clas):
      """
      Get the index of the Param for the given clas,
      creating a new one if needed.
      """
      for i in xrange(self.current_size):
         if self.params[i].clas == clas:
            return i
         elif self.params[i].clas == -1:
            self.params[i].clas = clas
            return i
      # If we got here, we scanned all entries without
      # finding the clas. Increase the size and add the clas.
      cdef int new_size = self.current_size * 2
      cdef Param *new_params = <Param *>malloc(new_size*sizeof(Param))
      for i in xrange(self.current_size):
         new_params[i] = self.params[i]
      free(self.params)
      self.params = new_params
      for i in xrange(self.current_size, new_size):
         self.params[i].clas=-1
         self.params[i].lastUpd=0
         self.params[i].acc=0
         self.params[i].w=0
      self.params[self.current_size].clas = clas
      cdef int res = self.current_size
      self.current_size = new_size
      return res

   cdef void add_to_clas(self, int clas, double amount, int now):
      cdef int i = self.get_param_index_for(clas)
      self.params[i].acc += (now-self.params[i].lastUpd)*self.params[i].w
      self.params[i].w += amount
      self.params[i].lastUpd = now

   cdef void set_clas_w_to(self, int clas, double score, int now):
      cdef int i = self.get_param_index_for(clas)
      self.params[i].acc += (now-self.params[i].lastUpd)*self.params[i].w
      self.params[i].w = score
      self.params[i].lastUpd = now

   cdef void add_from_other(self, SparseMulticlassParamData other, double factor, int now):
      for i in xrange(other.current_size):
         if other.params[i].clas == -1: break
         self.add_to_clas(other.params[i].clas, other.params[i].w * factor, now)

   cdef void add_w_to_scores(self, double *scores):
      for i in xrange(self.current_size):
         if self.params[i].clas == -1: break
         else:
            scores[self.params[i].clas] += self.params[i].w

   cdef void finalize(self, int now):
      for i in xrange(self.current_size):
         if self.params[i].clas == -1: break
         self.params[i].acc+=(now-self.params[i].lastUpd)*self.params[i].w
         self.params[i].w = self.params[i].acc / now

   cdef double avgd_w_for_clas(self, int clas, int now):
      for i in xrange(self.current_size):
         if self.params[i].clas == -1: break
         if self.params[i].clas == clas:
            return (self.params[i].acc + ((now - self.params[i].lastUpd) * self.params[i].w)) / now
      return 0

   def __dealloc__(self):
      free(self.params)

cdef class SparseMultitronParameters:
   cdef:
      int nclasses
      int now
      dict W

      double* scores # (re)used in calculating prediction
   
   def __cinit__(self, nclasses):
      self.scores = <double *>malloc(nclasses*sizeof(double))

   cpdef getW(self, clas): 
      d={}
      cdef SparseMulticlassParamData p
      for f,p in self.W.iteritems():
         d[f] = p.w_for_clas(clas)
      return d

   def __init__(self, nclasses):
      self.nclasses = nclasses
      self.now = 0
      self.W = {}

   cdef _tick(self):
      self.now=self.now+1

   def tick(self): self._tick()

   cpdef scalar_multiply(self, double scalar):
      """
      note: DOES NOT support averaging
      """
      cdef SparseMulticlassParamData p
      cdef int c
      for p in self.W.values():
         p.multiply_w_by(scalar)
         for c in xrange(self.nclasses):
            p.w[c]*=scalar

   cpdef add(self, list features, int clas, double amount):
      cdef SparseMulticlassParamData p
      for f in features:
         try:
            p = self.W[f]
         except KeyError:
            p = SparseMulticlassParamData()
            self.W[f] = p
         p.add_to_clas(clas, amount, self.now)

   cpdef set(self, list features, int clas, double amount):
      """
      like "add", but replaces instead of adding
      """
      cdef SparseMulticlassParamData p
      cdef double v
      cdef str f
      for f in features:
         try:
            p = self.W[f]
         except KeyError:
            p = SparseMulticlassParamData()
            self.W[f] = p
         p.set_clas_w_to(clas, amount, self.now)

   cpdef add_params(self, SparseMultitronParameters other, double factor):
      """
      like "add", but with data from another MultitronParameters object.
      they must both share the number of classes
      add each value * factor
      """
      cdef SparseMulticlassParamData p
      cdef SparseMulticlassParamData op
      cdef double v
      cdef str f
      cdef int clas
      for f,op in other.W.items():
         try:
            p = self.W[f]
         except KeyError:
            p = SparseMulticlassParamData()
            self.W[f] = p
         p.add_from_other(op, factor, self.now)

   cpdef get_scores(self, features):
      cdef SparseMulticlassParamData p
      cdef int i
      cdef double w
      for i in xrange(self.nclasses):
         self.scores[i]=0
      for f in features:
         try:
            p = self.W[f]
            p.add_w_to_scores(self.scores)
         except KeyError: pass
      cdef double tot = 0
      res={}
      for i in xrange(self.nclasses):
         res[i] = self.scores[i]
      return res

   cpdef get_best_class(self, features):
      cdef SparseMulticlassParamData p
      cdef int i
      cdef double w
      cdef int best_i
      cdef double best_score
      for i in xrange(self.nclasses):
         self.scores[i]=0
      for f in features:
         try:
            p = self.W[f]
            p.add_w_to_scores(self.scores)
         except KeyError: pass
      cdef double tot = 0
      best_score = self.scores[0]
      best_i = 0
      for i in xrange(self.nclasses):
         if self.scores[i] > best_score:
            best_i = i
            best_score = self.scores[i]
      return (best_score,best_i)

   def update(self, correct_class, features):
      """
      does a prediction, and a parameter update.
      return: the predicted class before the update.
      """
      self._tick()
      prediction = self._predict_best_class(features)
      if prediction != correct_class:
         self._update(correct_class, prediction, features)
      return prediction

   cdef int _predict_best_class(self, list features):
      cdef int i
      cdef SparseMulticlassParamData p
      for i in range(self.nclasses):
         self.scores[i]=0
      for f in features:
         #print "lookup", f
         try:
            p = self.W[f]
            p.add_w_to_scores(self.scores)
         except KeyError: 
            #print "feature",f,"not found"
            pass
      # return best_i
      cdef int best_i = 0
      cdef double best = self.scores[0]
      for i in xrange(1,self.nclasses):
         if best < self.scores[i]:
            best_i = i
            best = self.scores[i]
      return best_i

   cdef _update(self, int goodClass, int badClass, list features):
         self.add(features, goodClass, 1.0)
         self.add(features, badClass, -1.0)
         # TODO: can be made a tiny bit faster by looking up the SparseMulticlassParamData only once per feature
         # and not twice as is done now. (see implementation in the (non-sparse)  MultitronParameters)

   def finalize(self):
      cdef SparseMulticlassParamData p
      # average
      for f in self.W.keys():
         p = self.W[f]
         p.finalize(self.now)

   #def dump(self, out=sys.stdout):
   #   cdef SparseMulticlassParamData p
   #   for f in self.W.keys():
   #      out.write("%s" % f)
   #      for c in xrange(self.nclasses):
   #         p = self.W[f]
   #         out.write(" %s" % p.w_for_clas(c))
   #      out.write("\n")

   def dump(self, out=sys.stdout, sparse=False):
      cdef SparseMulticlassParamData p
      if sparse:
         out.write("%s\n" % self.nclasses)
      for f in self.W.keys():
         out.write("%s" % f)
         for c in xrange(self.nclasses):
            p = self.W[f]
            w = p.w_for_clas(c)
            if sparse:
               if w != 0:
                  out.write(" %s:%s" % (c,w))
            else:
               out.write(" %s" % w)
         out.write("\n")

   def dump_fin(self,out=sys.stdout, sparse=False):
      cdef SparseMulticlassParamData p
      # write the average
      if sparse:
         out.write("%s\n" % self.nclasses)
      for f in self.W.keys():
         out.write("%s" % f)
         for c in xrange(self.nclasses):
            p = self.W[f]
            w = p.avgd_w_for_clas(c, self.now)
            if sparse:
               if w != 0:
                  out.write(" %s:%s" % (c,w))
            else:
               out.write(" %s " % (w))
         out.write("\n")

### These are used only for prediction.

cdef class SparseWeightsArr:
   cdef double *vals
   cdef short *class_deltas
   cdef public int n
   def __cinit__(self, list classes, list weights):
      cdef int i
      assert(len(classes) == len(weights))
      self.n = len(classes)
      if self.n == 0: return
      self.vals=<double *>malloc(sizeof(double)*self.n)
      self.class_deltas=<short *>malloc(sizeof(short)*self.n)
      cdef int current_class = 0
      for i in xrange(self.n):
         n = float(weights[i])
         self.vals[i] = n
         self.class_deltas[i] = classes[i] - current_class
         current_class = classes[i]
   def __dealloc__(self):
      if self.n == 0: return
      free(self.vals)
      free(self.class_deltas)

   cdef double weight_for_class(self, c):
      cdef current_class = 0
      for i in xrange(self.n):
         current_class += self.class_deltas[i]
         if current_class == c: return self.vals[i]
         if current_class > c: return 0
      return 0

   cdef void add_to_dense_scores(self, double *scores):
      cdef current_class = 0
      for i in xrange(self.n):
         current_class += self.class_deltas[i]
         scores[current_class] += self.vals[i]

cdef class SparseMulticlassModel:
   cdef:
      SparseWeightsArr biases
      int nclasses
      dict W
      double* scores # (re)used in calculating prediction

   cdef load_from_dense(self,fname):
      return self.from_dense_file_handle(file(fname))

   cdef from_dense_file_handle(self,fh):
      for line in fh:
         f,ws = line.strip().split(None,1)
         weights = [float(w) for w in ws.split()]
         classes = range(len(weights))
         self.nclasses = len(classes)
         self.W[f]=SparseWeightsArr(classes, weights)
      try:
         self.biases = self.W['**BIAS**']
      except KeyError:
         self.biases = SparseWeightsArr([],[])
         for i in xrange(self.biases.n):
            self.biases.vals[i]=0

      self.scores=<double *>malloc(sizeof(double)*self.nclasses)

   cdef from_sparse_file_handle(self,fh):
      self.nclasses = int(fh.next())
      for line in fh:
         try:
            f,ws = line.strip().split(None,1)
         except ValueError:
            #print >> sys.stderr,"skip empty line",line
            continue
         c_ws = [cw.split(":") for cw in ws.split()]
         weights = [float(w) for c,w in c_ws]
         classes = [int(c) for c,w in c_ws]
         self.W[f]=SparseWeightsArr(classes, weights)
      try:
         self.biases = self.W['**BIAS**']
      except KeyError:
         self.biases = SparseWeightsArr([],[])
         for i in xrange(self.biases.n):
            self.biases.vals[i]=0
      self.scores=<double *>malloc(sizeof(double)*self.nclasses)

   cdef load_from_sparse(self,fname):
      sys.stderr.write("loading sparse model %s" % fname)
      fh = file(fname)
      return self.from_sparse_file_handle(fh)


   def __init__(self, fh, sparse=True):
      self.W = {}
      if sparse:
         self.from_sparse_file_handle(fh)
      else:
         self.from_dense_file_handle(fh)
      sys.stderr.write(" done\n")

   def __dealloc__(self):
      free(self.scores)

   cpdef object predict(self,list features):
      cdef int i
      cdef double w
      cdef SparseWeightsArr ws
      for i in xrange(self.nclasses):
         self.scores[i] = 0
      self.biases.add_to_dense_scores(self.scores)
      for f in features:
         try:
            ws = self.W[f]
            ws.add_to_dense_scores(self.scores)
         except KeyError: pass
      #cdef double tot = 0
      #if self.probs_output:
      #   for i in xrange(self.nclas): 
      #      self.scores[i]=math.exp(self.scores[i])
      #      tot+=self.scores[i]
      res=[]
      cdef int besti=0
      cdef double best=0
      for i in xrange(self.nclasses):
         if self.scores[i] > best:
            best = self.scores[i]
            besti = i
         #if self.probs_output:
         #   res.append(self.scores[i]/tot)
         #else:
         res.append(self.scores[i])
      return besti,res

   cpdef object get_scores(self,list features):
      cdef int i
      cdef SparseWeightsArr ws
      for i in xrange(self.nclasses):
         self.scores[i] = 0
      self.biases.add_to_dense_scores(self.scores)
      for f in features:
         try:
            ws = self.W[f]
            ws.add_to_dense_scores(self.scores)
         except KeyError: pass
      res=[]
      for i in xrange(self.nclasses):
         res.append(self.scores[i])
      return res

   cpdef object get_best_class(self,list features):
      cdef int i
      cdef SparseWeightsArr ws
      cdef int best_i
      cdef double max_score
      for i in xrange(self.nclasses):
         self.scores[i] = 0
      self.biases.add_to_dense_scores(self.scores)
      for f in features:
         try:
            ws = self.W[f]
            ws.add_to_dense_scores(self.scores)
         except KeyError: pass
      max_score = self.scores[0]
      best_i = 0
      for i in xrange(self.nclasses):
         if max_score < self.scores[i]:
            max_score = self.scores[i]
            best_i = i
      return max_score,best_i

   cpdef object get_best_class_with_initial_scores(self,list features, list scores):
      cdef int i
      cdef SparseWeightsArr ws
      cdef int best_i
      cdef double max_score
      for i in xrange(self.nclasses):
         self.scores[i] = scores[i]
      self.biases.add_to_dense_scores(self.scores)
      for f in features:
         try:
            ws = self.W[f]
            ws.add_to_dense_scores(self.scores)
         except KeyError: pass
      max_score = self.scores[0]
      best_i = 0
      for i in xrange(self.nclasses):
         if max_score < self.scores[i]:
            max_score = self.scores[i]
            best_i = i
      return max_score,best_i

