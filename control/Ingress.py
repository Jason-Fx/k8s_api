# coding=utf-8

from flask import Response
from flask import json
from kubernetes.client import V1DeleteOptions
from kubernetes.client import V1ObjectMeta
# from kubernetes.client import V1beta1HTTPIngressPath
# from kubernetes.client import V1beta1HTTPIngressRuleValue
# from kubernetes.client import V1beta1Ingress
# from kubernetes.client import V1beta1IngressBackend
# from kubernetes.client import V1beta1IngressRule
# from kubernetes.client import V1beta1IngressSpec
from kubernetes.client import NetworkingV1beta1HTTPIngressPath as V1beta1HTTPIngressPath
from kubernetes.client import NetworkingV1beta1HTTPIngressRuleValue as V1beta1HTTPIngressRuleValue
from kubernetes.client import NetworkingV1beta1Ingress as V1beta1Ingress
from kubernetes.client import NetworkingV1beta1IngressBackend as V1beta1IngressBackend
from kubernetes.client import NetworkingV1beta1IngressRule as V1beta1IngressRule
from kubernetes.client import NetworkingV1beta1IngressSpec as V1beta1IngressSpec
from kubernetes.client.rest import ApiException

from control import configure
from control.parse_error import Error
from pcGroup.log.logUtil import logUtil
from pcGroup.util.requestUtil import logutil

namespace = 'default'  # str | object name and auth scope, such as for teams and projects
container = ''  # str | The container for which to stream logs. Defaults to only container if there is one container in the pod. (optional)
follow = False  # bool | Follow the log stream of the pod. Defaults to false. (optional)
# limit_bytes = 56 # int | If set, the number of bytes to read from the server before terminating the log output. This may not display a complete final line of logging, and may return slightly more or slightly less than the specified limit. (optional)
pretty = True  # str | If 'true', then the output is pretty printed. (optional)
previous = True  # bool | Return previous terminated container logs. Defaults to false. (optional)
# since_seconds = 56 # int | A relative time in seconds before the current time from which to show logs. If this value precedes the time a pod was started, only logs since the pod start will be returned. If this value is in the future, no logs will be returned. Only one of sinceSeconds or sinceTime may be specified. (optional)
# tail_lines = 56 # int | If set, the number of lines from the end of the logs to show. If not specified, logs are shown from the creation of the container or sinceSeconds or sinceTime (optional)
##full lines
timestamps = True  # bool | If true, add an RFC3339 or RFC3339Nano timestamp at the beginning of every line of log output. Defaults to false. (optional)
logutil = logUtil()
# v1betaclient = configure.api_client('ctccluster').v1betaclient
# v1client = configure.api_client('ctccluster').v1client

cluster = configure.api_client('ctccluster')
v1betaclient = cluster.v1betaclient
v1client = cluster.v1client


