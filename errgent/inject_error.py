#!/usr/bin/env python
#encoding: utf-8

import sys
import os
import random
import bisect
import json
import numpy as np
from pattern.en import pluralize, singularize
from pattern.en import conjugate, lemma, lexeme

BEVERB = ['am', 'are', 'is', 'was', 'were', 'be', 'being', 'been']
VTAGS = ['VB', 'VBP', 'VBZ', 'VBG', 'VBD', 'VBN']
DEBUG = False

class error_config():
    def __init__(self, error_type):
        self.ERROR_TYPES = [
                "sub_prep",
                "ins_prep",
                "del_prep",
                "sub_det",
                "ins_det",
                "del_det",
                "sub_nn",
                "sub_vform"
                ]
        assert error_type in self.ERROR_TYPES
        self.CONF_MATRIX = {}
        if error_type in ("sub_prep", "del_prep", "ins_prep"):
            self.CONF_MATRIX = json.load(open('./prepConfMat.json', 'r'))
        elif error_type in ("sub_det", "del_det", "ins_det"):
            self.CONF_MATRIX = None
        elif error_type == "sub_nn":
            self.CONF_MATRIX = "None"
        elif error_type == "sub_vform":
            self.CONF_MATRIX = None
        else:
            raise
            

def rand_sample(e_config, target):
    assert target in e_config.CONF_MATRIX.keys(), "{} is an incorrect target".format(target)
    distrib = e_config.CONF_MATRIX[target].values()
    candidates = e_config.CONF_MATRIX[target].keys()
    accumulated = np.add.accumulate(distrib)
    normalized = [float(x)/accumulated[-1] for x in accumulated]
    smpl = candidates[bisect.bisect(normalized, random.random())]
    return smpl.encode('utf-8')

def tokenize_blanks(fh):
    stack = []
    for line in fh:
       line = line.strip().split()
       if not line:
          if stack: yield stack
          stack = []
       else:
          stack.append(line)
    if stack: yield stack

def to_tok(line):
    if line[4]=="_": line[4]=line[3]
    return {"parent": int(line[-4]),
            "prel"  : line[-3],
            "form"  : line[1], 
            "lem"  : line[2], 
            "id"    : int(line[0]), 
            "tag"   : line[4],
            "ctag"   : line[3],
            "morph" : line[-5].split("|"),
            "extra" :  line[-1],
            }

def conll_to_sents(fh,ignore_errs=True):
    for sent in tokenize_blanks(fh):
        if ignore_errs and sent[0][0][0]=="@": continue
        yield [to_tok(l) for l in sent] 

def out_conll(sent,out=sys.stdout,parent='parent',form='form',prel='prel'): 
    for tok in sent:
        try:
            out.write("%s\n" % "\t".join(map(str, [tok['id'], tok[form], tok['lem'],tok['tag'],tok['tag'],"_",tok[parent],tok[prel],"_",tok.get('extra','_')])))
        except KeyError,e:
            print e
            print tok
            raise e
    out.write("\n") 

def set_parent_token(sent_i):
    for tok in sent_i:
        parent_idx = tok['parent']
        if parent_idx == 0:
            tok['extra'] = "#ROOT"
        else:
            parent_token = sent_i[parent_idx-1]['form']
            tok['extra'] = parent_token
    return sent_i

def inject_ins_det(sent_i, e_config):
    # get target indices
    target_indices = []
    for idx, w_i in enumerate(sent_i):
        tag = w_i['tag']
        form = w_i['form']
        chunk = w_i['lem']
        if ((chunk=="B-NP")
            and (tag in ("NN", "NNS", "JJ", "JJR", "JJS"))
            and (not form[0].isupper())
            and (sent_i[idx-1]['tag'] != "DT")
            and (idx>0)):
            target_indices.append(idx)

    # choose one and apply insertion
    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        definite = random.randint(0,1)

        new_token = sent_i[target_index].copy()
        if definite:
            new_token['form'] = 'the'
        else:
            if sent_i[target_index]['form'][0] in ('a', 'i', 'u', 'e', 'o', 'y'):
                new_token['form'] = 'an'
            else:
                new_token['form'] = 'a'

        new_token['tag'] = 'DT'
        new_token['ctag'] = 'DT'
        new_token['prel'] = 'NMOD'
        new_token['lem'] = 'B-NP'
        new_token['parent'] = new_token['id']+1
        new_token['extra'] = sent_i[target_index]['form']
        new_token['morph'] = "_"

        # update other indices in sent_i
        for w_i in sent_i:
            if w_i['id'] > target_index: # we don't have root, so we don't use >=
                w_i['id'] += 1
            if w_i['parent'] > target_index:
                w_i['parent'] += 1

        sent_i.insert(target_index, new_token)

    else:
        pass

    return  sent_i


