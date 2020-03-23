#!/usr/bin/env python

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

import math
import random
import sys
import os.path
import cPickle as pickle
from collections import defaultdict
from itertools import izip,islice
from tqdm import tqdm
from deps import DependenciesCollection
from ml.ml import MulticlassModel, MultitronParameters 
from pio import io
import isprojective 
from common import PAD,ROOT
from moduleloader import load_module
import kskutil
from pattern.en import singularize, pluralize, lemma, conjugate
import kenlm

### specify your kenlm model
#lmmodel = kenlm.Model("path_to_kenlm_model")
lmmodel = kenlm.Model("../data/gigaword.kenlm")

TARGET_PREP = ["on", "about", "from", "for", "of", "to", "at", "in", "with", "by"]
TARGET_VFORM = ["VB", "VBP", "VBZ", "VBG", "VBD", "VBN"]
TENSE_ASPECTS = ['inf', '1sg', '3sg', 'part', 'p', 'ppart']
PREV_PREP_TAGS = ["NN", "NNS", "DT", "CD", "JJ", "JJR", "JJS", "NNP", "NNPS"]
DETS = ['a', 'an', 'the']

DEBUG = False
DEBUG_TRAIN = False

class Oracle: #{{{
   def __init__(self):
      self.sent = None
      self.childs = defaultdict(set)

   def allow_connection(self, sent, deps, parent, child, label=None):
      if self.sent != sent:
         self.sent = sent
         self.childs = defaultdict(set)
         for tok in sent:
            self.childs[tok['parent']].add((tok['parent'],tok['id']))

      if child['parent'] != parent['id']: 
         return False
      # if child didn't collect all it's childs, it can't connect.
      if len(self.childs[child['id']] - deps.deps) > 0:
         return False
      if label and child['prel'] != label: return False
      return True
   #}}}

class CostOracle: #{{{
   def __init__(self):
      self.sent = None
      self.childs = defaultdict(set)

   def action_cost(self, roots, parent, child, action_type, orig_tokens, gold_tokens, label=None): # roots = parsed in train
      #  after connecting child to parent:
      #  children of child on the roots list will not be able to get their correct head.
      #  child will not be able to acquire a new head on the roots list.
      cost = 0.0
      edited_tokens = orig_tokens[:]
      if action_type == "attach":
          for tok in roots: # id = token index, parent = parent index (both are int!)
             if tok['parent'] == child['id']: 
                cost += 1 # the child never becomes a parent of other tokens
             if child['parent'] == tok['id'] and tok['id'] != parent['id']:
                cost += 1 # the child has only one parent and if it is different, add cost

          if len(roots) > 2:
              if parent['form'] == "_ROOT_" or child['form'] == "_ROOT_":
                  cost += 1

          return cost

      elif action_type == "substituteDet":
          ed_before = kskutil.getEditDist(orig_tokens, gold_tokens)[0]
          assert parent['form'] in DETS
          assert parent['morph'] != 1
          assert parent['tag'] == "DT"
          candidates = ['a', 'the','an']
          w_insert = candidates[0]
          best_score = float('-inf')
          for cand in candidates:
              edited_tokens = orig_tokens[:]
              edited_tokens[parent['id']] = cand
              tmp_sent = " ".join(edited_tokens)
              tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
              if best_score < tmp_score:
                  best_score = tmp_score
                  w_insert = cand
          edited_tokens = orig_tokens[:]
          edited_tokens[parent['id']] = w_insert
          ed_after = kskutil.getEditDist(edited_tokens, gold_tokens)[0]
          if ed_before <= ed_after:
              cost += 1
          return cost

      elif action_type == "substituteNN":
          ed_before = kskutil.getEditDist(orig_tokens, gold_tokens)[0]
          # NOTE parent is tok2, child is tok1
          # change parent(tok2) depending on part of speech
          assert parent['tag'] in ('NN', 'NNS')
          assert parent['morph'] != 1

          if parent['tag'] == "NN":
              edited_tokens[parent['id']] = pluralize(parent['form'])
          elif parent['tag'] == "NNS":
              edited_tokens[parent['id']] = singularize(parent['form'])
          else: 
              raise

          ed_after = kskutil.getEditDist(edited_tokens, gold_tokens)[0]
          if ed_before < ed_after:
              cost += 1
          return cost

      # delete action
      elif action_type.startswith("delete"):
          assert parent['morph'] != 1
          ed_before = kskutil.getEditDist(orig_tokens, gold_tokens)[0]
          edited_tokens.pop(parent['id'])
          ed_after = kskutil.getEditDist(edited_tokens, gold_tokens)[0]
          if ed_before <= ed_after:
              cost += 1
          return cost

      elif action_type.startswith("insert"):
          ed_before = kskutil.getEditDist(orig_tokens, gold_tokens)[0]
          w_insert = ""

          if parent['lem'] != "I-NP":
              cost += 1
              return cost

          if action_type.startswith("insertDet"):
              candidates = DETS
              w_insert = candidates[0]
              best_score = float('-inf')
              for cand in candidates:
                  edited_tokens = orig_tokens[:]
                  edited_tokens.insert(parent['id'], cand)
                  tmp_sent = " ".join(edited_tokens)
                  tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                  if best_score < tmp_score:
                      best_score = tmp_score
                      w_insert = cand

          elif action_type.startswith("insertPrep"):
              candidates = TARGET_PREP
              w_insert = candidates[0]
              best_score = float('-inf')
              for cand in candidates:
                  edited_tokens = orig_tokens[:]
                  edited_tokens.insert(parent['id'], cand)
                  tmp_sent = " ".join(edited_tokens)
                  tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                  if best_score < tmp_score:
                      best_score = tmp_score
                      w_insert = cand

          assert w_insert != ""

          edited_tokens = orig_tokens[:]
          edited_tokens.insert(parent['id'], w_insert)

          ed_after = kskutil.getEditDist(edited_tokens, gold_tokens)[0]
          if ed_before <= ed_after:
              cost += 1
          return cost


      elif action_type.startswith("substituteVform"):
          ed_before = kskutil.getEditDist(orig_tokens, gold_tokens)[0]

          assert parent['tag'].startswith("VB")
          assert parent['morph'] != 1
    
          candidates = []
          for ta in TENSE_ASPECTS:
              candidates.append(str(conjugate(lemma(parent['form']), ta)))

          w_insert = candidates[0]
          best_score = float('-inf')
          for cand in candidates:
              edited_tokens = orig_tokens[:]
              edited_tokens[parent['id']] = cand
              tmp_sent = " ".join(edited_tokens)
              tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
              if best_score < tmp_score:
                  best_score = tmp_score
                  w_insert = cand

          edited_tokens = orig_tokens[:]
          edited_tokens[parent['id']] = w_insert
          ed_after = kskutil.getEditDist(edited_tokens, gold_tokens)[0]
          if ed_before < ed_after:
              cost += 1
          return cost

      elif action_type.startswith("substitutePrep"):
          assert parent['tag'].startswith("IN")
          assert parent['morph'] != 1

          ed_before = kskutil.getEditDist(orig_tokens, gold_tokens)[0]
          candidates = TARGET_PREP
          w_insert = candidates[0]
          best_score = float('-inf')
          for cand in candidates:
              edited_tokens = orig_tokens[:]
              edited_tokens[parent['id']] = cand
              tmp_sent = " ".join(edited_tokens)
              tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
              if best_score < tmp_score:
                  best_score = tmp_score
                  w_insert = cand
          edited_tokens = orig_tokens[:]
          edited_tokens[parent['id']] = w_insert
          ed_after = kskutil.getEditDist(edited_tokens, gold_tokens)[0]
          if ed_before < ed_after:
              cost += 1
          return cost
      
      else:
          raise
   #}}}

