#!/bin/bash

python train.py -o ./models/$1 -f features/znp.py --iters 20 ../data/train.$1 ../data/train.E00
