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

        privatedeploy = ExtensionsV1beta1Deployment(kind="Deployment", api_version="extensions/v1beta1",
                                                    metadata=V1ObjectMeta(labels=labels, name=name,
                                                                          namespace=k8sNamespace),
                                                    spec=ExtensionsV1beta1DeploymentSpec(strategy=deployUpdateAbout,
                                                                                         replicas=replicas,
                                                                                         revision_history_limit=3,
                                                                                         template=V1PodTemplateSpec(
                                                                                             spec=kubernetes.client.V1PodSpec(
                                                                                                 dns_config=V1PodDNSConfig(
                                                                                                     nameservers=[
                                                                                                         ""]),
                                                                                                 containers=[
                                                                                                     client.V1Container(
                                                                                                         lifecycle=V1Lifecycle(
                                                                                                             pre_stop=V1Handler(
                                                                                                                 _exec=V1ExecAction(
                                                                                                                     command=[
                                                                                                                         "/bin/sh",
                                                                                                                         "-c",
                                                                                                                         "/stopRegister.sh"]))),
                                                                                                         liveness_probe=V1Probe(
                                                                                                             http_get=V1HTTPGetAction(
                                                                                                                 path=healthUrl,
                                                                                                                 port=8080,
                                                                                                                 scheme="HTTP"),
                                                                                                             initial_delay_seconds=180,
                                                                                                             period_seconds=300,
                                                                                                             timeout_seconds=60),
                                                                                                         readiness_probe=V1Probe(
                                                                                                             http_get=V1HTTPGetAction(
                                                                                                                 path=healthUrl,
                                                                                                                 port=8080,
                                                                                                                 scheme="HTTP"),
                                                                                                             initial_delay_seconds=3,
                                                                                                             period_seconds=5,
                                                                                                             timeout_seconds=10),
                                                                                                         resources=V1ResourceRequirements(
                                                                                                             limits={
                                                                                                                 "cpu": cpunum,
                                                                                                                 "memory": "2500Mi"},
                                                                                                             requests={
                                                                                                                 "cpu": "0.3",
                                                                                                                 "memory": memnum + "Mi"}),
                                                                                                         name=name,
                                                                                                         image=image,
                                                                                                         ports=[
                                                                                                             client.V1ContainerPort(
                                                                                                                 container_port=port,
                                                                                                                 protocol="TCP")]),
                                                                                                     client.V1Container(
                                                                                                         name="k8s-probe-net",
                                                                                                         image_pull_policy="IfNotPresent",
                                                                                                         image="k8s-probe-net:1.0")]),
                                                                                             metadata=kubernetes.client.V1ObjectMeta(
                                                                                                 labels=labels,
                                                                                                 name=name))))
        publicdeploy = ExtensionsV1beta1Deployment(kind="Deployment", api_version="extensions/v1beta1",
                                                   metadata=V1ObjectMeta(labels=labels, name=name,
                                                                         namespace=k8sNamespace),
                                                   spec=ExtensionsV1beta1DeploymentSpec(replicas=replicas,
                                                                                        revision_history_limit=3,
                                                                                        template=V1PodTemplateSpec(
                                                                                            spec=kubernetes.client.V1PodSpec(
                                                                                                containers=[
                                                                                                    client.V1Container(
                                                                                                        lifecycle=V1Lifecycle(
                                                                                                            pre_stop=V1Handler(
                                                                                                                _exec=V1ExecAction(
                                                                                                                    command=[
                                                                                                                        "/bin/sh",
                                                                                                                        "-c",
                                                                                                                        "/stopRegister.sh"]))),
                                                                                                        liveness_probe=V1Probe(
                                                                                                            http_get=V1HTTPGetAction(
                                                                                                                path=healthUrl,
                                                                                                                port=8080,
                                                                                                                scheme="HTTP"),
                                                                                                            initial_delay_seconds=180,
                                                                                                            period_seconds=300,
                                                                                                            timeout_seconds=60),
                                                                                                        readiness_probe=V1Probe(
                                                                                                            http_get=V1HTTPGetAction(
                                                                                                                path=healthUrl,
                                                                                                                port=8080,
                                                                                                                scheme="HTTP"),
                                                                                                            initial_delay_seconds=3,
                                                                                                            period_seconds=5,
                                                                                                            timeout_seconds=10),
                                                                                                        resources=V1ResourceRequirements(
                                                                                                            limits={
                                                                                                                "cpu": cpunum,
                                                                                                                "memory": "2500Mi"},
                                                                                                            requests={
                                                                                                                "cpu": "0.3",
                                                                                                                "memory": memnum + "Mi"}),
                                                                                                        name=name,
                                                                                                        image=image,
                                                                                                        ports=[
                                                                                                            client.V1ContainerPort(
                                                                                                                container_port=port,
                                                                                                                protocol="TCP")]),
                                                                                                    client.V1Container(
                                                                                                        name="k8s-probe-net",
                                                                                                        image_pull_policy="IfNotPresent",
                                                                                                        image="172.20.2.193:5000/k8s-probe-net:1.0")
                                                                                                ]),
                                                                                            metadata=kubernetes.client.V1ObjectMeta(
                                                                                                labels=labels,
                                                                                                name=name))))
        testdeploy = ExtensionsV1beta1Deployment(kind="Deployment", api_version="extensions/v1beta1",
                                                 metadata=V1ObjectMeta(labels=labels, name=name,
                                                                       namespace=k8sNamespace),
                                                 spec=ExtensionsV1beta1DeploymentSpec(replicas=replicas,
                                                                                      revision_history_limit=0,
                                                                                      template=V1PodTemplateSpec(
                                                                                          spec=kubernetes.client.V1PodSpec(
                                                                                              dns_config=V1PodDNSConfig(
                                                                                                  nameservers=[
                                                                                                      ""]),
                                                                                              containers=[
                                                                                                  client.V1Container(
                                                                                                      lifecycle=V1Lifecycle(
                                                                                                          pre_stop=V1Handler(
                                                                                                              _exec=V1ExecAction(
                                                                                                                  command=[
                                                                                                                      "/bin/sh",
                                                                                                                      "-c",
                                                                                                                      "/stopRegister.sh"]))),
                                                                                                      liveness_probe=V1Probe(
                                                                                                          http_get=V1HTTPGetAction(
                                                                                                              path=healthUrl,
                                                                                                              port=8080,
                                                                                                              scheme="HTTP"),
                                                                                                          initial_delay_seconds=180,
                                                                                                          period_seconds=300,
                                                                                                          timeout_seconds=60),
                                                                                                      readiness_probe=V1Probe(
                                                                                                          http_get=V1HTTPGetAction(
                                                                                                              path=healthUrl,
                                                                                                              port=8080,
                                                                                                              scheme="HTTP"),
                                                                                                          initial_delay_seconds=3,
                                                                                                          period_seconds=5,
                                                                                                          timeout_seconds=10),
                                                                                                      resources=V1ResourceRequirements(
                                                                                                          limits={
                                                                                                              "cpu": cpunum,
                                                                                                              "memory": "2500Mi"},
                                                                                                          requests={
                                                                                                              "cpu": "0.3",
                                                                                                              "memory": memnum + "Mi"}),
                                                                                                      name=name,
                                                                                                      image=image,
                                                                                                      ports=[
                                                                                                          client.V1ContainerPort(
                                                                                                              container_port=port,
                                                                                                              protocol="TCP")]),
                                                                                                  client.V1Container(
                                                                                                      name="k8s-probe-net",
                                                                                                      image_pull_policy="IfNotPresent",
                                                                                                      image="k8s-probe-net:1.0")]),
                                                                                          metadata=kubernetes.client.V1ObjectMeta(
                                                                                              labels=labels,
                                                                                              name=name))))
        privatedeploy_ctc2 = V1Deployment(api_version='apps/v1', kind='Deployment',
                                          metadata=V1ObjectMeta(labels=labels, name=name, namespace=k8sNamespace),
                                          spec=V1DeploymentSpec(strategy=appsv1DeployUpdateAbout,
                                                                selector=V1LabelSelector(
                                                                    match_labels=labels
                                                                ),
                                                                replicas=replicas,
                                                                revision_history_limit=3,
                                                                template=V1PodTemplateSpec(
                                                                    spec=V1PodSpec(
                                                                        dns_config=V1PodDNSConfig(
                                                                            nameservers=[
                                                                                ""]),
                                                                        containers=[
                                                                            client.V1Container(
                                                                                lifecycle=V1Lifecycle(
                                                                                    pre_stop=V1Handler(
                                                                                        _exec=V1ExecAction(
                                                                                            command=[
                                                                                                "/bin/sh",
                                                                                                "-c",
                                                                                                "/stopRegister.sh"]))),
                                                                                liveness_probe=V1Probe(
                                                                                    http_get=V1HTTPGetAction(
                                                                                        path=healthUrl,
                                                                                        port=8080,
                                                                                        scheme="HTTP"),
                                                                                    initial_delay_seconds=180,
                                                                                    period_seconds=300,
                                                                                    timeout_seconds=60),
                                                                                readiness_probe=V1Probe(
                                                                                    http_get=V1HTTPGetAction(
                                                                                        path=healthUrl,
                                                                                        port=8080,
                                                                                        scheme="HTTP"),
                                                                                    initial_delay_seconds=3,
                                                                                    period_seconds=5,
                                                                                    timeout_seconds=10),
                                                                                resources=V1ResourceRequirements(
                                                                                    limits={
                                                                                        "cpu": cpunum,
                                                                                        "memory": "2500Mi"},
                                                                                    requests={
                                                                                        "cpu": "0.3",
                                                                                        "memory": memnum + "Mi"}),
                                                                                name=name,
                                                                                image=image,
                                                                                ports=[
                                                                                    client.V1ContainerPort(
                                                                                        container_port=port,
                                                                                        protocol="TCP")]),
                                                                            client.V1Container(
                                                                                name="k8s-probe-net",
                                                                                image_pull_policy="IfNotPresent",
                                                                                image="k8s-probe-net:1.0")]),
                                                                    metadata=V1ObjectMeta(
                                                                        labels=labels,
                                                                        name=name))))
        zxBase_labels = {
            "name": name,
            "app": name,
            'release': name,
        }
        publicdeployzxBase = V1Deployment(
            api_version="apps/v1",
            kind='Deployment',
            metadata=V1ObjectMeta(
                labels=zxBase_labels,
                name=name,
                namespace=k8sNamespace),
            spec=V1DeploymentSpec(
                replicas=replicas,
                selector=V1LabelSelector(
                    match_labels=zxBase_labels
                ),
                revision_history_limit=10,
                strategy=appsv1DeployUpdateAbout,
                template=V1PodTemplateSpec(
                    spec=V1PodSpec(
                        dns_config=V1PodDNSConfig(
                            nameservers=["10.96.0.10"],
                            options=[
                                V1PodDNSConfigOption(
                                    name="ndots",
                                    value="1"
                                ),
                                V1PodDNSConfigOption(
                                    name="edns0"
                                ),
                            ],
                            searches=["svc.cluster.local"]),
                        dns_policy=None,
                        containers=[
                            V1Container(
                                env=[
                                    V1EnvVar(
                                        name="config_env",
                                        value="prod")],
                                liveness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=180,
                                    period_seconds=300,
                                    timeout_seconds=60),
                                readiness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=3,
                                    period_seconds=5,
                                    timeout_seconds=10),
                                resources=V1ResourceRequirements(
                                    limits={
                                        "cpu": cpunum,
                                        "memory": "2500Mi"
                                    },
                                    requests={
                                        "cpu": "0.1",
                                        "memory": memnum + "Mi"
                                    }
                                ),
                                name=name,
                                image=image,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    V1ContainerPort(
                                        container_port=port,
                                        name="http",
                                        protocol="TCP"
                                    )
                                ],
                                volume_mounts=[
                                    V1VolumeMount(
                                        mount_path="/config",
                                        name="config-volume",
                                        read_only=True,
                                    ),
                                    V1VolumeMount(
                                        mount_path="/etc/localtime",
                                        name="host-time",
                                        read_only=True,
                                    ),
                                    V1VolumeMount(
                                        mount_path="/data/public_web/global_ssi",
                                        name="public-ssi-dir",
                                        read_only=True,
                                    )
                                ]
                            ),
                        ],
                        image_pull_secrets=[
                            V1LocalObjectReference(
                                name="74-82-image-login"
                            )
                        ],
                        volumes=[
                            V1Volume(
                                config_map=V1ConfigMapVolumeSource(
                                    default_mode=420,
                                    name="act-config-file"
                                ),
                                name="config-volume"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/etc/localtime",
                                    type=""
                                ),
                                name="host-time"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/nas/public_web/global_ssi",
                                    type=""
                                ),
                                name="public-ssi-dir"
                            ),
                        ]
                    ),
                    metadata=V1ObjectMeta(
                        labels=zxBase_labels
                    )
                )
            )
        )

        xiaofeipgc_labels = {
            "name": name,
            "app": name,
            "rdc-version": name,
            "version": name
        }
        publicdeployxiaofeipgc = V1Deployment(
            api_version="apps/v1",
            kind='Deployment',
            metadata=V1ObjectMeta(
                labels=xiaofeipgc_labels,
                name=name,
                namespace=k8sNamespace),
            spec=V1DeploymentSpec(
                replicas=replicas,
                selector=V1LabelSelector(
                    match_labels=xiaofeipgc_labels
                ),
                revision_history_limit=10,
                strategy=appsv1DeployUpdateAbout,
                template=V1PodTemplateSpec(
                    spec=V1PodSpec(
                        dns_policy="ClusterFirst",
                        containers=[
                            V1Container(
                                env=[
                                    V1EnvVar(
                                        name="PROJECT_NAME",
                                        value="search"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_CONF",
                                        value="/data/conf"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_APPLICATION",
                                        value="/data/application"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_ROOTDIR",
                                        value="/data/application"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_GLOBAL_SSI",
                                        value="/data/global_ssi"
                                    ),
                                ],
                                liveness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=180,
                                    period_seconds=300,
                                    timeout_seconds=60),
                                readiness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=3,
                                    period_seconds=5,
                                    timeout_seconds=10),
                                resources=V1ResourceRequirements(
                                    limits={
                                        "cpu": cpunum,
                                        "memory": "2500Mi"
                                    },
                                    requests={
                                        "cpu": "0.1",
                                        "memory": memnum + "Mi"
                                    }
                                ),
                                name=name,
                                image=image,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    V1ContainerPort(
                                        container_port=port,
                                        name="http",
                                        protocol="TCP"
                                    )
                                ],
                                volume_mounts=[
                                    # V1VolumeMount(
                                    #     mount_path="/data/conf",
                                    #     name="search",
                                    # ),
                                    V1VolumeMount(
                                        mount_path="/etc/localtime",
                                        name="host-time",
                                    ),
                                    V1VolumeMount(
                                        mount_path="/data/global_ssi",
                                        name="global-ssi",
                                    ),
                                    V1VolumeMount(
                                        mount_path="/data/pc-config",
                                        name="pc-config",
                                    ),
                                ]
                            ),
                        ],
                        image_pull_secrets=[
                            V1LocalObjectReference(
                                name="rdc-cluster-image-pull-sercret-registry.cn-shenzhen.aliyuncs.com"
                            )
                        ],
                        volumes=[
                            # V1Volume(
                            #     config_map=V1ConfigMapVolumeSource(
                            #         default_mode=420,
                            #         name="pcbaby-search"
                            #     ),
                            #     name="search"
                            # ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/etc/localtime",
                                    type=""
                                ),
                                name="host-time"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/data/public_web/global_ssi",
                                    type=""
                                ),
                                name="global-ssi"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/data/pc-config",
                                    type=""
                                ),
                                name="pc-config"
                            ),
                        ]
                    ),
                    metadata=V1ObjectMeta(
                        labels=xiaofeipgc_labels
                    )
                )
            )
        )

        try:
            logutil.infoMsg("clustername:" + Constant.platformCode(region))
            if Constant.platformCode(region) == "alicluster":
                deploymentbody = publicdeploy
                result = v1betaclient.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                                  pretty=True)
            elif Constant.platformCode(region) == "testcluster":
                deploymentbody = testdeploy
                result = v1betaclient.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                                  pretty=True)
            elif Constant.platformCode(region) == "ctccluster":
                deploymentbody = privatedeploy
                result = v1betaclient.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                                  pretty=True)

            elif Constant.platformCode(region) == "ctc2cluster":
                deploymentbody = privatedeploy_ctc2
                # print (deploymentbody)
                result = appsv1api.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                               pretty=True)

            elif Constant.platformCode(region) == ("zxBase" or "pcall"):
                deploymentbody = publicdeployzxBase
                # print(deploymentbody)
                result = appsv1api.create_namespaced_deployment_with_http_info(k8sNamespace, deploymentbody,
                                                                               pretty=True)

            elif Constant.platformCode(region) == "xiaofeipgck8s" or Constant.platformCode(region) == "xiaofeipgc":
                deploymentbody = publicdeployxiaofeipgc
                # print(deploymentbody)
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
        # print("mod_host:", v1client.api_client.configuration.host)
        # print(cluster.clustername)
        labels = {"name": name}

        deployUpdateAbout = ExtensionsV1beta1DeploymentStrategy(
            rolling_update=ExtensionsV1beta1RollingUpdateDeployment(max_surge="25%", max_unavailable="25%"))

        appsv1DeployUpdateAbout = AppsV1beta1DeploymentStrategy(
            rolling_update=AppsV1beta1RollingUpdateDeployment(max_surge="25%", max_unavailable="25%"),
            type="RollingUpdate")

        privatedeploy = ExtensionsV1beta1Deployment(kind="Deployment", api_version="extensions/v1beta1",
                                                    metadata=V1ObjectMeta(labels=labels, name=name,
                                                                          namespace=k8sNamespace),
                                                    spec=ExtensionsV1beta1DeploymentSpec(strategy=deployUpdateAbout,
                                                                                         replicas=replicas,
                                                                                         revision_history_limit=3,
                                                                                         template=V1PodTemplateSpec(
                                                                                             spec=kubernetes.client.V1PodSpec(
                                                                                                 dns_config=V1PodDNSConfig(
                                                                                                     nameservers=[
                                                                                                         ""]),
                                                                                                 containers=[
                                                                                                     client.V1Container(
                                                                                                         lifecycle=V1Lifecycle(
                                                                                                             pre_stop=V1Handler(
                                                                                                                 _exec=V1ExecAction(
                                                                                                                     command=[
                                                                                                                         "/bin/sh",
                                                                                                                         "-c",
                                                                                                                         "/stopRegister.sh"]))),
                                                                                                         liveness_probe=V1Probe(
                                                                                                             http_get=V1HTTPGetAction(
                                                                                                                 path=healthUrl,
                                                                                                                 port=8080,
                                                                                                                 scheme="HTTP"),
                                                                                                             initial_delay_seconds=180,
                                                                                                             period_seconds=300,
                                                                                                             timeout_seconds=60),
                                                                                                         readiness_probe=V1Probe(
                                                                                                             http_get=V1HTTPGetAction(
                                                                                                                 path=healthUrl,
                                                                                                                 port=8080,
                                                                                                                 scheme="HTTP"),
                                                                                                             initial_delay_seconds=3,
                                                                                                             period_seconds=5,
                                                                                                             timeout_seconds=10),
                                                                                                         resources=V1ResourceRequirements(
                                                                                                             limits={
                                                                                                                 "cpu": cpunum,
                                                                                                                 "memory": "2500Mi"},
                                                                                                             requests={
                                                                                                                 "cpu": "0.3",
                                                                                                                 "memory": memnum + "Mi"}),
                                                                                                         name=name,
                                                                                                         image=image,
                                                                                                         ports=[
                                                                                                             client.V1ContainerPort(
                                                                                                                 container_port=port,
                                                                                                                 protocol="TCP")]),
                                                                                                     client.V1Container(
                                                                                                         name="k8s-probe-net",
                                                                                                         image_pull_policy="IfNotPresent",
                                                                                                         image="k8s-probe-net:1.0")]),
                                                                                             metadata=kubernetes.client.V1ObjectMeta(
                                                                                                 labels=labels,
                                                                                                 name=name))))
        publicdeploy = ExtensionsV1beta1Deployment(kind="Deployment", api_version="extensions/v1beta1",
                                                   metadata=V1ObjectMeta(labels=labels, name=name,
                                                                         namespace=k8sNamespace),
                                                   spec=ExtensionsV1beta1DeploymentSpec(replicas=replicas,
                                                                                        revision_history_limit=3,
                                                                                        template=V1PodTemplateSpec(
                                                                                            spec=kubernetes.client.V1PodSpec(
                                                                                                containers=[
                                                                                                    client.V1Container(
                                                                                                        lifecycle=V1Lifecycle(
                                                                                                            pre_stop=V1Handler(
                                                                                                                _exec=V1ExecAction(
                                                                                                                    command=[
                                                                                                                        "/bin/sh",
                                                                                                                        "-c",
                                                                                                                        "/stopRegister.sh"]))),
                                                                                                        liveness_probe=V1Probe(
                                                                                                            http_get=V1HTTPGetAction(
                                                                                                                path=healthUrl,
                                                                                                                port=8080,
                                                                                                                scheme="HTTP"),
                                                                                                            initial_delay_seconds=180,
                                                                                                            period_seconds=300,
                                                                                                            timeout_seconds=60),
                                                                                                        readiness_probe=V1Probe(
                                                                                                            http_get=V1HTTPGetAction(
                                                                                                                path=healthUrl,
                                                                                                                port=8080,
                                                                                                                scheme="HTTP"),
                                                                                                            initial_delay_seconds=3,
                                                                                                            period_seconds=5,
                                                                                                            timeout_seconds=10),
                                                                                                        resources=V1ResourceRequirements(
                                                                                                            limits={
                                                                                                                "cpu": cpunum,
                                                                                                                "memory": "2500Mi"},
                                                                                                            requests={
                                                                                                                "cpu": "0.3",
                                                                                                                "memory": memnum + "Mi"}),
                                                                                                        name=name,
                                                                                                        image=image,
                                                                                                        ports=[
                                                                                                            client.V1ContainerPort(
                                                                                                                container_port=port,
                                                                                                                protocol="TCP")]),
                                                                                                    client.V1Container(
                                                                                                        name="k8s-probe-net",
                                                                                                        image_pull_policy="IfNotPresent",
                                                                                                        image="172.20.2.193:5000/k8s-probe-net:1.0")

                                                                                                ]),

                                                                                            metadata=kubernetes.client.V1ObjectMeta(
                                                                                                labels=labels,
                                                                                                name=name))))
        testdeploy = ExtensionsV1beta1Deployment(kind="Deployment", api_version="extensions/v1beta1",
                                                 metadata=V1ObjectMeta(labels=labels, name=name,
                                                                       namespace=k8sNamespace),
                                                 spec=ExtensionsV1beta1DeploymentSpec(replicas=replicas,
                                                                                      revision_history_limit=0,
                                                                                      template=V1PodTemplateSpec(
                                                                                          spec=kubernetes.client.V1PodSpec(
                                                                                              dns_config=V1PodDNSConfig(
                                                                                                  nameservers=[
                                                                                                      ""]),
                                                                                              containers=[
                                                                                                  client.V1Container(
                                                                                                      lifecycle=V1Lifecycle(
                                                                                                          pre_stop=V1Handler(
                                                                                                              _exec=V1ExecAction(
                                                                                                                  command=[
                                                                                                                      "/bin/sh",
                                                                                                                      "-c",
                                                                                                                      "/stopRegister.sh"]))),
                                                                                                      liveness_probe=V1Probe(
                                                                                                          http_get=V1HTTPGetAction(
                                                                                                              path=healthUrl,
                                                                                                              port=8080,
                                                                                                              scheme="HTTP"),
                                                                                                          initial_delay_seconds=180,
                                                                                                          period_seconds=300,
                                                                                                          timeout_seconds=60),
                                                                                                      readiness_probe=V1Probe(
                                                                                                          http_get=V1HTTPGetAction(
                                                                                                              path=healthUrl,
                                                                                                              port=8080,
                                                                                                              scheme="HTTP"),
                                                                                                          initial_delay_seconds=3,
                                                                                                          period_seconds=5,
                                                                                                          timeout_seconds=10),
                                                                                                      resources=V1ResourceRequirements(
                                                                                                          limits={
                                                                                                              "cpu": cpunum,
                                                                                                              "memory": "2500Mi"},
                                                                                                          requests={
                                                                                                              "cpu": "0.3",
                                                                                                              "memory": memnum + "Mi"}),
                                                                                                      name=name,
                                                                                                      image=image,
                                                                                                      ports=[
                                                                                                          client.V1ContainerPort(
                                                                                                              container_port=port,
                                                                                                              protocol="TCP")]),
                                                                                                  client.V1Container(
                                                                                                      name="k8s-probe-net",
                                                                                                      image_pull_policy="IfNotPresent",
                                                                                                      image="k8s-probe-net:1.0")]),
                                                                                          metadata=kubernetes.client.V1ObjectMeta(
                                                                                              labels=labels,
                                                                                              name=name))))
        privatedeploy_ctc2 = V1Deployment(api_version='apps/v1', kind='Deployment',
                                          metadata=V1ObjectMeta(labels=labels, name=name, namespace=k8sNamespace),
                                          spec=V1DeploymentSpec(strategy=appsv1DeployUpdateAbout,
                                                                selector=V1LabelSelector(
                                                                    match_labels=labels
                                                                ),
                                                                replicas=replicas,
                                                                revision_history_limit=3,
                                                                template=V1PodTemplateSpec(
                                                                    spec=V1PodSpec(
                                                                        dns_config=V1PodDNSConfig(
                                                                            nameservers=[
                                                                                ""]),
                                                                        containers=[
                                                                            client.V1Container(
                                                                                lifecycle=V1Lifecycle(
                                                                                    pre_stop=V1Handler(
                                                                                        _exec=V1ExecAction(
                                                                                            command=[
                                                                                                "/bin/sh",
                                                                                                "-c",
                                                                                                "/stopRegister.sh"]))),
                                                                                liveness_probe=V1Probe(
                                                                                    http_get=V1HTTPGetAction(
                                                                                        path=healthUrl,
                                                                                        port=8080,
                                                                                        scheme="HTTP"),
                                                                                    initial_delay_seconds=180,
                                                                                    period_seconds=300,
                                                                                    timeout_seconds=60),
                                                                                readiness_probe=V1Probe(
                                                                                    http_get=V1HTTPGetAction(
                                                                                        path=healthUrl,
                                                                                        port=8080,
                                                                                        scheme="HTTP"),
                                                                                    initial_delay_seconds=3,
                                                                                    period_seconds=5,
                                                                                    timeout_seconds=10),
                                                                                resources=V1ResourceRequirements(
                                                                                    limits={
                                                                                        "cpu": cpunum,
                                                                                        "memory": "2500Mi"},
                                                                                    requests={
                                                                                        "cpu": "0.3",
                                                                                        "memory": memnum + "Mi"}),
                                                                                name=name,
                                                                                image=image,
                                                                                ports=[
                                                                                    client.V1ContainerPort(
                                                                                        container_port=port,
                                                                                        protocol="TCP")]),
                                                                            client.V1Container(
                                                                                name="k8s-probe-net",
                                                                                image_pull_policy="IfNotPresent",
                                                                                image="k8s-probe-net:1.0")]),
                                                                    metadata=V1ObjectMeta(
                                                                        labels=labels,
                                                                        name=name))))
        zxBase_labels = {
            "name": name,
            "app": name,
            'release': name,
        }
        publicdeployzxBase = V1Deployment(
            api_version="apps/v1",
            kind='Deployment',
            metadata=V1ObjectMeta(
                labels=zxBase_labels,
                name=name,
                namespace=k8sNamespace),
            spec=V1DeploymentSpec(
                replicas=replicas,
                selector=V1LabelSelector(
                    match_labels=zxBase_labels
                ),
                revision_history_limit=10,
                strategy=appsv1DeployUpdateAbout,
                template=V1PodTemplateSpec(
                    spec=V1PodSpec(
                        dns_config=V1PodDNSConfig(
                            nameservers=["10.96.0.10"],
                            options=[
                                V1PodDNSConfigOption(
                                    name="ndots",
                                    value="1"
                                ),
                                V1PodDNSConfigOption(
                                    name="edns0"
                                ),
                            ],
                            searches=["svc.cluster.local"]),
                        dns_policy=None,
                        containers=[
                            V1Container(
                                env=[
                                    V1EnvVar(
                                        name="config_env",
                                        value="prod")],
                                liveness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=180,
                                    period_seconds=300,
                                    timeout_seconds=60),
                                readiness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=3,
                                    period_seconds=5,
                                    timeout_seconds=10),
                                resources=V1ResourceRequirements(
                                    limits={
                                        "cpu": cpunum,
                                        "memory": "2500Mi"
                                    },
                                    requests={
                                        "cpu": "0.1",
                                        "memory": memnum + "Mi"
                                    }
                                ),
                                name=name,
                                image=image,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    V1ContainerPort(
                                        container_port=port,
                                        name="http",
                                        protocol="TCP"
                                    )
                                ],
                                volume_mounts=[
                                    V1VolumeMount(
                                        mount_path="/config",
                                        name="config-volume",
                                        read_only=True,
                                    ),
                                    V1VolumeMount(
                                        mount_path="/etc/localtime",
                                        name="host-time",
                                        read_only=True,
                                    ),
                                    V1VolumeMount(
                                        mount_path="/data/public_web/global_ssi",
                                        name="public-ssi-dir",
                                        read_only=True,
                                    )
                                ]
                            ),
                        ],
                        image_pull_secrets=[
                            V1LocalObjectReference(
                                name="74-82-image-login"
                            )
                        ],
                        volumes=[
                            V1Volume(
                                config_map=V1ConfigMapVolumeSource(
                                    default_mode=420,
                                    name="act-config-file"
                                ),
                                name="config-volume"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/etc/localtime",
                                    type=""
                                ),
                                name="host-time"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/nas/public_web/global_ssi",
                                    type=""
                                ),
                                name="public-ssi-dir"
                            ),
                        ]
                    ),
                    metadata=V1ObjectMeta(
                        labels=zxBase_labels
                    )
                )
            )
        )

        xiaofeipgc_labels = {
            "name": name,
            "app": name,
            "rdc-version": name,
            "version": name
        }
        publicdeployxiaofeipgc = V1Deployment(
            api_version="apps/v1",
            kind='Deployment',
            metadata=V1ObjectMeta(
                labels=xiaofeipgc_labels,
                name=name,
                namespace=k8sNamespace),
            spec=V1DeploymentSpec(
                replicas=replicas,
                selector=V1LabelSelector(
                    match_labels=xiaofeipgc_labels
                ),
                revision_history_limit=10,
                strategy=appsv1DeployUpdateAbout,
                template=V1PodTemplateSpec(
                    spec=V1PodSpec(
                        dns_policy="ClusterFirst",
                        containers=[
                            V1Container(
                                env=[
                                    V1EnvVar(
                                        name="PROJECT_NAME",
                                        value="search"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_CONF",
                                        value="/data/conf"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_APPLICATION",
                                        value="/data/application"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_ROOTDIR",
                                        value="/data/application"
                                    ),
                                    V1EnvVar(
                                        name="PROJECT_GLOBAL_SSI",
                                        value="/data/global_ssi"
                                    ),
                                ],
                                liveness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=180,
                                    period_seconds=300,
                                    timeout_seconds=60),
                                readiness_probe=V1Probe(
                                    http_get=V1HTTPGetAction(
                                        path=healthUrl,
                                        port=8080,
                                        scheme="HTTP"),
                                    initial_delay_seconds=3,
                                    period_seconds=5,
                                    timeout_seconds=10),
                                resources=V1ResourceRequirements(
                                    limits={
                                        "cpu": cpunum,
                                        "memory": "2500Mi"
                                    },
                                    requests={
                                        "cpu": "0.1",
                                        "memory": memnum + "Mi"
                                    }
                                ),
                                name=name,
                                image=image,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    V1ContainerPort(
                                        container_port=port,
                                        name="http",
                                        protocol="TCP"
                                    )
                                ],
                                volume_mounts=[
                                    # V1VolumeMount(
                                    #     mount_path="/data/conf",
                                    #     name="search",
                                    # ),
                                    V1VolumeMount(
                                        mount_path="/etc/localtime",
                                        name="host-time",
                                    ),
                                    V1VolumeMount(
                                        mount_path="/data/global_ssi",
                                        name="global-ssi",
                                    ),
                                    V1VolumeMount(
                                        mount_path="/data/pc-config",
                                        name="pc-config",
                                    ),
                                ]
                            ),
                        ],
                        image_pull_secrets=[
                            V1LocalObjectReference(
                                name="rdc-cluster-image-pull-sercret-registry.cn-shenzhen.aliyuncs.com"
                            )
                        ],
                        volumes=[
                            # V1Volume(
                            #     config_map=V1ConfigMapVolumeSource(
                            #         default_mode=420,
                            #         name="pcbaby-search"
                            #     ),
                            #     name="search"
                            # ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/etc/localtime",
                                    type=""
                                ),
                                name="host-time"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/data/public_web/global_ssi",
                                    type=""
                                ),
                                name="global-ssi"
                            ),
                            V1Volume(
                                host_path=V1HostPathVolumeSource(
                                    path="/data/pc-config",
                                    type=""
                                ),
                                name="pc-config"
                            ),
                        ]
                    ),
                    metadata=V1ObjectMeta(
                        labels=xiaofeipgc_labels
                    )
                )
            )
        )

        try:
            logutil.infoMsg("clustername:" + Constant.platformCode(region))
            if Constant.platformCode(region) == "alicluster":
                deploymentbody = publicdeploy
                result = v1betaclient.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            elif Constant.platformCode(region) == "testcluster":
                deploymentbody = testdeploy
                result = v1betaclient.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            elif Constant.platformCode(region) == "ctccluster":
                deploymentbody = privatedeploy
                result = v1betaclient.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            elif Constant.platformCode(region) == "ctc2cluster":
                deploymentbody = privatedeploy_ctc2
                result = appsv1api.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            elif Constant.platformCode(region) == ("zxBase" or "pcall"):
                deploymentbody = publicdeployzxBase
                # print (deploymentbody)
                result = appsv1api.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

            elif Constant.platformCode(region) == "xiaofeipgck8s" or Constant.platformCode(region) == "xiaofeipgc":
                deploymentbody = publicdeployxiaofeipgc
                # print (deploymentbody)
                result = appsv1api.patch_namespaced_deployment_with_http_info(name, k8sNamespace, deploymentbody)

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
            if int(region) != (cluster1 or alicluster or testcluster or pcauto2020QA):
                result = appsv1api.read_namespaced_deployment(k8sNamespace, label_selector=label_selector)
            else:
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
            if int(region) != (cluster1 or alicluster or testcluster or pcauto2020QA):
                rev = appsv1api.read_namespaced_deployment(name, k8sNamespace)
            else:
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
            if int(region) != (cluster1 or alicluster or testcluster or pcauto2020QA):
                deployment_rev = appsv1api.read_namespaced_deployment_status(name, k8sNamespace)
            else:
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
        if int(region) != (cluster1 or alicluster or testcluster or pcauto2020QA):
            deploymentList = appsv1api.list_namespaced_deployment(k8sNamespace)
        else:
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
            # if int(region) == (ctc2cluster or zxBase or xiaofeipgck8s):
            if int(region) != (cluster1 or alicluster or testcluster or pcauto2020QA):
                rev = appsv1api.read_namespaced_deployment(name, k8sNamespace)
            else:
                rev = v1betaclient.read_namespaced_deployment(name, k8sNamespace)
            print(rev)
            availableReplicas = rev.status.availableReplicas
        except(ApiException, Exception) as e:
            logutil.infoMsg("deploy ArgMsg failed:" + str(name))
            traceback.print_exc()
        return availableReplicas