class Parser: #{{{
   def __init__(self, attachonly, scorer, featExt, oracle=None):
      self.scorer=scorer
      self.featExt=featExt
      self.oracle=oracle
      self.attachonly=attachonly

   def vis_parse(self, sent): #{{{
      deps = DependenciesCollection()
      parsed = sent[:]
      parsed=[ROOT]+parsed
      sent = [ROOT]+sent
      connections = 0
      mistake=False
      for tok in parsed: tok['s']=tok['form']
      fcache={}
      scache={}
      while len(parsed)>1:
         # find best action
         best = -9999999
         best_pair = None 
         scores = {}
         for i,(tok1,tok2) in enumerate(zip(parsed,parsed[1:])):
            tid=tok1['id']
            if tid in fcache:
               feats = fcache[tid]
            else:
               feats = self.featExt.extract(parsed,deps,i,sent)
               fcache[tid] = feats
            if tid in scache:
               s1,s2 = scache[tid]
            else:
               scr = self.scorer.get_scores(feats)
               s1 = scr[0]
               s2 = scr[1]
               scache[tid]=s1,s2
            if s1 > best:
               best = s1
               best_pair = (tok1,tok2)
            if s2 > best:
               best = s2
               best_pair = (tok2,tok1)
            scores[(i,i+1)]=s1
            scores[(i+1,i)]=s2
            
         c,p = best_pair
         # remove the neighbours of parent from the cache
         i = parsed.index(p)
         frm=i-4
         to=i+4
         if frm<0: frm = 0
         if to>=len(parsed):to=len(parsed)-1
         for tok in parsed[frm:to]:
            try:
               del fcache[tok['id']]
               del scache[tok['id']]
            except: pass
         yield (self.oracle,sent, parsed, deps, scores)
         deps.add(p,c)
         connections += 1
         parsed = [x for x in parsed if x!=c]
      yield (self.oracle,sent, parsed, deps, scores)
   #}}}

   def parse(self, sent): #{{{
      oracle=CostOracle()
      deps = DependenciesCollection()

      sent = [ROOT]+sent
      parsed = sent[:]
      scache={}
      fe=self.featExt.extract
      gscore=self.scorer.get_scores
      MAXEDITS = len(parsed)
      num_edits = 0
      while len(parsed)>1:
         # find best action
         _pairs=[]
         for i,(tok1,tok2) in enumerate(izip(parsed,islice(parsed,1,None))): 
            tid=tok1['id']
            scache_list = []

            if tid in scache:
               scache_list = scache[tid]
            else:
               feats = fe(parsed,deps,i,sent)
               scr = gscore(feats)
                
               for j, score_j in enumerate(scr):
                   scache_list.append(scr[j])
               scache[tid] = scache_list

            # add attach actions (when allowed)
            if len(parsed)>2 and tok1['form'] == "_ROOT_":
                pass
            elif len(parsed)==2 and tok1['form'] == "_ROOT_":
                _pairs.append((scache_list[1],1,tok2,tok1,i))
            else:
                _pairs.append((scache_list[0],0,tok1,tok2,i+1))
                _pairs.append((scache_list[1],1,tok2,tok1,i))

            # new actions
            if num_edits<=MAXEDITS and len(parsed) > 2:
                # add NN substitution hypothesis
                if tok2['tag'] in ('NN', 'NNS') and tok2['morph'] != 1:
                    _pairs.append((scache_list[2],2,tok1,tok2,i+1))

                # DT deletion hypothesis 
                if tok2['form'] in DETS and tok2['morph'] != 1 and len(deps._childs[tok2['id']])==0:
                        _pairs.append((scache_list[3],3,tok1,tok2,i+1))

                # insert DT hypothesis
                if tok2['tag'] in ('NN', 'NNS', 'JJ', 'JJR', 'JJS') and (not tok2['form'][0].isupper() and (tok1['tag']!='DT')):
                    _pairs.append((scache_list[4],4,tok1,tok2,i+1))

                # Vform substitution hypothesis:
                if tok2['tag'].startswith("VB") and tok2['morph'] != 1:
                    _pairs.append((scache_list[5],5,tok1,tok2,i+1)) # substitute to VB

                # Prep substitution and deletion hypothesis:
                if tok2['tag'] == "IN" and tok2['form'] in TARGET_PREP and tok2['morph'] != 1:
                    _pairs.append((scache_list[6],6,tok1,tok2,i+1))
                    if len(deps._childs[tok2['id']])==0: # we don't want to delete prep which already has a child.
                        _pairs.append((scache_list[7],7,tok1,tok2,i+1))

                # Prep insertion hypothesis:
                if tok2['tag'] in PREV_PREP_TAGS and tok1['tag'] != "IN":
                    _pairs.append((scache_list[8],8,tok1,tok2,i+1))

                if tok2['form'] in DETS and tok2['tag'] == "DT" and tok2['id'] < len(sent) and tok2['morph'] != 1 and len(deps._childs[tok2['id']])==0:
                    _pairs.append((scache_list[9],9,tok1,tok2,i+1))


         assert len(_pairs) > 0
         best,cls,c,p,locidx = max(_pairs)
         action_type = getActiontype(cls)

         cost = 0
         i = locidx # index in parsed (not token id)
         j = ""
         for j_tmp, t_id in enumerate(sent):
             if t_id['id'] == p['id']:
                 j = j_tmp

         scache = {}
         
         if action_type == "attach":
             deps.add(p,c)
             parsed.remove(c)

         elif action_type == "substituteDet":
             assert parsed[i]['tag'] == "DT"
             assert parsed[i]['form'] == sent[j]['form']
             assert parsed[i]['form'] in ('a', 'an', 'the')

             if DEBUG:
                 print "substituteDet"
                 print parsed
                 print "target is ", parsed[i]
 
             candidates = ['a', 'the', 'an']
             best_score = float('-inf')
             best_cand = candidates[0]
             for cand in candidates:
                 tmp_token = sent[:]
                 tmp_token[j]['form'] = cand
                 tmp_sent = " ".join([tt['form'] for tt in tmp_token])
                 tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                 if best_score < tmp_score:
                     best_score = tmp_score
                     best_cand = cand
             sent[j]['form'] = cand
             parsed[i]['form'] = cand
             sent[j]['morph'] = 1
             parsed[i]['morph'] = 1

             num_edits += 1

             if DEBUG:
                 print "substituted parse"
                 print parsed

         elif action_type == "substituteNN":
             assert parsed[i]['tag'] in ("NN", "NNS")
             assert parsed[i]['form'] == sent[j]['form']
             if DEBUG:
                 print "substituteNN"
                 print parsed
                 print "target is ", parsed[i]
             if parsed[i]['tag'] == "NN":
                 parsed[i]['form'] = pluralize(parsed[i]['form'])
                 parsed[i]['tag'] = "NNS"
                 sent[j]['form'] = pluralize(sent[j]['form'])
                 sent[j]['tag'] = "NNS"


             elif parsed[i]['tag'] == "NNS":
                 parsed[i]['form'] = singularize(parsed[i]['form'])
                 parsed[i]['tag'] = "NN"
                 sent[j]['form'] = singularize(sent[j]['form'])
                 sent[j]['tag'] = "NN"

             else:
                 print parsed[i]['tag'] + ": something wrong"
                 raise
             if DEBUG:
                 print "substituted parse"
                 print parsed

             parsed[i]['morph'] = 1
             sent[j]['morph'] = 1
             num_edits += 1

         elif action_type.startswith("delete"):
             assert p['id'] == parsed[i]['id']
             delidx = parsed[i]['id']

             if DEBUG:
                 print "+++++ decrement dep +++++" , str(delidx)
                 print deps.deps

             deps.decrement(delidx)

             if DEBUG:
                print deps.deps

             if DEBUG:
                 print "##### delete parsed token #####" , str(delidx)
                 print parsed

             del parsed[i]
             if DEBUG:
                 print parsed

             if DEBUG:
                 print "##### delete sent token #####" , str(delidx)
                 print sent

             sent = [s_token for s_token in sent if s_token['id'] != delidx]
             if DEBUG:
                 print sent

             num_edits += 1

             new_parsed = []
             for p_token in parsed:
                 p_token = kskutil.decrementToken(p_token, delidx)
                 new_parsed.append(p_token)
             parsed = new_parsed

             new_sent = []
             for s_token in sent:
                 s_token = kskutil.decrementToken(s_token, delidx)
                 new_sent.append(s_token)
             sent = new_sent
                 
         elif action_type.startswith("insert"):
             if DEBUG:
                 print "insert"
             
             assert p['id'] == parsed[i]['id']
             insidx = p['id']

             left_most_id = insidx
             left_most_char = p['form'][0]
             for child_i in deps._childs[i]:
                 if left_most_id > child_i['id']:
                     left_most_id = child_i['id']
                     left_most_char = child_i['form'][0]

             # 1. increment deps
             if DEBUG:
                 print "+++++ increment dep +++++" , str(insidx)
                 print deps.deps
             deps.increment(insidx)
             if DEBUG:
                 print deps.deps

             # 2. increment parsed  (N.B. reversed order)
             if DEBUG:
                 print "##### increment parsed #####"
                 print parsed
             new_parsed = []
             for p_token in parsed:
                 p_token = kskutil.incrementToken(p_token, insidx)
                 new_parsed.append(p_token)
             parsed = new_parsed
             if DEBUG:
                 print parsed

             if DEBUG:
                 print "##### increment sent #####"
                 print sent
             new_sent = []
             for s_token in sent:
                 s_token = kskutil.incrementToken(s_token, insidx)
                 new_sent.append(s_token)
             sent = new_sent
             if DEBUG:
                 print sent

             # 3. create token for insertion (with morph=1!)
             token_i = ""
             if action_type.startswith("insertDet"):
                 candidates = DETS
                 best_cand = candidates[0]
                 best_score = float('-inf')
                 for cand in candidates:
                     tmp_sent_tokens = sent[:]
                     tmp_tokens = [tt['form'] for tt in tmp_sent_tokens]
                     tmp_tokens.insert(j, cand)
                     tmp_sent = " ".join(tmp_tokens)
                     tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                     if best_score < tmp_score:
                         best_score = tmp_score
                         best_cand = cand

                 token_i = kskutil.tokenTemplate(insidx, best_cand, 'DT')

             elif action_type.startswith("insertPrep"):
                 candidates = TARGET_PREP
                 best_cand = candidates[0]
                 best_score = float('-inf')
                 for cand in candidates:
                     tmp_sent_tokens = sent[:]
                     tmp_tokens = [tt['form'] for tt in tmp_sent_tokens]
                     tmp_tokens.insert(j, cand)
                     tmp_sent = " ".join(tmp_tokens)
                     tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                     if best_score < tmp_score:
                         best_score = tmp_score
                         best_cand = cand
                 token_i = kskutil.tokenTemplate(insidx, best_cand, 'IN')

             else:
                 raise
             if DEBUG:
                 print "----- new token -----"
                 print token_i

             # 4. insert the token to parsed
             if DEBUG:
                 print "***** insert check *****"
                 print "parsed: ", parsed
                 print "sent: ", sent
             parsed.insert(i, token_i)
             sent.insert(j, token_i)
             if DEBUG:
                 print "***** insert check *****"
                 print "parsed: ", parsed
                 print "sent: ", sent

             # 5. numedits++
             num_edits += 1

         elif action_type.startswith("substituteVform"):
             
             assert parsed[i]['tag'].startswith("VB")
             assert parsed[i]['form'] == sent[j]['form']

             if DEBUG:
                 print "+++++ substitute Vform +++++" , parsed[i]['id']
                 print parsed
                 print sent

             # TARGET_VFORM, and TENSE_ASPECTS are the candidates
             best_score = float('-inf')
             best_cand = str(parsed[i]['form'])
             best_tag = str(parsed[i]['tag'])
             for t_vtag, t_tense in zip(TARGET_VFORM, TENSE_ASPECTS):
                 tmp_tokens = sent[:]
                 cand = str(conjugate(lemma(parsed[i]['form']), t_tense))
                 tmp_tokens[j]['form'] = cand
                 tmp_sent = " ".join([tt['form'] for tt in tmp_tokens])
                 tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                 if best_score < tmp_score:
                     best_score = tmp_score
                     best_cand = cand
                     best_tag = t_vtag
             
             sent[j]['form'] = best_cand
             parsed[i]['form'] = best_cand
             sent[j]['tag'] = best_tag
             parsed[i]['tag'] = best_tag
             sent[j]['morph'] = 1
             parsed[i]['morph'] = 1

             # 5. numedits++
             num_edits += 1

         elif action_type.startswith("substitutePrep"):
             if DEBUG:
                 print "substitutePrep"

             assert parsed[i]['tag'].startswith("IN")
             assert parsed[i]['form'] == sent[j]['form']

             if DEBUG:
                 print "+++++ substitute Prep +++++" , parsed[i]['id']
                 print parsed
                 print sentj

             candidates = TARGET_PREP
             best_cand = candidates[0]
             best_score = float('-inf')
             for cand in candidates:
                 tmp_sent_tokens = sent[:]
                 tmp_sent_tokens[j]['form'] = cand
                 tmp_sent = " ".join([tt['form'] for tt in tmp_sent_tokens])
                 tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                 if best_score < tmp_score:
                     best_score = tmp_score
                     best_cand = cand
             sent[j]['form'] = cand
             parsed[i]['form'] = cand
             parsed[i]['morph'] = 1
             sent[j]['morph'] = 1

             if DEBUG:
                 print "***** substitute substitutePrep check *****"
                 print "parsed: ", parsed
                 print "sent: ", sent
 
             num_edits += 1


         else: # sanity check of action type
             print 
             print action_type
             raise

      if DEBUG:
          print "===final deps (dev)==="
          print sorted([t[1] for t in deps.deps])
      assert sorted([t[1] for t in deps.deps])[-1] == len(deps.deps)

      return deps, sent[1:]

   #}}}

