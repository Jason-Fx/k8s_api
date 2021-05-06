# coding=utf-8
from __future__ import print_function
import json, sys
import kubernetes.client
from flask import Response
from kubernetes import client
from kubernetes.client import ExtensionsV1beta1Deployment, AppsV1beta1DeploymentStrategy, \
    AppsV1beta1RollingUpdateDeployment, V1Deployment, V1DeploymentSpec, V1LabelSelector, V1PodSpec, \
    V1DeploymentStrategy, V1RollingUpdateDeployment, V1PodDNSConfigOption, V1Container, V1EnvVar, V1ContainerPort, \
    V1VolumeMount, V1LocalObjectReference, V1Volume, V1ConfigMapVolumeSource, V1HostPathVolumeSource
from kubernetes.client import ExtensionsV1beta1DeploymentSpec, ExtensionsV1beta1DeploymentStrategy, \
    ExtensionsV1beta1RollingUpdateDeployment
from kubernetes.client import V1ExecAction
from kubernetes.client import V1Handler
from kubernetes.client import V1Lifecycle
from kubernetes.client import V1Probe
from kubernetes.client import V1HTTPGetAction
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1PodTemplateSpec
from kubernetes.client import V1PodDNSConfig
from kubernetes.client import V1ResourceRequirements
from kubernetes.client.rest import ApiException
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