def inject_del_det(sent_i, e_config):
    determiners = ['a', 'an', 'the']
    tags_i = [w_i['tag'] for w_i in sent_i]
    parents = [w_i['parent'] for w_i in sent_i]
    target_indices = []
    for idx, w_i in enumerate(sent_i):
        if w_i['tag'] == 'DT' and w_i['form'] in determiners and w_i['id'] not in parents:
            target_indices.append(idx)

    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        sent_i.pop(target_index)
        for w_i in sent_i:
            if w_i['id'] > target_index: # we don't have root, so we don't use >=
                w_i['id'] -= 1
            if w_i['parent'] > target_index:
                w_i['parent'] -= 1
    else:
        pass
    return sent_i


def inject_sub_det(sent_i, e_config):
    determiners = ['a', 'an', 'the']
    target_indices = []
    for i, w_i in enumerate(sent_i):
        if w_i['tag'] == 'DT' and w_i['form'] in determiners and i<len(sent_i)-1:
            target_indices.append(i)

    if target_indices:
        target_index = target_indices[random.randint(0, max(0, len(target_indices)-2))] # DT may not be at the end 
        target_token = sent_i[target_index]['form']
        if target_token == "the":
            next_token = sent_i[target_index+1]['form']
            if len(next_token) > 0 and next_token in ('a','i','u','e','o','y'):
                sent_i[target_index]['form'] = 'an'
            else:
                sent_i[target_index]['form'] = 'a'
        else:
            sent_i[target_index]['form'] = 'the'
    else:
        pass

    return sent_i


def inject_ins_prep(sent_i, e_config):
    # get target indices
    target_indices = []
    allowed_tags = ["NN", "NNS", "DT", "CD", "JJ", "JJR", "JJS", "NNP", "NNPS"]
    for idx, w_i in enumerate(sent_i):
        tag = w_i['tag']
        form = w_i['form']
        chunk = w_i['lem']
        if ((chunk=="B-NP") 
            and (tag in allowed_tags) 
            and (idx>0) 
            and (sent_i[idx-1]['tag']!="IN")
            and (sent_i[idx-1]['lem']!="B-PP")):
            target_indices.append(idx)

    # choose one and apply insertion
    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        preps = e_config.CONF_MATRIX.keys()
        new_prep = preps[random.randint(0, len(preps)-1)]

        new_token = sent_i[target_index].copy()
        new_token['form'] = new_prep
        new_token['tag'] = 'IN'
        new_token['ctag'] = 'IN'
        new_token['prel'] = 'PREP' #dummy
        new_token['lem'] = 'B-PP'
        new_token['parent'] = new_token['id']+1
        new_token['extra'] = sent_i[target_index]['form']
        new_token['morph'] = "_"

        # update other indices in sent_i
        for w_i in sent_i:
            if w_i['id'] > target_index: 
                w_i['id'] += 1
            if w_i['parent'] > target_index:
                w_i['parent'] += 1

        sent_i.insert(target_index, new_token)
    else:
        pass

    return  sent_i


def inject_del_prep(sent_i, e_config):

    tags_i = [w_i['tag'] for w_i in sent_i]
    parents = [w_i['parent'] for w_i in sent_i]
    target_indices = []
    for idx, w_i in enumerate(sent_i):
        if w_i['tag'] == 'IN' and w_i['form'] in e_config.CONF_MATRIX.keys() and w_i['id'] not in parents:
            target_indices.append(idx)

    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        sent_i.pop(target_index)
        for w_i in sent_i:
            if w_i['id'] > target_index:
                w_i['id'] -= 1
            if w_i['parent'] > target_index:
                w_i['parent'] -= 1
    else:
        pass
    return sent_i


def inject_sub_prep(sent_i, e_config):
    tags_i = [w_i['tag'] for w_i in sent_i]
    target_indices = [idx for idx, tag in enumerate(tags_i) if tag == "IN" and sent_i[idx]['form'] in e_config.CONF_MATRIX.keys()]
    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        target_token = sent_i[target_index]['form']
        new_token = rand_sample(e_config, target_token)
        sent_i[target_index]['form'] = new_token
    else:
        pass

    return sent_i

def inject_sub_nn(sent_i, e_config):
    target_indices = []
    for i, w_i in enumerate(sent_i):
        if w_i['tag'] in ('NN', 'NNS'):
            target_indices.append(i)
    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        target_token = sent_i[target_index]['form']
        target_tag = sent_i[target_index]['tag']

        new_token = ""
        new_tag = ""
        if target_tag == "NN":
            new_token = pluralize(target_token)
            new_tag = "NNS"
        elif target_tag == "NNS":
            new_token = singularize(target_token)
            new_tag = "NN"
        else:
            raise
        sent_i[target_index]['form'] = str(new_token)
        sent_i[target_index]['tag'] = new_tag
        sent_i[target_index]['ctag'] = new_tag
    else:
        pass
    return sent_i

