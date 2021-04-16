# coding=utf-8
from __future__ import print_function
import time
import traceback

import kubernetes.client
from kubernetes.client.rest import ApiException
from pprint import pprint

from control import configure
from control.parse_error import Error
from pcGroup.log.logUtil import logUtil
from pcGroup.util.requestUtil import logutil
logutil = logUtil()
v1betaclient = configure.api_client('ctccluster').v1betaclient
v1client = configure.api_client('ctccluster').v1client

#name = 'name_example' # str | name of the Endpoints
namespace = 'default' # str | object name and auth scope, such as for teams and projects
#pretty = 'true' # str | If 'true', then the output is pretty printed. (optional)
#exact = True # bool | Should the export be exact.  Exact export maintains cluster-specific fields like 'Namespace'. (optional)
#export = True # bool | Should this value be exported.  Export strips fields that a user can not specify. (optional)
class endpoint:
    @staticmethod
    def _get(name):
        data = {}
        try:
            result = v1client.read_namespaced_endpoints(name, namespace)
            ip_ready=result.subsets[0].addresses
            ip_not_ready=result.subsets[0].not_ready_addresses
            ready_list=[]
            for i in ip_ready:
                ready_list.append(i.ip)
            data['ready_ip']=ready_list
            not_ready_list=[]
            if ip_not_ready:
                for i in ip_not_ready:
                    not_ready_list.append(i.ip)
            data['not_ready_ip']=not_ready_list
            data['k8scode']=200
            return data

        except (ApiException,Exception) as e:
            logutil.infoMsg("endpoint get failed:"+name)
            return Error(e).get_code(data=data)