#!/bin/bash

# train.E00 = ptb.train (in CoNLL format)
python inject_error.py ../data/train.E00 5 >  ../data/train.E05
python inject_error.py ../data/train.E00 10 > ../data/train.E10
python inject_error.py ../data/train.E00 15 > ../data/train.E15
python inject_error.py ../data/train.E00 20 > ../data/train.E20

# dev.E00 = ptb.dev (in CoNLL format)
python inject_error.py ../data/dev.E00 5 >  ../data/dev.E05
python inject_error.py ../data/dev.E00 10 > ../data/dev.E10
python inject_error.py ../data/dev.E00 15 > ../data/dev.E15
python inject_error.py ../data/dev.E00 20 > ../data/dev.E20

# test.E00 = ptb.test (in CoNLL format)
python inject_error.py ../data/test.E00 5 >  ../data/test.E05
python inject_error.py ../data/test.E00 10 > ../data/test.E10
python inject_error.py ../data/test.E00 15 > ../data/test.E15
python inject_error.py ../data/test.E00 20 > ../data/test.E20

