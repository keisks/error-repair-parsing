#!/bin/bash

python conllx_to_conll09.py ../easyfirst/parsed/$1.$2.$3 > ./$1.$2.$3.tmp
python conllx_to_conll09.py ../data/$1.E00 > ./$1.gold.tmp

cd ./srleval/trunk/
python eval.py ../../$1.gold.tmp ../../$1.$2.$3.tmp
cd ../../

rm ./$1.$2.$3.tmp ./$1.gold.tmp
