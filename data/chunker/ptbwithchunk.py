import sys
import os

ptb_f = open(sys.argv[1]).readlines()
chunk_f = open(sys.argv[2]).readlines()
assert len(ptb_f) == len(chunk_f)

for p, c in zip(ptb_f, chunk_f):
    if p.rstrip() == "":
        print p.rstrip()
    else:
        p_li = p.rstrip().split('\t')
        p_li[2] = c.rstrip()
        print '\t'.join(p_li)
