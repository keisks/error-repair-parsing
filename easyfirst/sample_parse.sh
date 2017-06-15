#!/bin/bash

rm ./models/$2.model.bak
if [ ! -e ./models/$2.model.bak ]; then
  sed -i.bak -e "s/.\/models\///" ./models/$2.model
fi

~/local/bin/python parse.py -m ./models/$2.model ../data/$1.$3 > ./parsed/$1.$2.$3