#   def parse_labeled(self, sent): #{{{
#      id_to_action_mapper = self.id_to_action_mapper
#      deps = DependenciesCollection()
#      parsed = sent[:]
#      parsed=[ROOT]+parsed
#      sent = [ROOT]+sent
#      scache={}
#      fe=self.featExt.extract
#      gscore=self.scorer.get_scores
#      lp = len(parsed) 
#      while lp>1:
#         # find best action
#         _pairs=[]
#         for i,(tok1,tok2) in enumerate(izip(parsed,islice(parsed,1,None))): 
#            tid=tok1['id']
#            if tid in scache:
#               (max_score_0,max_score_1,max_lbl_0,max_lbl_1) = scache[tid]
#            else:
#               feats = fe(parsed,deps,i,sent)
#               scr = gscore(feats)
#               scache[tid]=scr # TODO: should I copy with dict() or is it safe?
#               scored = [(score,id_to_action_mapper[aid]) for (aid,score) in enumerate(scr)]
#               s0 = [(s,lbl) for (s,(dr,lbl)) in scored if dr == 0]
#               s1 = [(s,lbl) for (s,(dr,lbl)) in scored if dr == 1]
#               max_score_0,max_lbl_0 = max(s0)
#               max_score_1,max_lbl_1 = max(s1)
#               scache[tid] = (max_score_0,max_score_1,max_lbl_0,max_lbl_1)
#            _pairs.append((max_score_0,tok1,tok2,max_lbl_0,i+1))
#            _pairs.append((max_score_1,tok2,tok1,max_lbl_1,i))
#
#         best,c,p,lbl,locidx = max(_pairs)
#         # remove the neighbours of parent from the cache
#         i = locidx
#         frm=i-4
#         to=i+4
#         if frm<0: frm = 0
#         if to>=lp:to=lp-1
#         for tok in parsed[frm:to]: 
#            try:
#               del scache[tok['id']]
#            except: pass
#         # apply action
#         deps.add(p,c,lbl)
#         parsed.remove(c)
#         lp-=1
#      return deps
#
#   #}}}

   def parse_with_span_constraints(self, sent, spans): #{{{
      """
      spans is a list of the tuples of the form (s,e)
      where s and e are integers, where s is the index of the first token in the span, and e is
      the index of the last token in the span.

      spans may not overlap or contain each other (this is not verified).

      The constraint is that all tokens in each span must share a head, and only that head may have
      children outside of the span.
      """
      deps = DependenciesCollection()
      parsed = sent[:]
      parsed=[ROOT]+parsed
      sent = [ROOT]+sent
      remaining_toks_in_span = {-1:0}
      for sid,(s,e) in enumerate(spans):
         if e >= len(sent): continue
         remaining_toks_in_span[sid] = (e-s)
         for tok in sent[s:e+1]:
            tok['span_id'] = sid
      scache={}
      fe=self.featExt.extract
      gscore=self.scorer.get_scores
      lp = len(parsed) 
      while lp>1:
         # find best action
         _pairs=[]
         for i,(tok1,tok2) in enumerate(izip(parsed,islice(parsed,1,None))): 
            # if tok1,tok2 not allowed by the span constraints, skip.
            # in order to be allowed, we need either:
            #  tok1 and tok2 inside the same span.
            #  tok1 and tok2 not inside any span.
            #  a single token in a span is not considered to be inside a span.
            sid1 = tok1.get('span_id',-1)
            sid2 = tok2.get('span_id',-1)
            if sid1 != sid2:
               if remaining_toks_in_span[sid1] > 0 or remaining_toks_in_span[sid2] > 0:
                  continue
            tid=tok1['id']
            if tid in scache:
               s1,s2 = scache[tid]
            else:
               feats = fe(parsed,deps,i,sent)
               scr = gscore(feats)
               s1 = scr[0]
               s2 = scr[1]
               scache[tid]=s1,s2

            _pairs.append((s1,tok1,tok2,i+1))
            _pairs.append((s2,tok2,tok1,i))
            
         best,c,p,locidx = max(_pairs)
         # remove the neighbours of parent from the cache
         i = locidx
         frm=i-4
         to=i+4
         if frm<0: frm = 0
         if to>=lp:to=lp-1
         for tok in parsed[frm:to]: 
            try:
               del scache[tok['id']]
            except: pass
         # apply action
         deps.add(p,c)
         parsed.remove(c)
         remaining_toks_in_span[c.get('span_id',-1)]-=1
         lp-=1
      return deps

   #}}}

   def parse2(self, sent): #{{{
      deps = DependenciesCollection()
      parsed = sent[:]
      parsed=[ROOT]+parsed
      sent = [ROOT]+sent
      scache={}
      fe=self.featExt.extract
      gscore=self.scorer.get_scores
      lp = len(parsed) 
      anum=0
      order=[]
      while lp>1:
         anum+=1
         # find best action
         _pairs=[]
         for i,(tok1,tok2) in enumerate(izip(parsed,islice(parsed,1,None))): 
            tid=tok1['id']
            if tid in scache:
               s1,s2 = scache[tid]
            else:
               feats = fe(parsed,deps,i,sent)
               scr = gscore(feats)
               s1 = scr[0]
               s2 = scr[1]
               scache[tid]=s1,s2

            _pairs.append((s1,tok1,tok2,i+1))
            _pairs.append((s2,tok2,tok1,i))
            
         best,c,p,locidx = max(_pairs)
         # remove the neighbours of parent from the cache
         i = locidx
         frm=i-4
         to=i+4
         if frm<0: frm = 0
         if to>=lp:to=lp-1
         for tok in parsed[frm:to]: 
            try:
               del scache[tok['id']]
            except: pass
         # apply action
         deps.add(p,c)
         order.append((p['id'],c['id'],anum))
         parsed.remove(c)
         lp-=1
      return deps, order

   #}}}

   def train(self, sent, gold_sent, iter_number, explore_policy=None): #{{{
      updates=0

      sent = [ROOT]+sent
      gold_sent = [ROOT]+gold_sent
      orig_tokens = [tok['form'] for tok in sent]
      gold_tokens = [tok['form'] for tok in gold_sent]

      self.scorer.tick()
      deps = DependenciesCollection()
      parsed = sent[:] # copying the sent list (avoid call by reference)
      fcache = {} # feature cache
      scache = {} # score cache

      num_edits = 0
      num_tokens = len(parsed)
      while len(parsed)>1: #{{{
         curr_tokens = [tok['form'] for tok in sent]
         scored = []
         for i,(tok1,tok2) in enumerate(zip(parsed,parsed[1:])):
            scache_list = []
            tid = tok1['id']
            if tid in fcache: # if in cache, reuse it.
               feats = fcache[tid]
            else:
               feats = self.featExt.extract(parsed,deps,i,sent)
               fcache[tid]=feats

            if tid in scache: # if in score cache, reuse it.
               scache_list = scache[tid]
            else:
               scores = self.scorer.get_scores(feats)
               for i, score_i in enumerate(scores):
                   scache_list.append(scores[i])
               scache[tid] = scache_list
        
            # additional huristics1 that prevent attach the root until the end
            if len(parsed) > 2 and tok1['form'] == "_ROOT_": 
                pass
            # additional huristics2 that force to do right attach to ROOT at the end 
            elif len(parsed) == 2 and tok1['form'] == "_ROOT_":
                scored.append((scache_list[1],1,feats,tok2,tok1)) #tok2 is child of tok1 (parent) = right attach
            else:
                scored.append((scache_list[0],0,feats,tok1,tok2)) #tok1 is child of tok2 (parent) = left attach
                scored.append((scache_list[1],1,feats,tok2,tok1)) #tok2 is child of tok1 (parent) = right attach

            # new actions
            if num_edits <= num_tokens and len(parsed) > 2:
                # NN substitution hypothesis
                if tok2['tag'] in ('NN', 'NNS') and tok2['morph'] != 1:
                    scored.append((scache_list[2],2,feats,tok1,tok2)) 

                # DT deletion hypothesis
                if tok2['form'] in DETS and tok2['morph'] != 1 and len(deps._childs[tok2['id']])==0:
                    scored.append((scache_list[3],3,feats,tok1,tok2))

                # DT insertion hypothesis
                if tok2['tag'] in ("NN", "NNS", "JJ", "JJR", "JJS") and (not tok2['form'][0].isupper() and (tok1['tag'] != 'DT')):
                    #scored.append((s5,4,feats,tok1,tok2)) #insert definite article 
                    scored.append((scache_list[4],4,feats,tok1,tok2)) #insert definite article 

                # Vform substitution hypothesis:
                if tok2['tag'].startswith("VB") and tok2['morph'] != 1:
                    scored.append((scache_list[5],5,feats,tok1,tok2)) # substitute to VB

                # Prep substitution and deletion hypothesis:
                if tok2['tag'] == "IN" and tok2['form'] in TARGET_PREP and tok2['morph'] != 1:
                    scored.append((scache_list[6],6,feats,tok1,tok2))

                    # Prep deletion hypothesis 
                    if len(deps._childs[tok2['id']])==0: # we don't want to delete prep which already has a child.
                        scored.append((scache_list[7],7,feats,tok1,tok2))
                    
                # Prep insertion hypothesis
                if tok2['tag'] in PREV_PREP_TAGS and tok1['tag']!="IN":
                    scored.append((scache_list[8],8,feats,tok1,tok2))

                # substitute DT
                if tok2['form'] in DETS and tok2['tag'] =="DT" and tok2['id'] < len(sent) and tok2['morph'] != 1 and len(deps._childs[tok2['id']])==0:
                    scored.append((scache_list[9],9,feats,tok1,tok2))
                 
         assert len(scored) > 0
         scored=sorted(scored,key=lambda (s,cls,f,t1,t2):-s)
         s,cls,f,c,p = scored[0]

         # debug
         if DEBUG_TRAIN:
             print "+++++ parsed detail +++++"
             print cls, [z[1] for z in scored]
             print "parent ", p
             print "child  ", c
             print [z['form'] for z in parsed]
             print [z['id'] for z in parsed]
             print [z['parent'] for z in parsed]

         action_type = getActiontype(cls)
         cost = self.oracle.action_cost(parsed,p,c,action_type,curr_tokens, gold_tokens)
         self.cumcost += cost
         if cost == 0:
            correct = True
         else:
            correct = False
            scache = {} # clear the cache -- numbers changed.
            # find best allowable pair
            best_action = []

            # learn non-attach actions with priority
            nonattach = False
            for s,gcls,gf,gc,gp in scored[1:]:
                g_action_type = getActiontype(gcls)
                if gcls >= 2 and self.oracle.action_cost(parsed,gp,gc, g_action_type, curr_tokens, gold_tokens) == 0:
                    nonattach = True
                    break

            if nonattach:
                for s,gcls,gf,gc,gp in scored[1:]:
                    g_action_type = getActiontype(gcls)
                    if gcls >= 2 and self.oracle.action_cost(parsed,gp,gc, g_action_type, curr_tokens, gold_tokens) == 0:
                        self.scorer.add(gf,gcls,1)
                        break
            else:
                for s,gcls,gf,gc,gp in scored[1:]:
                    g_action_type = getActiontype(gcls)
                    if self.oracle.action_cost(parsed,gp,gc, g_action_type, curr_tokens, gold_tokens) == 0:
                        self.scorer.add(gf,gcls,1)
                        break

            self.scorer.add(f,cls,-1)
            updates+=1

            if updates>200:
               print "STUCK, probably because of incomplete feature set"
               print " ".join([x['form'] for x in sent])
               print " ".join([x['form'] for x in parsed])
               return

         if correct or (explore_policy and explore_policy.should_explore(iter_number)):
            # remove the neighbours of parent from the cache
            i = parsed.index(p)

            j = ""
            for j_tmp, t_id in enumerate(sent):
                if t_id['id'] == p['id']:
                    j = j_tmp

            fcache = {}
            scache = {}

            ### take actual action 
            if action_type == "attach":
                deps.add(p,c)
                parsed = [x for x in parsed if x!=c]

            elif action_type == "substituteDet":
                assert parsed[i]['tag'] == "DT"
                assert parsed[i]['form'] == sent[j]['form']
                assert parsed[i]['form'] in ('a', 'an', 'the')

                if DEBUG:
                    print "+++++ substitute Det +++++" , parsed[i]['id']
                    print parsed
                    print sent

                candidates=['a','the','an']
                best_score = float('-inf')
                best_cand = candidates[0]
                for cand in candidates:
                    tmp_tokens = sent[:]
                    tmp_tokens[j]['form'] = cand
                    tmp_sent = " ".join([tt['form'] for tt in tmp_tokens])
                    tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)

                    if best_score < tmp_score:
                        best_score = tmp_score
                        best_cand = cand
                
                sent[j]['form'] = cand
                parsed[i]['form'] = cand
                parsed[i]['morph'] = 1
                sent[j]['morph'] = 1
               
                if DEBUG:
                    print "***** substitute check *****"
                    print "parsed: ", parsed
                    print "sent: ", sent
 
                num_edits += 1

            elif action_type == "substituteNN":
                assert parsed[i]['tag'] in ("NN", "NNS")
                assert parsed[i]['form'] == sent[j]['form']

                if DEBUG:
                    print "+++++ substitute NN +++++" , parsed[i]['id']
                    print parsed
                    print sent

                if parsed[i]['tag'] == "NN":
                    parsed[i]['form'] = pluralize(parsed[i]['form'])
                    parsed[i]['tag'] = "NNS"
                    parsed[i]['morph'] = 1

                    sent[j]['form'] = pluralize(sent[j]['form'])
                    sent[j]['tag'] = "NNS"
                    sent[j]['morph'] = 1


                elif parsed[i]['tag'] == "NNS":
                    parsed[i]['form'] = singularize(parsed[i]['form'])
                    parsed[i]['tag'] = "NN"
                    parsed[i]['morph'] = 1

                    sent[j]['form'] = singularize(sent[j]['form'])
                    sent[j]['tag'] = "NN"
                    sent[j]['morph'] = 1
 
                else:
                    print parsed[i]['tag'] + ": something wrong"
                    raise

                if DEBUG:
                    print "***** substitute check *****"
                    print "parsed: ", parsed
                    print "sent: ", sent
 
                num_edits += 1

            elif action_type.startswith("delete"):
                if DEBUG:
                    print "delete"

                assert p['id'] == parsed[i]['id']
                delidx = p['id']

                # 1. decrement deps (i is an index boundary)
                if DEBUG:
                    print "+++++ decrement dep +++++" , str(delidx)
                    print deps.deps
                deps.decrement(delidx)
                if DEBUG:
                    print deps.deps

                # 2. delete the token
                delidx = p['id']
                del parsed[i]

                sent = [s_token for s_token in sent if s_token['id'] != delidx]

                # 3. decrement parsed
                new_parsed = []
                for p_token in parsed:
                    p_token = kskutil.decrementToken(p_token, delidx)
                    new_parsed.append(p_token)
                parsed = new_parsed

                new_sent = []
                for s_token in sent:
                    s_token = kskutil.decrementToken(s_token, delidx)
                    new_sent.append(s_token)
                sent = new_sent

                num_edits += 1

            elif action_type.startswith("insert"):
                if DEBUG:
                    print "insert" 

                assert p['id'] == parsed[i]['id']
                insidx = p['id']
                left_most_id = insidx
                left_most_char = p['form'][0]
                for child_i in deps._childs[insidx]:
                    if left_most_id > child_i['id']:
                        left_most_id = child_i['id']
                        left_most_char = child_i['form'][0]
                insidx = left_most_id

                # 1. increment deps
                if DEBUG:
                    print "+++++ increment dep +++++" , str(insidx)
                    print deps.deps
                deps.increment(insidx)
                if DEBUG:
                    print deps.deps

                # 2. increment parsed  (N.B. reversed order)
                if DEBUG:
                    print "##### increment parsed #####"
                    print parsed
                new_parsed = []
                for p_token in parsed:
                    p_token = kskutil.incrementToken(p_token, insidx)
                    new_parsed.append(p_token)
                parsed = new_parsed
                if DEBUG:
                    print parsed

                if DEBUG:
                    print "##### increment sent #####"
                    print sent
                new_sent = []
                for s_token in sent:
                    s_token = kskutil.incrementToken(s_token, insidx)
                    new_sent.append(s_token)
                sent = new_sent
                if DEBUG:
                    print sent

                # 3. create token for insertion (with morph=1!)
                token_i = ""
                if action_type.startswith("insertDet"):
                    candidates = DETS
                    best_cand = candidates[0]
                    best_score = float('-inf')
                    for cand in candidates:
                        tmp_sent_tokens = sent[:]
                        tmp_tokens = [tt['form'] for tt in tmp_sent_tokens]
                        tmp_tokens.insert(j, cand)
                        tmp_sent = " ".join(tmp_tokens)
                        tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                        if best_score < tmp_score:
                            best_score = tmp_score
                            best_cand = cand
                    token_i = kskutil.tokenTemplate(insidx, best_cand, 'DT')

                elif action_type.startswith("insertPrep"):
                    candidates = TARGET_PREP
                    best_cand = candidates[0]
                    best_score = float('-inf')
                    for cand in candidates:
                        tmp_sent_tokens = sent[:]
                        tmp_tokens = [tt['form'] for tt in tmp_sent_tokens]
                        tmp_tokens.insert(j, cand)
                        tmp_sent = " ".join(tmp_tokens)
                        tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                        if best_score < tmp_score:
                            best_score = tmp_score
                            best_cand = cand
                    token_i = kskutil.tokenTemplate(insidx, best_cand, 'IN')

                else:
                    raise
                if DEBUG:
                    print "----- new token -----"
                    print token_i

                # 4. insert the token to parsed
                if DEBUG:
                    print "***** insert check *****"
                    print "parsed: ", parsed
                    print "sent: ", sent
                parsed.insert(i, token_i)
                sent.insert(j, token_i)
                if DEBUG:
                    print "***** insert check *****"
                    print "parsed: ", parsed
                    print "sent: ", sent

                # 5. numedits++
                num_edits += 1

            elif action_type.startswith("substituteVform"):

                assert parsed[i]['tag'].startswith("VB")
                assert parsed[i]['form'] == sent[j]['form']

                if DEBUG:
                    print "+++++ substitute Vform +++++" , parsed[i]['id']
                    print parsed
                    print sent

                # TARGET_VFORM, and TENSE_ASPECTS are the candidates
                best_score = float('-inf')
                best_cand = str(parsed[i]['form'])
                best_tag = str(parsed[i]['tag'])
                for t_vtag, t_tense in zip(TARGET_VFORM, TENSE_ASPECTS):
                    tmp_tokens = sent[:]
                    cand = str(conjugate(lemma(parsed[i]['form']), t_tense))
                    tmp_tokens[j]['form'] = cand
                    tmp_sent = " ".join([tt['form'] for tt in tmp_tokens])
                    tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                    if best_score < tmp_score:
                        best_score = tmp_score
                        best_cand = cand
                        best_tag = t_vtag
               
                sent[j]['form'] = best_cand
                parsed[i]['form'] = best_cand
                sent[j]['tag'] = best_tag
                parsed[i]['tag'] = best_tag
                sent[j]['morph'] = 1
                parsed[i]['morph'] = 1

                # numedits++
                num_edits += 1

            elif action_type.startswith("substitutePrep"):
                if DEBUG:
                    print "substitutePrep"

                assert parsed[i]['tag'].startswith("IN")
                assert parsed[i]['form'] == sent[j]['form']

                if DEBUG:
                    print "+++++ substitute Prep +++++" , parsed[i]['id']
                    print parsed
                    print sent

                candidates = TARGET_PREP
                best_cand = candidates[0]
                best_score = float('-inf')
                for cand in candidates:
                    tmp_sent_tokens = sent[:]
                    tmp_sent_tokens[j]['form'] = cand
                    tmp_sent = " ".join([tt['form'] for tt in tmp_sent_tokens])
                    tmp_score = lmmodel.score(tmp_sent, bos=True, eos=True)
                    if best_score < tmp_score:
                        best_score = tmp_score
                        best_cand = cand
                sent[j]['form'] = cand
                parsed[i]['form'] = cand
                parsed[i]['morph'] = 1
                sent[j]['morph'] = 1

                if DEBUG:
                    print "***** substitute substitutePrep check *****"
                    print "parsed: ", parsed
                    print "sent: ", sent
 
                num_edits += 1

            else: # sanity check of action_type
                print
                print action_type
                raise

      #}}} end while

      if DEBUG:
          print "===final deps (train) ==="
          print sorted([t[1] for t in deps.deps])
      assert sorted([t[1] for t in deps.deps])[-1] == len(deps.deps)

   #}}}

