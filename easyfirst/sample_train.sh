#!/bin/bash

python train.py -o ./models/$1 -f features/znp.py --iters 20 --train_file ../data/train.$1 --gold_file ../data/train.E00
