# coding=utf-8
import ssl
import traceback

from flask import Response
from flask import json
from kubernetes.client.rest import ApiException

from control import configure
from control.parse_error import Error
from pcGroup.log.logUtil import logUtil
from pcGroup.util.requestUtil import logutil

namespace = 'default' # str | object name and auth scope, such as for teams and projects
container = '' # str | The container for which to stream logs. Defaults to only container if there is one container in the pod. (optional)
follow = False # bool | Follow the log stream of the pod. Defaults to false. (optional)
#limit_bytes = 56 # int | If set, the number of bytes to read from the server before terminating the log output. This may not display a complete final line of logging, and may return slightly more or slightly less than the specified limit. (optional)
pretty = True # str | If 'true', then the output is pretty printed. (optional)
#previous = True # bool | Return previous terminated container logs. Defaults to false. (optional)
since_seconds = 3600 # int | A relative time in seconds before the current time from which to show logs. If this value precedes the time a pod was started, only logs since the pod start will be returned. If this value is in the future, no logs will be returned. Only one of sinceSeconds or sinceTime may be specified. (optional)
tail_lines = 100 # int | If set, the number of lines from the end of the logs to show. If not specified, logs are shown from the creation of the container or sinceSeconds or sinceTime (optional)
##full lines
timestamps = True # bool | If true, add an RFC3339 or RFC3339Nano timestamp at the beginning of every line of log output. Defaults to false. (optional)
logutil = logUtil()
v1betaclient = configure.api_client('ctccluster').v1betaclient
v1client = configure.api_client('ctccluster').v1client
class podlogs:
    @staticmethod
    def get_pods_log(podname,jobname,previous=None,type=None,tailline=None):
        print(previous)
        if int(previous)==0:
            ##True old
            a=True
        elif int(previous)==1:
            ##false now
            a=False
        data = {}
        data['logmessage']='null'
        try:
            if type == "test":
                api_response = v1client.read_namespaced_pod_log(podname, namespace, tail_lines=tailline, #limit_bytes=limit_bytes,
                                                                     previous=a,pretty=pretty # since_seconds=since_seconds,
                                                                     # timestamps=timestamps
                                                            )
            if type == "product":
                api_response = v1client.read_namespaced_pod_log(podname, namespace, container=jobname, tail_lines=tailline,#limit_bytes=limit_bytes,
                                                                     previous=a,pretty=pretty #since_seconds=since_seconds,
                                                                     # timestamps=timestamps
                                                                )

            data['logmessage']=api_response
            data['k8scode']=200
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException,Exception) as e:
            logutil.infoMsg("pods get_logs failed:"+podname)
            logutil.infoMsg("get_pods_log: %s,%s,%s,%s"  %(jobname,podname,str(previous),str(type)))
            logutil.infoMsg(str(e))
            print e
            return Error(e).get_code(data=data)


if __name__ == '__main__':
    #print podlogs.get_pods_log("in-gw-test-5f5d5d4c57-5blgw").get_data()
    print ssl.OPENSSL_VERSION
    print configure.api_client().v1betaclient.list_deployment_for_all_namespaces()