#   def train_labeled(self, sent, iter_number, explore_policy=None): #{{{
#      id_to_action_mapper = self.id_to_action_mapper
#      updates=0
#      sent = [ROOT]+sent
#      self.scorer.tick()
#      deps = DependenciesCollection()
#      parsed = sent[:]
#      fcache = {}
#      scache = {}
#      while len(parsed)>1: #{{{
#         # find best action
#         #best = -9999999
#         #best_pair = None 
#         scored = []
#         for i,(tok1,tok2) in enumerate(zip(parsed,parsed[1:])):
#            tid = tok1['id']
#            if tid in fcache:
#               feats = fcache[tid]
#            else:
#               feats = self.featExt.extract(parsed,deps,i,sent)
#               fcache[tid]=feats
#            if tid in scache:
#               scores = scache[tid]
#            else:
#               scores = self.scorer.get_scores(feats)
#               scache[tid] = scores 
#            for aid,score in scores.iteritems():
#               dr,lbl = id_to_action_mapper[aid]
#               if dr == 0:
#                  scored.append((score,(aid,lbl),feats,tok1,tok2))
#               else:
#                  assert(dr == 1)
#                  scored.append((score,(aid,lbl),feats,tok2,tok1))
#         #print [(x[0],x[1]) for x in scored]
#         scored=sorted(scored,key=lambda (s,cls,f,t1,t2):-s)
#         s,cls,f,c,p = scored[0]
#         #print "selected:",cls,p['id'],c['id'],s
#         cost = self.oracle.action_cost(parsed,p,c,cls[1])
#         if cost == 0:
#            correct = True
#         else:
#            correct = False
#            scache = {} # clear the cache -- numbers changed..
#            # find best allowable pair
#            for s,gcls,gf,gc,gp in scored[1:]:
#               if self.oracle.action_cost(parsed,gp,gc,gcls[1]) == 0:
#                  break
#
#            self.scorer.add(f,cls[0],-1)
#            self.scorer.add(gf,gcls[0],1)
#
#            updates+=1
#            if updates>200:
#               print "STUCK, probably because of incomplete feature set",id_to_action_mapper[cls[0]],id_to_action_mapper[gcls[0]]
#               print " ".join([x['form'] for x in sent])
#               print " ".join([x['form'] for x in parsed])
#               return
#         if correct or (explore_policy and explore_policy.should_explore(iter_number)):
#            # remove the neighbours of parent from the cache
#            i = parsed.index(p)
#            frm=i-4
#            to=i+4
#            if frm<0: frm = 0
#            if to>=len(parsed):to=len(parsed)-1
#            for tok in parsed[frm:to]:
#               try:
#                  del fcache[tok['id']]
#                  del scache[tok['id']]
#               except: pass
#            ###
#            deps.add(p,c,cls[1])
#            parsed = [x for x in parsed if x!=c]
#      #}}} end while
#   #}}}
##}}}


