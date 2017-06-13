#!/usr/bin/env python
#encoding: utf-8

## Copyright 2017 Keisuke Sakaguchi 
##
##    This is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This code is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this code.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

def tokenTemplate(id_tmp, form_tmp, pos_tmp):
    token_tmp = {
            "parent": id_tmp + 1,
            "prel"  : "DEP",
            "form"  : form_tmp,
            "lem"  : "",
            "id"    : id_tmp,
            "tag"   : pos_tmp,
            "ctag"   : pos_tmp,
            "morph" : 1,
            "extra" : None,
            }
    return token_tmp


def decrementToken(tmpDict, idx_bound):
    # create new dict otherwise it won't be changed
    newDict = tmpDict.copy()
    if newDict['id'] > idx_bound:
        newDict['id'] -= 1
    if newDict['parent'] > idx_bound:
        newDict['parent'] -= 1
    if 'pparent' in newDict.keys():
        if newDict['pparent'] > idx_bound:
            newDict['pparent'] -= 1
    return newDict

def incrementToken(tmpDict, idx_bound):
    
    newDict = dict(tmpDict)
    if newDict['id'] >= idx_bound:
        newDict['id'] += 1
    if newDict['parent'] >= idx_bound:
        newDict['parent'] += 1
    if 'pparent' in newDict.keys():
        if newDict['pparent'] >= idx_bound:
            newDict['pparent'] += 1
    return newDict


def getEditDist(seq1, seq2):
    #Constant Values
    ins_cost = 1 # insertion cost
    del_cost = 1 #deletion cost
    sub_cost = 1 #substitution cost

    if isinstance(seq1, str):
        seq1 = list(seq1)
    if isinstance(seq2, str):
        seq2 = list(seq2)

    seq1 = ['#'] + seq1
    seq2 = ['#'] + seq2
    
    dist_matrix = [[0 for j in range(len(seq1))] for i in range(len(seq2))]
    for i in range(len(seq1)):
        dist_matrix[0][i] = i
    for j in range(len(seq2)):
        dist_matrix[j][0] = j

    move_matrix = [[0 for j in range(len(seq1))] for i in range(len(seq2))]
    move_matrix[0][0] = '#'
    for i in range(1,len(seq1)):
        move_matrix[0][i] = "I"
    for j in range(1,len(seq2)):
        move_matrix[j][0] = "D"
   
    #calculate edit distance using DP
    for j in range(1, len(seq1)):
        for i in range(1, len(seq2)):
            # compute cost for insertion, deletion, and replace(substitution)
            cost1 = dist_matrix[i][j-1] + ins_cost
            cost2 = dist_matrix[i-1][j] + del_cost
            if seq1[j] == seq2[i]:
                cost3 = dist_matrix[i-1][j-1]
            else:
                cost3 = dist_matrix[i-1][j-1] + sub_cost

            # decide the move
            if cost3 <= cost2 and cost3 <= cost1:
                dist_matrix[i][j] = cost3
                move_matrix[i][j] = 'R'
            elif cost2 <= cost3 and cost2 <= cost1:
                dist_matrix[i][j] = cost2
                move_matrix[i][j] = "D"
            else:
                dist_matrix[i][j] = cost1
                move_matrix[i][j] = "I"
    

    # get operations
    j = len(seq1)-1
    i = len(seq2)-1
    prev_move = move_matrix[i][j]
    moves = [prev_move]
    while not (prev_move == "#"):
        if prev_move == "I": 
            prev_move = move_matrix[i][j-1]
            j -= 1
        elif prev_move == "D":
            prev_move = move_matrix[i-1][j]
            i -= 1
        elif prev_move == "R":
            prev_move = move_matrix[i-1][j-1]
            j -= 1
            i -= 1
        moves.append(prev_move)

    return dist_matrix[-1][-1], moves[::-1]


if __name__ == '__main__':
    pass
