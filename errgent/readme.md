# Errgent: grammatical error injection script

The script inject grammatical errors into sentences with CoNLL format.
usage: inject_error.py source error_rate_inpercentage

e.g.  
> python inject_error.py ../data/train.E00 5 >  ../data/train.E05
> python inject_error.py ../data/train.E00 10 > ../data/train.E10
> python inject_error.py ../data/train.E00 15 > ../data/train.E15
> python inject_error.py ../data/train.E00 20 > ../data/train.E20

N.B.
- Chunking information should be added in the third column in advance. (e.g., using CRFsuite)
