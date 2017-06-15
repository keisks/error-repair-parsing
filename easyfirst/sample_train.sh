#!/bin/bash

~/local/bin/python train.py -o ./models/$1 -f features/znp.py --iters 10 ../data/train.$1 ../data/train.E00