class ingress:
    @staticmethod
    def _add(datajson):
        print "create", datajson
        data = {}
        httppath = []
        data1 = {"mName": "jobname",
                 "mDomain": "ingresstest1.inm.com",
                 "mBackend": [{"svc_name": "pcloud-pclive-api", "svc_port": 8443, "path": "/dsf"},
                              {"svc_name": "pcloud-pclive-api", "svc_port": 8080, "path": "/"}]}

        name = datajson['mName']
        domainname = datajson['mDomain']
        labels = {"name": name}
        backend_data = datajson['mBackend']
        if len(backend_data) > 0:
            for i in backend_data:
                print i['path']
                httppath.append(V1beta1HTTPIngressPath(path=i['path'],
                                                       backend=V1beta1IngressBackend(service_name=i['svc_name'],
                                                                                     service_port=i['svc_port'])))
        if len(httppath) > 0:
            body = V1beta1Ingress(api_version="extensions/v1beta1", kind="Ingress",
                                  metadata=V1ObjectMeta(labels=labels, name=name),
                                  spec=V1beta1IngressSpec(
                                      rules=[V1beta1IngressRule(host=domainname, http=V1beta1HTTPIngressRuleValue(
                                          paths=httppath
                                      ))])
                                  )
        else:
            ##错误参数
            data['k8scode'] = 100
            logutil.infoMsg("Args avalibe", datajson)
            return Response(json.dumps(data), mimetype='application/json')
        try:
            api_response = v1betaclient.create_namespaced_ingress_with_http_info(namespace="default", body=body)
            # print api_response
            data['k8scode'] = 200
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException, Exception) as e:
            logutil.infoMsg("ingress add failed:" + str(name))
            logutil.infoMsg(str(e))
            print e
            return Error(e).get_code(data=data)

    @staticmethod
    def _replace(datajson):
        print "replace", datajson
        data = {}
        httppath = []
        data1 = {"mName": "jobname",
                 "mDomain": "ingresstest1.inm.com",
                 "mBackend": [{"svc_name": "pcloud-pclive-api", "svc_port": 8443, "path": "/dsf"},
                              {"svc_name": "pcloud-pclive-api", "svc_port": 8080, "path": "/"}]}

        name = datajson['mName']
        domainname = datajson['mDomain']
        labels = {"name": name}
        backend_data = datajson['mBackend']
        if len(backend_data) > 0:
            for i in backend_data:
                print i['path']
                httppath.append(V1beta1HTTPIngressPath(path=i['path'],
                                                       backend=V1beta1IngressBackend(service_name=i['svc_name'],
                                                                                     service_port=i['svc_port'])))
        if len(httppath) > 0:
            body = V1beta1Ingress(api_version="extensions/v1beta1", kind="Ingress",
                                  metadata=V1ObjectMeta(labels=labels, name=name),
                                  spec=V1beta1IngressSpec(
                                      rules=[V1beta1IngressRule(host=domainname, http=V1beta1HTTPIngressRuleValue(
                                          paths=httppath
                                      ))])
                                  )
        else:
            ##错误参数
            data['k8scode'] = 100
            return Response(json.dumps(data), mimetype='application/json')
        try:
            api_response = v1betaclient.replace_namespaced_ingress_with_http_info(name=name, namespace="default",
                                                                                  body=body)
            print api_response
            data['k8scode'] = 200
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException, Exception) as e:
            logutil.infoMsg("ingress add failed:" + str(name))
            logutil.infoMsg(str(e))
            return Error(e).get_code(data=data)

    @staticmethod
    def _get(mName):
        data = {}
        try:
            data['mName'] = ''
            data['mDomain'] = ''
            data['mBackend'] = ''
            ingress_info = v1betaclient.read_namespaced_ingress(mName, "default")
            print ingress_info
            data['mName'] = ingress_info.metadata.name
            data['mDomain'] = ingress_info.spec.rules[0].host
            if len(ingress_info.spec.rules[0].http.paths) > 1:
                dict = []
                for paths in ingress_info.spec.rules[0].http.paths:
                    data1 = {}
                    data1['svc_name'] = paths.backend.service_name
                    data1['svc_port'] = paths.backend.service_port
                    data1['path'] = paths.path
                    dict.append(data1)
                # if len(ingress_info.spec.rules[0].http.paths) < 1:
                #     dict = []
                #     data2 = {}
                #     data2['svc_name'] = ingress_info.spec.rules[0].http.paths[0].backend.service_name
                #     data2['svc_port'] = ingress_info.spec.rules[0].http.paths[0].backend.service_port
                #     data2['path'] = ingress_info.spec.rules[0].http.paths[0].path
                #     dict.append(data2)
                data['mBackend'] = dict
            data['k8scode'] = 200
            print(json.dumps(data))
            return Response(json.dumps(data), mimetype='application/json')
        except Exception as e:
            logutil.infoMsg("ingress get error" + str(e))
            return Error(e).getcode(data={})

    @staticmethod
    def _list(k8sNamespace = "default"):
        listdata = []
        respone_data = {}
        try:
            api_response = v1betaclient.list_namespaced_ingress(k8sNamespace)
            print api_response
            for i in api_response.items:
                data = {}
                data['mName'] = ''
                data['mDomain'] = ''
                data['mBackend'] = ''
                data['mName'] = i.metadata.name
                data['mDomain'] = i.spec.rules[0].host
                if len(i.spec.rules[0].http.paths) > 0:
                    dict = []
                    for paths in i.spec.rules[0].http.paths:
                        data1 = {}
                        data1['svc_name'] = paths.backend.service_name
                        data1['svc_port'] = paths.backend.service_port
                        data1['path'] = paths.path
                        dict.append(data1)
                if len(i.spec.rules[0].http.paths) < 0:
                    dict = []
                    data2 = {}
                    data2['svc_name'] = i.spec.rules[0].http.paths[0].backend.service_name
                    data2['svc_port'] = i.spec.rules[0].http.paths[0].backend.service_port
                    data2['path'] = i.spec.rules[0].http.paths[0].path
                    dict.append(data2)
                data['mBackend'] = dict
                listdata.append(data)
            respone_data['k8scode'] = 200
            respone_data['ingress_list'] = listdata
            print(json.dumps(data))
            return Response(json.dumps(respone_data), mimetype='application/json')
        except ApiException as e:
            logutil.infoMsg("ingress list error" + str(e))
            return Error(e).get_code(data=respone_data)

    @staticmethod
    def _del(mName):
        data = {}
        try:
            result = v1betaclient.delete_namespaced_ingress_with_http_info(mName, "default")
            data['k8scode'] = 200
            return Response(json.dumps(data), mimetype='application/json')
        except ApiException as e:
            logutil.infoMsg("ingress del fail" + str(e))
            return Error(e).get_code(data=data)
