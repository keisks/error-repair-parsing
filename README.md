# Error-repair Dependency Pasring for Ungrammatical Texts (ACL 2017)

[paper](http://cs.jhu.edu/~keisuke/paper/2017_error-repair.pdf)  [bibtex](http://cs.jhu.edu/~keisuke/paper/2017_error-repair.bib) 

- - -

## Instructions 

- N.B. For license restriction, we don't provide the original PTB in this repository.

0. Prerequisites 

   - This repository uses [git-lfs](https://git-lfs.github.com/).

   - The code depends on Python 2.7 (compiled with unicode=ucs2). 

   - Check if your python is compatible with the code.

         $ python --version
         Python 2.7.17
         $ python -c "import sys; print(sys.maxunicode)"
         65535 (If this is 1114111, then your python uses unicode=ucs4)

   - If your python is not compatible, you might want to build python from source.

         (for example)
         cd $HOME
         mkdir local
         mkdir temp
         cd ./temp
         wget https://www.python.org/ftp/python/2.7.17/Python-2.7.17.tgz
         tar zxvf Python-2.7.17.tgz
         cd Python-2.7.17
         ./configure --prefix=$HOME/local --enable-unicode=ucs2 --enable-loadable-sqlite-extensions
         make && make install
         export PATH=$HOME/local/bin:$PATH
         cd $HOME/temp
         curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
         python get-pip.py

   - Once you have a compatible python, install pre-requisite modules.

         pip install -r requirements.txt
     
     (You need to install `libmysqlclient-dev` and `libsqlite3-dev` (e.g., `sudo apt-get install libmysqlclient-dev libsqlite3-dev`)

1. Get Penn Treebank under data directory. 

        cd ./data
        ln -s PATH_TO_YOUR_PTB treebank_3

2. Download and Install [CRFsuite](http://www.chokkan.org/software/crfsuite/manual.html#idp8849147120) for preprocessing.

        [example for linux]
        cd ./data
        wget https://github.com/downloads/chokkan/crfsuite/crfsuite-0.12-x86_64.tar.gz
        wget https://github.com/downloads/chokkan/crfsuite/crfsuite-0.12.tar.gz
        tar zxvf crfsuite-0.12-x86_64.tar.gz
        tar zxvf crfsuite-0.12-.tar.gz

3. Set `CRFSUITE_UTIL` and `crfsuite` paths in `preproc.sh` and run the script.

        sh ./preproc.sh
        
   This creates `./data/[train|dev|test].E00` (i.e., Error rate = 0%)

4. Add noise by running errgent. See the readme file in the directory.

        cd ./errgent
        sh ./generate_train_dev_test.sh (for generating all the files needed)
        
        
    We assume that we have named the files as ./data/[train|dev|test].[E00|E05|E10|E15|E20].
    The file should look like the following. 

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

5. Set path for KenLM in [easyfirst.py](https://github.com/keisks/error-repair-parsing/blob/master/easyfirst/easyfirst.py#L37) 
  
   You can download pretraind LM by 
   
        wget http://cs.jhu.edu/~keisuke/shared/gigaword.kenlm
        
   If you want to train and use your own LM, please check `https://github.com/kpu/kenlm`.

6. Training a error-repair parser

        cd easyfirst
        (e.g.,) sh sample_train.sh E05 (training a model with 5% error-injected corpus)

7. Parsing sentences with the trained model 

        (e.g.,) sh sample_parse.sh dev E05 E10 (parse 10% error-injected dev set with a model trained on 5% error corpus)

8. Evaluation on parsing performance 

        cd ./eval
        wget https://storage.googleapis.com/google-code-archive-source/v2/code.google.com/srleval/source-archive.zip -O srleval.zip
        unzip srleval.zip
        cd ./eval/srleval/trunk/align
        make
        
        modify line 231 in ./eval/srleval/trunk/eval.py
        (from) for item in alignment.align(ref_words, hyp_words, command=os.path.dirname(__file__) + "/align/align"):
        (to)   for item in alignment.align(ref_words, hyp_words):
        
        run evaluation script
        cd  ./eval
        (e.g.,) sh evaluate.sh dev E05 E10 (evaluate 10% error-injected dev set with a model trained on 5% error corpus)

7. Evaluation on grammaticality improvement

  - See [Predicting Grammaticality on an Ordinal Scale](https://github.com/cnap/grammaticality-metrics/tree/master/heilman-et-al)


## Questions

 - Please e-mail to Keisuke Sakaguchi (keisuke[at]cs.jhu.edu).
