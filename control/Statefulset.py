# coding=utf-8
from __future__ import print_function
import json, sys
import kubernetes.client
from flask import Response
from kubernetes import client
from common import Constant
from common.Constant import *
from control import configure
from control.parse_error import Error
from pcGroup.log.logUtil import logUtil
import traceback
namespace = "default"
cluster = configure.api_client('ctccluster')
v1betaclient = cluster.v1betaclient

clustername = None
v1client = cluster.v1client
logutil = logUtil()

appsv1api = cluster.appsv1api

class statefulset:
    @staticmethod
    def getStatefulsetList(region = 1, k8sNamespace = "default"):
        statefulsetList = appsv1api.list_namespaced_stateful_set(k8sNamespace)
        retList = []
        for  statefulesetTmp in statefulsetList.items:
            retDict = {}
            retDict["name"] = statefulesetTmp.metadata.name
            retDict["k8sNamespace"] = k8sNamespace
            retList.append(retDict)
        return retList