class Model: #{{{
   def __init__(self, featuresFile, weightFile, iter=None):
      self._featuresFile = featuresFile
      self._weightFile = weightFile
      self._iter=iter

      featuresModule = load_module(featuresFile)
      self.fext = featuresModule.FeaturesExtractor()

   def save(self, filename):
      fh = file(filename,"w")
      fh.write("%s\n%s\n" % (self._featuresFile, self._weightFile))
      fh.close()

   @classmethod
   def load(cls, filename, iter=19):
      lines = file(filename,"r").readlines()
      dirname = os.path.dirname(filename)
      featuresFile = os.path.join(dirname,lines[0].strip())
      weightFile   = os.path.join(dirname,lines[1].strip())
      return cls(featuresFile, weightFile, iter)

   def weightsFile(self, iter):
      if iter is None: iter = self._iter
      return "%s.%s" % (self._weightFile, iter)

   def featureExtractor(self):
      return self.fext
#}}}

def train(attachonly, sents, gold_sents, model, dev=None, ITERS=20, save_every=None, explore_policy=None, shuffle_sents=True):

   fext = model.featureExtractor()
   oracle=CostOracle()
   scorer=MultitronParameters(10)

   parser=Parser(attachonly, scorer, fext, oracle)
   for ITER in xrange(1,ITERS+1):
      parser.cumcost = 0
      print "Iteration",ITER,"[",
      if shuffle_sents:
          tmp = zip(sents, gold_sents)
          random.shuffle(tmp)
          tmp = zip(*tmp)
          sents = list(tmp[0])
          gold_sents = list(tmp[1])
      for i,sent in enumerate(sents):
         if i%100==0: 
            print i,"(%s)" % parser.cumcost,
            sys.stdout.flush()
         parser.train(sent, gold_sents[i], ITER, explore_policy)
      print "]"
      if save_every and (ITER % save_every==0):
         print "saving weights at iter",ITER
         parser.scorer.dump_fin(file(model.weightsFile(ITER),"w"))
         if dev:
            print "testing dev skipped"
            #print "testing dev"
            #print "\nscore: %s" % (test(attachonly,dev,model,ITER,quiet=True,labeled=False),)
   parser.scorer.dump_fin(file(model.weightsFile("FINAL"),"w"))

