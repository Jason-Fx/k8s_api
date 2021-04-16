# coding=utf-8
from __future__ import print_function

import kubernetes.client
import configure , json
from control.parse_error import Error
import traceback , json
from kubernetes.client.rest import ApiException

from pcGroup.log.logUtil import logUtil
logutil = logUtil()
namespace = 'default' # str | object name and auth scope, such as for teams and projects
body = kubernetes.client.ExtensionsV1beta1Deployment() # ExtensionsV1beta1Deployment |
pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)
v1betaclient = configure.api_client('ctccluster').v1betaclient
v1client = configure.api_client('ctccluster').v1client

class k8sNamespace:
    @staticmethod
    def _list():
        try:
            api_response = v1client.list_namespace(timeout_seconds=30, watch=False)
            k8sNamespace = []
            for  namespace in api_response.items:
                k8sNamespace.append(namespace.metadata.name)
            return k8sNamespace
        except ApiException as e:
            logutil.errmsgStringIO(traceback , 'nodes list error')
            return Error(e).get_code()