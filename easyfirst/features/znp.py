from common import PAD,ROOT
## An extended feature-set for the easy-first parser.

## Copyright Keisuke Sakaguchi (2017)
## Originally under GPL by Yoav Goldberg (2013)
##
##    this code is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    Thie code is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Thie code.  If not, see <http://www.gnu.org/licenses/>.


class BaselineFeatureExtractor: # {{{
   LANG='ENG'
   def __init__(self):
      self.versions = None
      self.vocab = set()

   def extract(self,parsed,deps,i,sent=None):
      """
      i=T4:
         should I connect T4 and T5 in:
            t1 t2 t3 T4 T5 t6 t7 t8
         ?
         focus: f1=T4 f2=T5
         previous: p1=t3 p2=t2
         next:     n1=t6 n2=t7
      returns (feats1,feats2)
      where feats1 is a list of features for connecting T4->T5  (T4 is child)
      and   feats2 is a list of features for connecting T4<-T5  (T5 is child)
      """
      #LANG = self.LANG
      CC = ['CC','CONJ']
      IN = ['IN']

      j=i+1
      features=[]

      f1=parsed[i]
      f2=parsed[j]
      n1=parsed[j+1] if j+1 < len(parsed) else PAD
      n2=parsed[j+2] if j+2 < len(parsed) else PAD
      p1=parsed[i-1] if i-1 > 0 else PAD
      p2=parsed[i-2] if i-2 > 0 else PAD

      f = features.append
      import math

      # Core Elements
      s0 = f1
      if s0 is not PAD:
         l = deps.left_child(s0)
         s0l = l if l else PAD
         r = deps.right_child(s0)
         s0r = r if r else PAD
         l = deps.left_child2(s0)
         s0l2 = l if l else PAD
         r = deps.right_child2(s0)
         s0r2 = r if r else PAD
      else:
         s0l = PAD
         s0r = PAD
         s0l2 = PAD
         s0r2 = PAD
      n0 = f2
      if n0 is not PAD:
         l = deps.left_child(n0)
         n0l = l if l else PAD
         l = deps.left_child2(n0)
         n0l2 = l if l else PAD
      else:
         n0l = PAD
         n0l2 = PAD

      if n0 != PAD and s0 != PAD:
         d = str(n0['id'] - s0['id'])
         if len(d) == 2: d = "10+" #TODO: cutoff needed?
      else: d = "NA"

      s0vr = deps.num_right_children(s0)
      s0vl = deps.num_left_children(s0)
      n0vl = deps.num_left_children(n0)

      s0w = s0['form']
      n0w = n0['form']

      # Edit flag
      n0e = n0['morph'] # actually it is an edited flag

      n1w = n1['form']
      n2w = n2['form']
      s0lw = s0l['form']
      s0rw = s0r['form']
      n0lw = n0l['form']
      s0l2w = s0l2['form']
      s0r2w = s0r2['form']
      n0l2w = n0l2['form']

      s0p = s0['tag']
      n0p = n0['tag']
      n1p = n1['tag']
      n2p = n2['tag']
      s0lp = s0l['tag']
      s0rp = s0r['tag']
      n0lp = n0l['tag']
      s0l2p = s0l2['tag']
      s0r2p = s0r2['tag']
      n0l2p = n0l2['tag']

      #assert(s0l == PAD or s0l2 == PAD or s0l['id'] < s0l2['id'])
      #assert(n0lc == PAD or n0lc2 == PAD or n0lc['id'] < n0lc2['id'])
      #assert(s0rc2 == PAD or s0rc == PAD or s0rc['id'] > s0rc2['id'])
      #assert(s0rc == PAD or s0rc['id'] > s0['id'])

      s0L = deps.label_for(s0)
      s0lL = deps.label_for(s0l)
      s0rL = deps.label_for(s0r)
      n0lL = deps.label_for(n0l)
      s0l2L = deps.label_for(s0l2)
      s0r2L = deps.label_for(s0r2)
      n0l2L = deps.label_for(n0l2)

      s0wp = "%s:%s" % (s0w, s0p)
      n0wp = "%s:%s" % (n0w, n0p)
      n1wp = "%s:%s" % (n1w, n0p)
      n2wp = "%s:%s" % (n2w, n0p)

      s0sr = deps.right_labels(s0)
      s0sl = deps.left_labels(s0)
      n0sl = deps.left_labels(n0)

      # Single Words
      f("s0wp_%s" % (s0wp))
      f("s0w_%s"  % (s0w))
      f("s0p_%s"  % (s0p))
      f("n0wp_%s" % (n0wp))
      f("n0w_%s"  % (n0w))

      # new features
      f("n0e_%s"  % (n0e))
      #f("s0c_%s"  % (s0c)) chunking feature?
      #f("n0c_%s"  % (n0c))

      f("n0p_%s"  % (n0p))
      f("n1wp_%s" % (n1wp))
      f("n1w_%s"  % (n1w))
      f("n1p_%s"  % (n1p))
      f("n2wp_%s" % (n2wp))
      f("n2w_%s"  % (n2w))
      f("n2p_%s"  % (n2p))

      # Pairs
      f("s0wp,n0wp_%s_%s" % (s0wp, n0wp))
      f("s0wp,n0w_%s_%s" % (s0wp, n0w))
      f("s0w,n0wp_%s_%s" % (s0w, n0wp))
      f("s0wp,n0p_%s_%s" % (s0wp, n0p))
      f("s0p,n0wp_%s_%s" % (s0p, n0wp))
      f("s0w,n0w_%s_%s" % (s0w, n0w)) #?
      f("s0p,n0p_%s_%s" % (s0p, n0p))
      f("n0p,n1p_%s_%s" % (n0p, n1p))

      # Tuples
      f("n0p,n1p,n2p_%s_%s_%s" % (n0p, n1p, n2p))
      f("s0p,n0p,n1p_%s_%s_%s" % (s0p, n0p, n1p))
      f("s0p,s0lp,n0p_%s_%s_%s" % (s0p, s0lp, n0p))
      f("s0p,s0rp,n0p_%s_%s_%s" % (s0p, s0rp, n0p))
      f("s0p,n0p,n0lp_%s_%s_%s" % (s0p, n0p, n0lp))

      # Distance
      f("s0wd_%s:%s" % (s0w, d))
      f("s0pd_%s:%s" % (s0p, d))
      f("n0wd_%s:%s" % (n0w, d))
      f("n0pd_%s:%s" % (n0p, d))
      f("s0w,n0w,d_%s:%s:%s" % (s0w, n0w, d))
      f("s0p,n0p,d_%s:%s:%s" % (s0p, n0p, d))

      # Valence
      f("s0wvr_%s:%s" % (s0w, s0vr))
      f("s0pvr_%s:%s" % (s0p, s0vr))
      f("s0wvl_%s:%s" % (s0w, s0vl))
      f("s0pvl_%s:%s" % (s0p, s0vl))
      f("n0wvl_%s:%s" % (n0w, n0vl))
      f("n0pvl_%s:%s" % (n0p, n0vl))

      # Unigrams
      f("s0L_%s" % (s0L))

      f("s0lw_%s" % (s0lw))
      f("s0lp_%s" % (s0lp))
      f("s0lL_%s" % (s0lL))

      f("s0rw_%s" % (s0rw))
      f("s0rp_%s" % (s0rp))
      f("s0rL_%s" % (s0rL))

      f("n0lw_%s" % (n0lw))
      f("n0lp_%s" % (n0lp))
      f("n0lL_%s" % (n0lL))

      # Third-order
      #do we really need the non-grandparent ones?
      f("s0l2w_%s" % (s0l2w))
      f("s0l2p_%s" % (s0l2p))
      f("s0l2L_%s" % (s0l2L))
      f("s0r2w_%s" % (s0r2w))
      f("s0r2p_%s" % (s0r2p))
      f("s0r2L_%s" % (s0r2L))
      f("n0l2w_%s" % (n0l2w))
      f("n0l2p_%s" % (n0l2p))
      f("n0l2L_%s" % (n0l2L))
      f("s0p,s0lp,s0l2p_%s_%s_%s" % (s0p, s0lp, s0l2p))
      f("s0p,s0rp,s0r2p_%s_%s_%s" % (s0p, s0rp, s0r2p))
      f("n0p,n0lp,n0l2p_%s_%s_%s" % (n0p, n0lp, n0l2p))

      # Labels
      f("s0wsr_%s_%s" % (s0w, s0sr))
      f("s0psr_%s_%s" % (s0p, s0sr))
      f("s0wsl_%s_%s" % (s0w, s0sl))
      f("s0psl_%s_%s" % (s0p, s0sl))
      f("n0wsl_%s_%s" % (n0w, n0sl))
      f("n0psl_%s_%s" % (n0p, n0sl))

      #from stnfeaturesplus
      # bigram+left/right child
      append = f
      f1_tag = f1['tag'] 
      f2_tag = f2['tag'] 
      p1_tag = p1['tag'] 
      n1_tag = n1['tag'] 
      n2_tag = n2['tag'] 
      p2_tag = p2['tag'] 
      f1_ctag = f1['tag'] 
      f2_ctag = f2['tag'] 
      p1_ctag = p1['tag'] 
      n1_ctag = n1['tag'] 
      n2_ctag = n2['tag'] 
      p2_ctag = p2['tag'] 
      #if f1_tag in IN: f1_tag = "%s_%s" % (f1_tag,f1_form)
      #if f2_tag in IN: f2_tag = "%s_%s" % (f2_tag,f2_form)
      #if p1_tag in IN: p1_tag = "%s_%s" % (p1_tag,p1_form)
      #if p2_tag in IN: p2_tag = "%s_%s" % (p2_tag,p2_form)
      #if n1_tag in IN: n1_tag = "%s_%s" % (n1_tag,n1_form)
      #if n2_tag in IN: n2_tag = "%s_%s" % (n2_tag,n2_form)


      ## @@@ Hurts performance with small training set. benefit with large!
      #if p2_tag in CC: p2_tag = "%s%s" % (p2_tag,p2_form)
      #if n2_tag in CC: n2_tag = "%s%s" % (n2_tag,n2_form)
      ####

      left_child=deps.left_child
      f1lc = left_child(f1)
      if f1lc: f1lc=f1lc['tag']
      f2lc = left_child(f2)
      if f2lc: f2lc=f2lc['tag']
      n1lc = left_child(n1) 
      if n1lc: n1lc=n1lc['tag']
      n2lc = left_child(n2) 
      if n2lc: n2lc=n2lc['tag']
      p1lc = left_child(p1) 
      if p1lc: p1lc=p1lc['tag']
      p2lc = left_child(p2) 
      if p2lc: p2lc=p2lc['tag']

      ## TO-VERB (to keep, to go,...)
      if f1_tag[0]=='V' and f1lc=='TO': f1_tag="%s_TO" % f1_tag
      if f2_tag[0]=='V' and f2lc=='TO': f2_tag="%s_TO" % f2_tag
      if p1_tag[0]=='V' and p1lc=='TO': p1_tag="%s_TO" % p1_tag
      if p2_tag[0]=='V' and p2lc=='TO': p2_tag="%s_TO" % p2_tag
      if n1_tag[0]=='V' and n1lc=='TO': n1_tag="%s_TO" % n1_tag
      if n2_tag[0]=='V' and n2lc=='TO': n2_tag="%s_TO" % n2_tag

      f1rc_form=None
      right_child=deps.right_child
      f1rc = right_child(f1) 
      if f1rc: 
         f1rc_form=f1rc['form']
         f1rc=f1rc['tag']

      f2rc_form=None
      f2rc = right_child(f2) 
      if f2rc: 
         f2rc_form=f2rc['form']
         f2rc=f2rc['tag']

      n1rc_form=None
      n1rc = right_child(n1) 
      if n1rc: 
         n1rc_form=n1rc['form']
         n1rc=n1rc['tag']

      n2rc = right_child(n2) 
      if n2rc: n2rc=n2rc['tag']
      p1rc = right_child(p1) 
      if p1rc: p1rc=p1rc['tag']
      p2rc = right_child(p2) 
      if p2rc: p2rc=p2rc['tag']

      f1rc2 = deps.right_child2(f1)
      if f1rc2: f1rc2 = f1rc2['tag']
      f2rc2 = deps.right_child2(f2)
      if f2rc2: f2rc2 = f2rc2['tag']
      f1lc2 = deps.left_child2(f1)
      if f1lc2: f1lc2 = f1lc2['tag']
      f2lc2 = deps.left_child2(f2)
      if f2lc2: f2lc2 = f2lc2['tag']
      append("Af1tf2t_%s_%s_%s_%s" % (f1_tag,f2_tag,f1lc,f2lc))
      append("Ap1tf1t_%s_%s_%s_%s" % (p1_tag,f1_tag,p1lc,f1lc))
      append("Ap1tf2t_%s_%s_%s_%s" % (p1_tag,f2_tag,p1lc,f2lc))
      append("Af2tn1t_%s_%s_%s_%s" % (f2_tag,n1_tag,f2lc,n1lc))
      append("Af1tn1t_%s_%s_%s_%s" % (f1_tag,n1_tag,f1lc,n1lc))

      append("Bf1tf2t_%s_%s_%s_%s" % (f1_tag,f2_tag,f1lc,f2rc))
      append("Bp1tf1t_%s_%s_%s_%s" % (p1_tag,f1_tag,p1lc,f1rc))
      append("Bp1tf2t_%s_%s_%s_%s" % (p1_tag,f2_tag,p1lc,f2rc))
      append("Bf2tn1t_%s_%s_%s_%s" % (f2_tag,n1_tag,f2lc,n1rc))
      append("Bf1tn1t_%s_%s_%s_%s" % (f1_tag,n1_tag,f1lc,n1rc))

      append("Cf1tf2t_%s_%s_%s_%s" % (f1_tag,f2_tag,f1rc,f2lc))
      append("Cp1tf1t_%s_%s_%s_%s" % (p1_tag,f1_tag,p1rc,f1lc))
      append("Cp1tf2t_%s_%s_%s_%s" % (p1_tag,f2_tag,p1rc,f2lc))
      append("Cf2tn1t_%s_%s_%s_%s" % (f2_tag,n1_tag,f2rc,n1lc))
      append("Cf1tn1t_%s_%s_%s_%s" % (f1_tag,n1_tag,f1rc,n1lc))

      append("Df1tf2t_%s_%s_%s_%s" % (f1_tag,f2_tag,f1rc,f2rc))
      append("Dp1tf1t_%s_%s_%s_%s" % (p1_tag,f1_tag,p1rc,f1rc))
      append("Dp1tf2t_%s_%s_%s_%s" % (p1_tag,f2_tag,p1rc,f2rc))
      append("Df2tn1t_%s_%s_%s_%s" % (f2_tag,n1_tag,f2rc,n1rc))
      append("Df1tn1t_%s_%s_%s_%s" % (f1_tag,n1_tag,f1rc,n1rc))

      # only triples
      append("1rDf1tf2t_%s_%s_%s" % (f1_tag,f2_tag,f1rc))
      append("1rDp1tf1t_%s_%s_%s" % (p1_tag,f1_tag,p1rc))
      append("1rDp1tf2t_%s_%s_%s" % (p1_tag,f2_tag,p1rc))
      append("1rDf2tn1t_%s_%s_%s" % (f2_tag,n1_tag,f2rc))
      append("1rDf1tn1t_%s_%s_%s" % (f1_tag,n1_tag,f1rc))
      append("1lDf1tf2t_%s_%s_%s" % (f1_tag,f2_tag,f1lc))
      append("1lDp1tf1t_%s_%s_%s" % (p1_tag,f1_tag,p1lc))
      append("1lDp1tf2t_%s_%s_%s" % (p1_tag,f2_tag,p1lc))
      append("1lDf2tn1t_%s_%s_%s" % (f2_tag,n1_tag,f2lc))
      append("1lDf1tn1t_%s_%s_%s" % (f1_tag,n1_tag,f1lc))
      # 
      append("2rDf1tf2t_%s_%s_%s" % (f1_tag,f2_tag,f2rc))
      append("2rDp1tf1t_%s_%s_%s" % (p1_tag,f1_tag,f1rc))
      append("2rDp1tf2t_%s_%s_%s" % (p1_tag,f2_tag,f2rc))
      append("2rDf2tn1t_%s_%s_%s" % (f2_tag,n1_tag,n1rc))
      append("2rDf1tn1t_%s_%s_%s" % (f1_tag,n1_tag,n1rc))
      append("2lDf1tf2t_%s_%s_%s" % (f1_tag,f2_tag,f2lc))
      append("2lDp1tf1t_%s_%s_%s" % (p1_tag,f1_tag,f1lc))
      append("2lDp1tf2t_%s_%s_%s" % (p1_tag,f2_tag,f2lc))
      append("2lDf2tn1t_%s_%s_%s" % (f2_tag,n1_tag,n1lc))
      append("2lDf1tn1t_%s_%s_%s" % (f1_tag,n1_tag,n1lc))

      # 4gram tags
      append("A1_%s_%s_%s"    % (       f2_tag,f2rc,n1_tag))  # not described
      append("A2_%s_%s_%s_%s" % (f1_tag,f2_tag,f2rc,n1_tag))

      append("A3_%s_%s_%s"    % (f1_tag       ,f1lc,p1_tag)) # not described
      append("A4_%s_%s_%s_%s"    % (f1_tag,f2_tag,f1lc,p1_tag))

      append("A5_%s_%s_%s_%s"    % (f2_tag,f2rc,n1_tag,n2_tag))
      append("A6_%s_%s_%s_%s"    % (f1_tag,f1lc,p1_tag,p2_tag))

      # 5gram tags
      append("A7_%s_%s_%s_%s"    % (p1_tag,f1_tag,f2_tag,n1_tag))

      append("A8_%s_%s_%s_%s_%s"    % (f1_tag,f2_tag,f2rc,n1_tag,n2_tag))
      append("A9_%s_%s_%s_%s_%s"    % (f2_tag,f1_tag,f1lc,p1_tag,p2_tag))

      # two children (can be labeled)
      append("X1_%s_%s_%s" % (f1_tag, f1rc, f1rc2))
      append("X2_%s_%s_%s" % (f1_tag, f1lc, f1lc2))
      append("X3_%s_%s_%s" % (f2_tag, f2rc, f2rc2))
      append("X4_%s_%s_%s" % (f2_tag, f2lc, f2lc2))

      append("X5_%s_%s_%s_%s" % (f2_tag, f2rc, f2rc2, n1_tag))
      append("X6_%s_%s_%s_%s" % (f1_tag, f1lc, f1lc2, p1_tag))

      append("X7_%s_%s_%s_%s" % (f1_tag, f1rc, f1rc2, f2_tag))
      append("X8_%s_%s_%s_%s" % (f2_tag, f2lc, f2lc2, f1_tag))

      return features

      for (fst,snd,typ) in [(f1,f2,"f1f2")]: #,(f1,n1,"f1n1"),(p1,f2,"p1f2")]: # the last two are too much
         if fst is PAD or snd is PAD: continue
         f=sent.index(fst)
         t=sent.index(snd)
         fstt=fst['tag']
         sndt=snd['tag']
         lo1 = sent[f-1] if f>0 else PAD
         ro1 = sent[f+1] if f+1<len(sent) else PAD
         lo2 = sent[t-1] if t>0 else PAD
         ro2 = sent[t+1] if t+1<len(sent) else PAD
         append("%s_ngbrs1_%s_%s_%s" % (typ,lo1['tag'],fstt,sndt))
         append("%s_ngbrs1_%s_%s_%s_%s" % (typ,lo1['tag'],fstt,sndt,ro2['tag']))
         append("%s_ngbrs2_%s_%s_%s" % (typ,lo1['tag'],sndt,ro2['tag']))
         append("%s_ngbrs3_%s_%s_%s" % (typ,lo1['tag'],fstt,ro2['tag']))
         append("%s_ngbrs4_%s_%s_%s" % (typ,fstt,sndt,ro2['tag']))

         append("%s_Angbrs1_%s_%s_%s" % (typ,ro1['tag'],fstt,lo2['tag']))
         append("%s_Angbrs1_%s_%s_%s_%s" % (typ,ro1['tag'],fstt,lo2['tag'],sndt))
         append("%s_Angbrs2_%s_%s_%s" % (typ,fstt,ro1['tag'],sndt))
         append("%s_Angbrs3_%s_%s_%s" % (typ,fstt,lo2['tag'],sndt))
         append("%s_Angbrs4_%s_%s_%s" % (typ,ro1['tag'],lo2['tag'],sndt))

         append("%s_Bngbrs1_%s_%s_%s_%s" % (typ,lo1['tag'],fstt,lo2['tag'],sndt))
         append("%s_Bngbrs2_%s_%s_%s_%s" % (typ,fstt,ro1['tag'],sndt,ro2['tag']))


      return features
   #}}}

FeaturesExtractor = BaselineFeatureExtractor