def label_sets_from_sents(sents):
   left_labels = set()
   right_labels = set()
   for sent in sents:
      for tok in sent:
         if tok['id'] > tok['parent']:
            left_labels.add(tok['prel'])
         else:
            right_labels.add(tok['prel'])
   return left_labels,right_labels

#def train_labeled(sents, model, dev=None,ITERS=20,save_every=None,explore_policy=None,shuffle_sents=True):
#   from ml.sml import SparseMultitronParameters
#   id_to_action_mapper = {}
#   left_labels, right_labels = label_sets_from_sents(sents)
#   aid = 0
#   for label in right_labels:
#      id_to_action_mapper[aid] = (0,label)
#      aid += 1
#   for label in left_labels:
#      id_to_action_mapper[aid] = (1,label)
#      aid += 1
#   pickle.dump(id_to_action_mapper,open(model.weightsFile("amap"),"w"))
#   fext = model.featureExtractor()
#   oracle=CostOracle()
#   scorer=SparseMultitronParameters(max(id_to_action_mapper.keys())+1)
#   parser=Parser(scorer, fext, oracle)
#   parser.id_to_action_mapper = id_to_action_mapper
#   if shuffle_sents: random.shuffle(sents)
#   for ITER in xrange(1,ITERS+1):
#      print "Iteration",ITER,"[",
#      for i,sent in enumerate(sents):
#         if i%100==0: 
#            print i,
#            sys.stdout.flush()
#         parser.train_labeled(sent, ITER, explore_policy) 
#      print "]"
#      if save_every and (ITER % save_every==0):
#         print "saving weights at iter",ITER
#         parser.scorer.dump_fin(file(model.weightsFile(ITER),"w"),sparse=True)
#         if dev:
#            print "testing dev"
#            print "\nscore: %s" % (test(dev,model,ITER,quiet=True,labeled=True),)
#   parser.scorer.dump_fin(file(model.weightsFile("FINAL"),"w"),sparse=True)

