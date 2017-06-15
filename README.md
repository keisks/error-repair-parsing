# Error-repair Dependency Pasring for Ungrammatical Texts (ACL 2017)

Last updated: June, 2017

[link to the paper](#)

- - -

## Instructions 

N.B. For license restriction, we don't provide the original PTB in this repository.

1. Download Penn Treebank under data directory.
2. Convert PTB into CoNLL format (e.g., [Penn2Malt](https://stp.lingfil.uu.se/~nivre/research/Penn2Malt.html))
3. Put the CoNLL format file as ./data/[train|dev|test].E00  (i.e., Error rate = 0%)

4. Add noise by running errgent. See the readme file in the directory.
        sh ./generate_train_dev_test.sh (for generating all the files needed)

The file should look like the following. We assume that we have named the files as ./data/[train|dev|test].[E00|E05|E10|E15|E20].

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

4. training a model

        e.g., sh sample_train.sh E05 (training a model with 5% error-injected corpus)

5. parsing sentences with the trained model 

        e.g., sh sample_parse.sh dev E05 E10 (parse 10% error-injected dev set with a model trained on 5% error corpus)

6. evaluation on parsing performance 

[srleval](https://code.google.com/archive/p/srleval/source/default/source)

        cd ./eval/srleval/trunk/align
        make

        modify line 231 in ./eval/srleval/trunk/eval.py
        (from) for item in alignment.align(ref_words, hyp_words, command=os.path.dirname(__file__) + "/align/align"):
        (to)   for item in alignment.align(ref_words, hyp_words):

        run evaluation script
        e.g., sh evaluate.sh dev E05 E10 (evaluate 10% error-injected dev set with a model trained on 5% error corpus)

7. evaluation on grammaticality improvement

[Predicting Grammaticality on an Ordinal Scale](https://github.com/cnap/grammaticality-metrics/tree/master/heilman-et-al)

### run 


## Reference
Under construction

## Questions

 - Please e-mail to Keisuke Sakaguchi (keisuke[at]cs.jhu.edu).