class deployment:
    @staticmethod
    def _add(name, replicas, port, image, cpunum, memnum, healthUrl, region=1, k8sNamespace="default"):
        if cpunum == None:
            cpunum = 2
        data = {}
        labels = {"name": name}
        deployUpdateAbout = ExtensionsV1beta1DeploymentStrategy(
            rolling_update=ExtensionsV1beta1RollingUpdateDeployment(max_surge="25%", max_unavailable="25%"))

        appsv1DeployUpdateAbout = AppsV1beta1DeploymentStrategy(
            rolling_update=AppsV1beta1RollingUpdateDeployment(max_surge="25%", max_unavailable="25%"),
            type="RollingUpdate")

        testdeploy = ExtensionsV1beta1Deployment()
        privatedeploy_ctc2 = V1Deployment()

        try:
            logutil.infoMsg("clustername:" + Constant.platformCode(region))
            if Constant.platformCode(region) == "cluster1":
                deploymentbody = testdeploy
                result = v1betaclient.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                                  pretty=True)
            elif Constant.platformCode(region) == "cluster2":
                deploymentbody = privatedeploy_ctc2
                # print (deploymentbody)
                result = appsv1api.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                               pretty=True)
            data['k8scode'] = result[1]
            # print (json.dumps(data))
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException, Exception) as e:
            logutil.infoMsg("deploy create failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def _update(name, replicas, port, image, cpunum, memnum, healthUrl, region=1, k8sNamespace="default"):
        if cpunum == None:
            cpunum = 2
        labels = {"name": name}
        deployUpdateAbout = ExtensionsV1beta1DeploymentStrategy(
            rolling_update=ExtensionsV1beta1RollingUpdateDeployment(max_surge="25%", max_unavailable="25%"))
        appsv1DeployUpdateAbout = AppsV1beta1DeploymentStrategy(
            rolling_update=AppsV1beta1RollingUpdateDeployment(max_surge="25%", max_unavailable="25%"),
            type="RollingUpdate")

        testdeploy = ExtensionsV1beta1Deployment()
        privatedeploy_ctc2 = V1Deployment()
        try:
            logutil.infoMsg("clustername:" + Constant.platformCode(region))
            if Constant.platformCode(region) == "cluster1":
                deploymentbody = testdeploy
                result = v1betaclient.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            elif Constant.platformCode(region) == "cluster2":
                deploymentbody = privatedeploy_ctc2
                result = v1betaclient.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            data = {}
            # print(deploymentbody, result)
            data['k8scode'] = result[1]
            # print(json.dumps(data))
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException, Exception) as e:
            # logutil.errmsgStringIO(e,"update deployment Error")
            logutil.infoMsg("deploy update failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def _del(name, k8sNamespace="default"):
        data = {}
        try:
            result = appsv1api.delete_namespaced_deployment_with_http_info(name, k8sNamespace)
            data['k8scode'] = result[1]
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException, Exception) as e:
            logutil.infoMsg("deploy del failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def _get_deployment_num(name, region=cluster1, k8sNamespace="default"):
        deployment_num = None
        label_selector = "name=" + name
        try:
            # if int(region) == (ctc2cluster or zxBase or xiaofeipgck8s):
            result = v1betaclient.list_namespaced_deployment(k8sNamespace, label_selector=label_selector)
            deployment_num = len(result.items)
        except (ApiException, Exception) as e:
            logutil.infoMsg("deploy status failed:" + name)
            return deployment_num
        return deployment_num

    @staticmethod
    def _get_deployment_info(name, region=cluster1, k8sNamespace="default"):
        data = {}
        data['jobName'] = 'None'
        data['imageName'] = 'None'
        data['replicas'] = 'None'
        data['cpuType'] = 'None'
        data['memNum'] = 'None'
        data['k8scode'] = 500  ###default error code
        print(cluster.clustername)
        try:
            # if int(region) == (ctc2cluster or zxBase or xiaofeipgck8s):
            rev = v1betaclient.read_namespaced_deployment(name, k8sNamespace)
            # print(rev.spec.template.spec.containers[0].image)
            print(rev)
            data['jobName'] = rev.metadata.name
            data['imageName'] = rev.spec.template.spec.containers[0].image
            data['replicas'] = rev.spec.replicas
            try:
                data['cpuType'] = rev.spec.template.spec.containers[0].resources.limits["cpu"]
            except:
                data['cpuType'] = 'None'
                traceback.print_exc()
            try:
                memNum = rev.spec.template.spec.containers[0].resources.requests["memory"]
                data['memNum'] = str(memNum).replace("Mi", "")
            except:
                data['memNum'] = 'None'
            '''旧代码获取cpu和mem
            try:
                if rev.spec.template.spec.containers[0].resources.limits:
                    data['cpuType'] = rev.spec.template.spec.containers[0].resources['cpu']
                if rev.spec.template.spec.containers[0].resources.requests:
                    data['memNum'] = rev.spec.template.spec.containers[0].resources.requests['memory']
            except:
                data['cpuType'] = 'None'
                data['memNum'] = 'None'
            '''
            data['k8scode'] = 200
            print(json.dumps(data))
            return Response(json.dumps(data), mimetype='application/json')
        except (ApiException, Exception) as e:
            logutil.infoMsg("deploy ArgMsg failed:" + name)
            return Error(e).get_code(data=data)

    @staticmethod
    def _get_update_status(name, region=cluster1, k8sNamespace="default"):
        labels = "name=" + name
        data = {}
        data['updated_rep'] = 0
        data['dep_rep'] = 0
        data['state'] = 0
        try:
            # if int(region) == (ctc2cluster or zxBase or xiaofeipgck8s):
            deployment_rev = v1betaclient.read_namespaced_deployment_status(name, k8sNamespace)
            data['updated_rep'] = deployment_rev.status.updated_replicas
            data['dep_rep'] = deployment_rev.spec.replicas
            pod_rev = v1client.list_namespaced_pod("default", label_selector=labels)
            for i in pod_rev.items:
                if i.status.container_statuses[0].state.waiting:
                    if i.status.container_statuses[0].state.waiting.reason == 'CrashLoopBackOff':
                        data['state'] = 1
                    elif i.status.container_statuses[0].state.waiting.reason == 'ContainerCreating':
                        pass
                    else:
                        data['state'] = 2
            data['k8scode'] = 200
            # print (json.dumps(data))
            return Response(json.dumps(data), mimetype='application/json')
        except Exception as e:
            logutil.infoMsg("get_update_status failed:" + name)
            data['state'] = 2
            return Error(e).get_code(data=data)

    @staticmethod
    def getDeploymentList(region, k8sNamespace="default"):
        deploymentList = ""
        # if int(region) == (ctc2cluster or zxBase or xiaofeipgck8s):
        deploymentList = v1betaclient.list_namespaced_deployment(k8sNamespace)
        retList = []
        for deploymentTmp in deploymentList.items:
            retDict = {}
            retDict["name"] = deploymentTmp.metadata.name
            retDict["k8sNamespace"] = k8sNamespace
            retList.append(retDict)
        return retList

    @staticmethod
    def getAvailableReplicas(name, region=cluster1, k8sNamespace="default"):
        availableReplicas = -1
        try:
            rev = v1betaclient.read_namespaced_deployment(name, k8sNamespace)
            print(rev)
            availableReplicas = rev.status.availableReplicas
        except(ApiException, Exception) as e:
            logutil.infoMsg("deploy ArgMsg failed:" + str(name))
            traceback.print_exc()
        return availableReplicas
