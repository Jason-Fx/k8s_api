import traceback
from pprint import pprint

import kubernetes
from kubernetes import client, config, watch
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1Service
from kubernetes.client import V1ServiceList
from kubernetes.client import V1ServicePort
from kubernetes.client import V1ServiceSpec
from kubernetes.client.rest import ApiException
from control import configure
from control.parse_error import Error
from pcGroup.log.logUtil import logUtil
from pcGroup.util.requestUtil import logutil

logutil = logUtil()
v1betaclient = configure.api_client('ctccluster').v1betaclient
v1client = configure.api_client('ctccluster').v1client


class services:
    @staticmethod
    def _add(name, port, k8sNamespace="default"):
        data = {}
        labels = {"name": name}
        try:
            # namespace = 'default'
            namespace = k8sNamespace
            result = v1client.create_namespaced_service_with_http_info(namespace,
                                                                       V1Service(api_version="v1", kind="Service",
                                                                                 metadata=V1ObjectMeta(name=name,
                                                                                                       labels=labels),
                                                                                 spec=V1ServiceSpec(selector=labels,
                                                                                                    ports=[
                                                                                                        V1ServicePort(
                                                                                                            protocol="TCP",
                                                                                                            port=port,
                                                                                                            target_port=port)])))
            data['k8scode'] = result[1]
            return data
        except (ApiException, Exception) as e:
            logutil.infoMsg("services create failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def _del(name, k8sNamespace="default"):
        data = {}
        try:
            namespace = 'default'
            namespace = k8sNamespace
            # result=v1client.delete_namespaced_service_with_http_info( name, namespace,kubernetes.client.V1DeleteOptions())
            result = v1client.delete_namespaced_service_with_http_info(name, namespace)
            data['k8scode'] = result[1]
            return data
        except (ApiException, Exception) as e:
            print e
            logutil.infoMsg("services delete failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def svc_ip(name, k8sNamespace="default"):
        data = {}
        data['ip'] = 'None'
        try:
            namespace = 'default'
            namespace = k8sNamespace
            result = v1client.read_namespaced_service_with_http_info(name, namespace, pretty=True, exact=True)
            ip = result[0].spec.cluster_ip
            port = result[0].spec.ports[0].port
            data['ip'] = ip + ":" + str(port)
            data['k8scode'] = 200
            return data
        except (ApiException, Exception) as e:
            logutil.infoMsg("service_ip get failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def svc_list(lType="noInfo", k8sNamespace="default"):
        data = {}
        svclist = []
        data['svclist'] = []
        try:
            # namespace = 'default'
            namespace = k8sNamespace
            result = v1client.list_namespaced_service(namespace)
            for i in result.items:
                if lType == "otherInfo":
                    if i.spec.type == "ClusterIP":
                        if i.metadata.name != "kubernetes":
                            resultDict = {}
                            resultDict["name"] = i.metadata.name
                            resultDict["type"] = "ClusterIP"
                            resultDict["clusterIP"] = i.spec.cluster_ip
                            resultDict["port"] = i.spec.ports[0].port
                            resultDict["protocol"] = i.spec.ports[0].protocol
                            svclist.append(resultDict)
                else:
                    svclist.append(i.metadata.name)
            data['svclist'] = svclist
            data['k8scode'] = 200
            return data
        except (ApiException, Exception) as e:
            logutil.infoMsg("service_list get failed:" + str(e))
            return Error(e).get_code(data=data)
