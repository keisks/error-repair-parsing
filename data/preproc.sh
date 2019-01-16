#!/bin/bash

# Before running this script, make sure that you installed CRFsuite (http://www.chokkan.org/software/crfsuite/)
CRFSUITE="$HOME/tools/crfsuite/crfsuite-0.12/example"

# convert conllX format
echo "convert ptb into conll format"
wget -N http://fileadmin.cs.lth.se/nlp/software/pennconverter/pennconverter.jar
echo "convert ptb-train (02-21)"
java -jar pennconverter.jar < ./treebank_3/wsj_split/wsj02-21.mrg > wsj02-21.conll
echo "convert ptb-dev (22)"
java -jar pennconverter.jar < ./treebank_3/wsj_split/wsj22.mrg > wsj22.conll
echo "convert ptb-test (23)"
java -jar pennconverter.jar < ./treebank_3/wsj_split/wsj23.mrg > wsj23.conll

# convert conll2000 format (for chunking)
echo "convert into conll2000 format (for chunking)"
echo "converting training data ..."
python2 ./chunker/convert_to_conll2000.py wsj02-21.conll > wsj02-21.cnl2000
echo "converting dev data ..."
python2 ./chunker/convert_to_conll2000.py wsj22.conll > wsj22.cnl2000
echo "converting test data ..."
python2 ./chunker/convert_to_conll2000.py wsj23.conll > wsj23.cnl2000

# get features
echo "extract features (for chunking)"
echo "extracting ptb-training features"
python2 $CRFSUITE/chunking.py < ./wsj02-21.cnl2000 > wsj02-21.feats
echo "extracting ptb-dev features"
python2 $CRFSUITE/chunking.py < ./wsj22.cnl2000 > wsj22.feats
echo "extracting ptb-test features"
python2 $CRFSUITE/chunking.py < ./wsj23.cnl2000 > wsj23.feats

# run chunker
echo "running chunker"
echo "chunking ptb-train"
crfsuite tag -m ./chunker/CoNLL2000.model wsj02-21.feats > wsj02-21.chunk
echo "chunking ptb-dev"
crfsuite tag -m ./chunker/CoNLL2000.model wsj22.feats > wsj22.chunk
echo "chunking ptb-test"
crfsuite tag -m ./chunker/CoNLL2000.model wsj23.feats > wsj23.chunk

# merge result
echo "creating train.E00"
python2 chunker/ptbwithchunk.py wsj02-21.conll wsj02-21.chunk > train.E00
echo "creating dev.E00"
python2 chunker/ptbwithchunk.py wsj22.conll wsj22.chunk > dev.E00
echo "creating test.E00"
python2 chunker/ptbwithchunk.py wsj23.conll wsj23.chunk > test.E00

# delete intermediate files
echo "delete intermediate files"
rm *.conll
rm *.cnl2000
rm *.feats
rm *.chunk

echo "preprocessing is done!"
