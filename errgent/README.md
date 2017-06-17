# Errgent: Grammatical Error Injection Script

The script is to inject grammatical errors into sentences with CoNLL format.

N.B. Chunking information must be added in the third column in advance. (e.g., see [CRFsuite](http://www.chokkan.org/software/crfsuite/tutorial.html))


    usage: python inject_error.py source_file  error_rate_in_percentage

    e.g.,  
    python inject_error.py ../data/train.E00 5 >  ../data/train.E05