def test(attachonly, sents,model,iter="FINAL",quiet=False,ignore_punc=False,labeled=True):
   fext = model.featureExtractor()
   import time
   good = 0.0
   bad  = 0.0
   complete = 0.0
   if labeled:
      from ml.sml import SparseMulticlassModel
      m=SparseMulticlassModel(file(model.weightsFile(iter)))
   else:
      m=MulticlassModel(model.weightsFile(iter))
   start = time.time()
   parser=Parser(attachonly, m,fext,Oracle())
   if labeled:
      parser.id_to_action_mapper = pickle.load(file(model.weightsFile("amap")))
   scores=[]

   for sent in sents:
      sent_good=0.0
      sent_bad =0.0
      no_mistakes=True
      if not quiet:
         print "@@@",good/(good+bad+1)
      if labeled:
         deps=parser.parse_labeled(sent)
      else:
         deps, sent_new = parser.parse(sent)
      #print sent
      #print sent_new
      sent = deps.annotate(sent_new)


      for tok in sent:
         if not quiet:
            if labeled:
               print tok['id'], tok['form'], "_",tok['tag'],tok['tag'],"_",tok['pparent'],tok['pprel'],"_ _"
            else:
               print tok['id'], tok['form'], "_",tok['tag'],tok['tag'],"_",tok['pparent'],"_ _ _"
         if ignore_punc and tok['form'][0] in "'`,.-;:!?{}": continue
         if tok['parent']==tok['pparent']:
            good+=1
            sent_good+=1
         else:
            bad+=1
            sent_bad+=1
            no_mistakes=False
      if not quiet: print
      if no_mistakes: complete+=1
      scores.append((sent_good/(sent_good+sent_bad)))

   if not quiet:
      print "time(seconds):",time.time()-start
      print "num sents:",len(sents)
      print "complete:",complete/len(sents)
      print "macro:",sum(scores)/len(scores)
      print "micro:",good/(good+bad)
   return good/(good+bad), complete/len(sents)

