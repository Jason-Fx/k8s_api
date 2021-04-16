# coding=utf-8
import ConfigParser
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import traceback
import kubernetes

from kubernetes import config

from pcGroup.log.logUtil import logUtil
from pcGroup.util.requestUtil import logutil

local_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cp = ConfigParser.SafeConfigParser()
mainConf = local_path + "/conf/main.conf"


# 检查配置文件
def check_config():
    if os.access(mainConf, os.F_OK):
        pass
    else:
        print("mainConf not found:" + mainConf)
        sys.exit()

    cp.read(mainConf)
    try:
        project_dir = cp.get("project", "root")
        ##cluster list
        ##regionlist=cp.options('k8sconfig')
        cp.get("Queue", "servers")
    except Exception as e:
        # print("Error :"+e)
        traceback.print_exc()
        sys.exit()
    project_dir = project_dir
    host = cp.get("Queue", "servers")
    return project_dir, host


project_dir = check_config()[0]
host = check_config()[1]

logutil = logUtil()


class api_client():
    def __init__(self, cluster):
        config_file = cp.get("k8sconfig", cluster)
        self.clustername = cluster
        self.config_file = config_file
        self.Loadconfig()
        self.v1betaclient = kubernetes.client.ExtensionsV1beta1Api()
        self.v1client = kubernetes.client.CoreV1Api()
        self.appsv1api = kubernetes.client.AppsV1Api()

    def Loadconfig(self):
        try:
            config.load_kube_config(project_dir + self.config_file)
            configuration = kubernetes.client.Configuration()
        except:
            logutil.errmsgStringIO(traceback, "api_client error")
            traceback.print_exc()
            sys.exit()
        return configuration
