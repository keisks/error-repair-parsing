# Errgent: grammatical error injection script

The script inject grammatical errors into sentences with CoNLL format.
usage: inject_error.py source error_rate_inpercentage
e.g.  
> python inject_error.py ../data/sample.train.E00 5 > ../data/sample.train.E05
> python inject_error.py ../data/sample.train.E00 10 > ../data/sample.train.E10
> python inject_error.py ../data/sample.train.E00 15 > ../data/sample.train.E15
> python inject_error.py ../data/sample.train.E00 20 > ../data/sample.train.E20

