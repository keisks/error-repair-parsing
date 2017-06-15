#!/usr/bin/env python
#encoding: utf-8

import sys
import os

for li in open(sys.argv[1], 'r'):
    if li.rstrip() == "":
        print 
    else:
        properties = ""
        if '\t' in li:
            properties = li.rstrip().split('\t')
        else:
            properties = li.rstrip().split()
        # conll09 columns
        # ID FORM LEMMA PLEMMA POS PPOS FEAT PFEAT HEAD PHEAD DEPREL PDEPREL FILLPRED PRED APREDs
        conll09 = []
        conll09.append(properties[0]) #ID
        conll09.append(properties[1]) #FORM
        conll09.append(properties[2]) #LEMMA
        conll09.append(properties[2]) #PLEMMA
        conll09.append(properties[3]) #POS
        conll09.append(properties[3]) #PPOS
        conll09.append(properties[5]) #FEAT (=MORPH)
        conll09.append(properties[6]) #HEAD
        conll09.append(properties[6]) #PHEAD
        conll09.append(properties[3]) #DEPREL  
        conll09.append(properties[3]) #PDEPREL

        conll09.append('_') #FILLPRED
        conll09.append('_') #PRED
        conll09.append('_') #APREDs
        print '\t'.join(conll09)

