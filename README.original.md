This is the code used in the TACL paper

   "Training Deterministic Parsers with Non-Deterministic Oracles",
   Yoav Goldberg and Joakim Nivre (2013)

The easyfirst/ directory contains code for the EasyFirst experiments,
and the lefttoright/ direcory contains code for the ArcEager and ArcHybrid experiments.



The specific scripts used for training/testing are:

   easyfirst/tacl_exps/train_ef_parsers.py                      # EasyFirst models
   lefttoright/tacl_exps/train_re_arceager_models.py            # ArcEager models
   lefttoright/tacl_exps/train_archybrid_models.py              # ArcHybrid models
   lefttoright/tacl_exps/train_re_arceager_models_kpsearch.py   # for the heatmap results



The feature definitions are in:

   easyfirst/features/znp.py                 # EasyFirst
   lefttoright/features/extractors.py       
      class EagerZhangNivre2011Extractor()   # ArcEager 
      class HybridFeatures()                 # ArcHybrid


INSTALLATION:
   The code relies on a compiled cython module.
   If you are on python2.7 and 64-bit linux, things should work out of the box.
   Otherwise you will need to compile the module.
   See instructions in
      easyfirst/ml/INSTALL
      lefttoright/ml/INSTALL


- Yoav Goldberg and Joakim Nivre, 2013.
  For questions contact Yoav Goldberg.

=======

LICENSE:
   The code is distributed under the GPL v3 license
   available at http://www.gnu.org/licenses/gpl-3.0.html 