def inject_sub_vform(sent_i, e_config=None):
    target_indices = []
    for i, w_i in enumerate(sent_i):
        if w_i['tag'].startswith("VB") and "'" not in w_i['form']:
            target_indices.append(i)
    if target_indices:
        target_index = target_indices[random.randint(0, len(target_indices)-1)]
        target_token = sent_i[target_index]['form']
        target_tag = sent_i[target_index]['tag']

        lem = target_token
        if target_tag != "VB":
            lem = lemma(target_token)

        new_token = ""
        cand_tags = VTAGS[:]
        cand_tags.pop(cand_tags.index(target_tag))
        new_tag = cand_tags[random.randint(0, len(cand_tags)-1)]

        if new_tag == "VB":
            new_token = lem
        elif new_tag == "VBP":
            new_token = conjugate(lem, '1sg')
        elif new_tag == "VBZ":
            new_token = conjugate(lem, '3sg')
        elif new_tag == "VBG":
            new_token = conjugate(lem, 'part')
        elif new_tag == "VBD":
            new_token = conjugate(lem, 'p')
        elif new_tag == "VBN":
            new_token = conjugate(lem, 'ppart')
        else:
            raise

        sent_i[target_index]['form'] = str(new_token)
        sent_i[target_index]['tag'] = new_tag
        sent_i[target_index]['ctag'] = new_tag
    else:
        pass
    return sent_i

def generate_specific_error(filepath, error_type):
    e_config = error_config(error_type)

    for sent_i in conll_to_sents(file(filepath)):
        # preprocessing: fill parent token into a column
        sent_i = set_parent_token(sent_i)
        if DEBUG:
            print "===== DEBUG mode ====="
            print " ".join([tok_i['form'] for tok_i in sent_i])

        if error_type == "sub_prep":
            sent_i = inject_sub_prep(sent_i, e_config)
        elif error_type == "del_prep":
            sent_i = inject_del_prep(sent_i, e_config)
        elif error_type == "ins_prep":
            sent_i = inject_ins_prep(sent_i, e_config)
        elif error_type == "sub_det":
            sent_i = inject_sub_det(sent_i, e_config)
        elif error_type == "del_det":
            sent_i = inject_del_det(sent_i, e_config)
        elif error_type == "ins_det":
            sent_i = inject_ins_det(sent_i, e_config)
        elif error_type == "sub_nn":
            sent_i = inject_sub_nn(sent_i, e_config)
        elif error_type == "sub_vform":
            sent_i = inject_sub_vform(sent_i, e_config)
        else:
            pass

        if DEBUG:
            print " ".join([tok_i['form'] for tok_i in sent_i])

        if not DEBUG:
            out_conll(sent_i)

    return

def generate_random_error(filepath, ratio):

    e_config_prep = error_config("sub_prep")
    e_config_nn = error_config("sub_nn")
    e_config_vform = error_config("sub_vform")
    e_config_det = error_config("sub_det")
    error_types = ["sub_prep", "del_prep", "ins_prep", "sub_det", "del_det", "ins_det", "sub_nn", "sub_vform"]

    for sent_i in conll_to_sents(file(filepath)):
        # preprocessing: fill parent token into a column
        sent_i = set_parent_token(sent_i)

        iternum = int(len(sent_i)*ratio/100)
        for q in range(iternum):
            et = error_types[random.randint(0,len(error_types)-1)]

            if et == "sub_prep":
                sent_i = inject_sub_prep(sent_i, e_config_prep)
            elif et == "del_prep":
                sent_i = inject_del_prep(sent_i, e_config_prep)
            elif et == "ins_prep":
                sent_i = inject_ins_prep(sent_i, e_config_prep)
            elif et == "sub_det":
                sent_i = inject_sub_det(sent_i, e_config_det)
            elif et == "del_det":
                sent_i = inject_del_det(sent_i, e_config_det)
            elif et == "ins_det":
                sent_i = inject_ins_det(sent_i, e_config_det)
            elif et == "sub_nn":
                sent_i = inject_sub_nn(sent_i, e_config_nn)
            elif et == "sub_vform":
                sent_i = inject_sub_vform(sent_i, e_config_vform)
            else:
                raise

        # sent to conll
        if not DEBUG:
            out_conll(sent_i)

    return


if __name__ == '__main__':
    generate_random_error(sys.argv[1], int(sys.argv[2])) # filepath and ratio
    #generate_specific_error(sys.argv[1], sys.argv[2])   # optional