def parse(attachonly, sents, model, iter="FINAL"):
   fext = model.featureExtractor()
   m=MulticlassModel(model.weightsFile(iter))
   parser=Parser(attachonly,m,fext,Oracle())
   #for sent in sents:
   for sent in tqdm(sents, mininterval=1, ncols=80):
      deps, sent_new = parser.parse(sent)
      sent = deps.annotate(sent_new)
      for tok in sent:
         print '\t'.join([str(tok['id']), tok['form'], "_", tok['tag'], tok['tag'], "_" , str(tok['pparent']), "_", "_", "_"])
      print 

#def parse_labeled(sents,model,iter="FINAL"):
#   from ml.sml import SparseMulticlassModel
#   fext = model.featureExtractor()
#   m=SparseMulticlassModel(model.weightsFile(iter),sparse=True)
#   parser=Parser(m,fext,Oracle())
#   id_to_action_mapper = pickle.load(file(model.weightsFile("amap")))
#   parser.id_to_action_mapper = id_to_action_mapper
#   for sent in sents:
#      deps=parser.parse_labeled(sent)
#      sent = deps.annotate(sent)
#      for tok in sent:
#         print tok['id'], tok['form'], "_",tok['tag'],tok['tag'],"_",tok['pparent'],tok['pprel'],"_ _"
#      print 

def make_parser(modelfile,iter):
   weightsFile = "%s.weights" % (modelfile)
   modelfile = "%s.model" % (modelfile)
   model = Model.load(modelfile,iter)
   fext = model.featureExtractor()
   m=MulticlassModel(model.weightsFile(iter))
   parser=Parser(m,fext,Oracle())
   return parser

def load_sentences(filename,ONLY_PROJECTIVE=False):
   sents = [s for s in io.conll_to_sents(file(filename)) if (not ONLY_PROJECTIVE) or isprojective.is_projective(s)]
   return sents


def getActiontype(c): #{{{
    action_type = ""
    if c <= 1:
        action_type = "attach"
    elif c == 2:
        action_type = "substituteNN"
    elif c == 3:
        action_type = "deleteDet"
    elif c == 4:
        action_type = "insertDet"
    elif c == 5:
        action_type = "substituteVform"
    elif c == 6:
        action_type = "substitutePrep"
    elif c == 7:
        action_type = "deletePrep"
    elif c == 8:
        action_type = "insertPrep"
    elif c == 9:
        action_type = "substituteDet"
    else:
        raise
    return action_type
#}}}

