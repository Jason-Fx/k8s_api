#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
   共用常量
'''

cluster1 = 1
cluster2 = 2
cluster3 = 3


def platformCode(var):
    if var == None or var == "":
        return "cluster1"
    return {
        1: "cluster1",
        2: "cluster2",
        3: "cluster3",
    }.get(int(var), 'cluster1')
