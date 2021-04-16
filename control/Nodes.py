# coding=utf-8
from __future__ import print_function

import traceback , json

import kubernetes.client
from kubernetes import client
from kubernetes.client.rest import ApiException

import configure
from control.parse_error import Error
from pprint import pprint

from pcGroup.log.logUtil import logUtil
logutil = logUtil()
namespace = 'default' # str | object name and auth scope, such as for teams and projects
body = kubernetes.client.ExtensionsV1beta1Deployment() # ExtensionsV1beta1Deployment |
pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)
v1betaclient = configure.api_client('ctccluster').v1betaclient
v1client = configure.api_client('ctccluster').v1client

class nodes:
    @staticmethod
    def _list():
        try:
            ret = v1client.list_node( watch = False)
            print (ret)
            result = {}
            resultList = []
            for i in ret.items:
                result["name"] = i.metadata.name
                address=""
                for j in range(0,len(i.status.addresses)):
                    address = "<strong>type</strong>:%s,<strong>Adress</strong>%s | %s" %(str(i.status.addresses[j].type),str(i.status.addresses[j].address),address)
                    print( address)
                result["address"] = address
                result["allocatable"] = "<strong>cpu</strong>:%s,<strong>memory</strong>:%s,<strong>pods</strong>:%s" %(str(i.status.allocatable["cpu"]),str(i.status.allocatable["memory"]),str(i.status.allocatable["pods"]))
                capacityStr = "<strong>cpu</strong>:%s,<strong>memory</strong>:%s,<strong>pods</strong>:%s" %(str(i.status.capacity["cpu"]),str(i.status.capacity["memory"]),str(i.status.capacity["pods"]))
                result["capacity"] = capacityStr
                resultList.append(result)
                result = {}
            return json.dumps(resultList)
        except ApiException as e:
            logutil.errmsgStringIO(traceback , 'nodes list error')
            return Error(e).get_code()