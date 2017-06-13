# Error-repair Dependency Pasring for Ungrammatical Texts (ACL 2017)

Last updated: June, 2017

[link to the paper](#)

- - -

## Instructions 

Under construction

(For license restriction, we don't provide the original PTB in this repository.)


1. Download Penn Treebank under data directory.
2. Convert PTB into CoNLL format (e.g., [Penn2Malt](https://stp.lingfil.uu.se/~nivre/research/Penn2Malt.html))
3. Add noise by running errgent (see readme file in the directory.)

The file should look like 

1       Ms.     B-NP    NNP     _       _       2       TITLE   _       _
2       Haag    I-NP    NNP     _       _       3       SBJ     _       _
3       plays   B-VP    VBZ     _       _       0       ROOT    _       _
4       Elianti B-NP    NNP     _       _       3       OBJ     _       _
5       .       O       .       _       _       3       P       _       _

1       The     B-NP    DT      _       _       4       NMOD    _       _
2       luxury  I-NP    NN      _       _       4       NMOD    _       _
3       auto    I-NP    NN      _       _       4       NMOD    _       _
4       maker   I-NP    NN      _       _       7       SBJ     _       _
5       last    B-NP    JJ      _       _       6       NMOD    _       _
6       year    I-NP    NN      _       _       7       TMP     _       _
7       sold    B-VP    VBD     _       _       0       ROOT    _       _
8       1,214   B-NP    CD      _       _       9       NMOD    _       _
9       cars    I-NP    NNS     _       _       7       OBJ     _       _
10      in      B-PP    IN      _       _       7       LOC     _       _
11      the     B-NP    DT      _       _       12      NMOD    _       _
12      U.S.    I-NP    NNP     _       _       10      PMOD    _       _

...

4. specify your Kenlm path in line 37 in easyfirst.py
4. run training
5.

### run 


## Reference
Under construction

## Questions

 - Please e-mail to Keisuke Sakaguchi (keisuke[at]cs.jhu.edu).
