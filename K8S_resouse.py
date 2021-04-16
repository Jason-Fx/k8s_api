# coding=utf-8

from flask import request
from flask_restful import Resource

from common import Connect
from control import Deployment, Ingress, Services, Endpoint, Pods, podlogs, Podlog , Statefulset
from control.Deployment import *
from control.Endpoint import endpoint
from control.Ingress import ingress
from control.Services import services
from control.Statefulset import statefulset
from control.configure import cp, os
from control.podlogs import podlogs
from control.Podlog import podlog
from control.Pods import pods
from pcGroup.util import redisUtil
from common import Constant
import pcGroup.util.paramUtil as paramUtil


##使用前必须注册 Connect.init(模块名."集群名称")
def RegionDict():
    return {
        1: "ctccluster",
        2: "alicluster"
    }


def task_err_return(e):
    return {"k8scode": 404, "message": e}


class deployment_resource(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Deployment, self.region)

    def post(self):
        if request.method == 'POST':
            data = request.get_data()
            data = json.loads(data)
            result = deployment._add(data)
            return result

    def delete(self):
        if request.method == 'DELETE':
            name = request.args.get('jobName')
            #####   "args.name" NOT NULL
            if not name:
                return {"k8scode": 404}
            result = deployment._del(name)
            return result


class services_resource(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Services, self.region)

    def post(self):
        if request.method == 'POST':
            data = request.get_data()
            data = json.loads(data)
            result = services._add(data)
            return result

    def delete(self):
        if request.method == 'DELETE':
            name = request.args.get('jobName')
            if not name:
                return {"k8scode": 404}
            result = services._del(name)
            return result

    def get(self):
        if request.method == 'GET':
            result = services.svc_list()
            return result


class endpoint_resource(Resource):
    def __init__(self):
        self.region = request.args.get('location')

        Connect.init(Endpoint, self.region)

    def get(self):
        if request.method == 'GET':
            name = request.args.get('jobName')
            result = endpoint._get(name)
            return Response(json.dumps(result), mimetype='application/json')


class pod_resource(Resource):
    def __init__(self):
        self.region = request.args.get('location')

        Connect.init(Pods, self.region)
        print

    def post(self):
        if request.method == 'POST':
            data = request.get_data()
            data = json.loads(data)
            result = pods._add(name=data["jobName"], image=data['imageName'], port=data["port"])
            return result

    def delete(self):
        if request.method == 'DELETE':
            name = request.args.get('jobName')
            if not name:
                return {"k8scode": 404}
            result = pods._del_collection(name)
            return result


class pods_ip_with_create_status(Resource):
    def __init__(self):
        self.region = request.args.get('location')

        Connect.init(Pods, self.region)

    def get(self):
        if request.method == 'GET':
            name = request.args.get('jobName')
            type = 'create'
            if not name:
                return {"k8scode": 404}
            result = pods.get_pod_ip(name, type)
            return result


class pods_ip_with_delete_status(Resource):
    def __init__(self):
        self.region = request.args.get('location')

        Connect.init(Pods, self.region)

    def get(self):
        if request.method == 'GET':
            type = 'delete'
            name = request.args.get('jobName')
            if not name:
                return {"k8scode": 404}
            result = pods.get_pod_ip(name, type)
            return result


class ingress_rule(Resource):
    def __init__(self):
        self.region = request.args.get('location')

        Connect.init(Ingress, self.region)

    def post(self):
        if request.method == 'POST':
            data = request.get_data()
            data = json.loads(data)
            if not data:
                return {"k8scode": 404}
            result = ingress._add(data)
            return result

    def get(self):
        if request.method == 'GET':
            data = request.args.get('mName')
            print self.region
            Connect.init(Ingress, region=self.region)
            return data

    def put(self):
        if request.method == 'PUT':
            data = request.get_data()
            data = json.loads(data)
            if not data:
                return {"k8scode": 404}
            result = ingress._replace(data)
            return result

    def delete(self):
        if request.method == 'DELETE':
            name = request.args.get('mName')
            if not name:
                return {"k8scode": 404}
            result = ingress._del(name)
            return result


class ingress_rule_list(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Ingress, self.region)

    def get(self):
        if request.method == 'GET':
            k8sNamespace = paramUtil.getString(request , "k8sNamespace" , isNull=True)
            if k8sNamespace == None:
                k8sNamespace = "default"
            result = ingress._list(k8sNamespace)
            return result


class services_ip(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Services, self.region)

    def get(self):
        if request.method == 'GET':
            name = request.args.get('jobName')
            namespace = request.args.get('k8sNamespace') or "default"
            if not name:
                return {"k8scode": 404}
            result = services.svc_ip(name, k8sNamespace=namespace)
            return result


class getlog(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Podlog, self.region)

    def get(self):
        if request.method == 'GET':
            jobname = request.args.get('jobName')
            podname = request.args.get('podName')
            previous = request.args.get('online')
            type = request.args.get('type')
            tailline = request.args.get('tailline')
            k8sNamespace = paramUtil.getString(request , "k8sNamespace")
            print jobname, podname, previous, type
            logutil.infoMsg("getlog: %s,%s,%s,%s" % (jobname, podname, str(previous), str(type)))
            if not podname:
                return {"k8scode": 404}
            if not type:
                return {"k8scode": 404}
            if not jobname:
                return {"k8scode": 404}
            if not previous:
                return {"k8scode": 404}
            if not tailline:
                tailline = 100
            tmpLocation = int(request.args.get('location'))
            '''
            if tmpLocation != 5:
                result = podlog.get_pods_log(podname=podname, jobname=jobname, previous=previous, type=type,
                                         tailline=tailline)
            else:
                result = podlog.get_pods_log(podname=podname, jobname=jobname, previous=previous, type=type,
                                             tailline=tailline , namespaceUser="zx-app")
            '''
            result = podlog.get_pods_log(podname=podname, jobname=jobname, previous=previous, type=type,
                                         tailline=tailline , namespaceUser=k8sNamespace)
            return result


class deployment_rs_status(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Deployment, self.region)

    def get(self):
        if request.method == 'GET':
            name = request.args.get('jobName')
            namespace = request.args.get('k8sNamespace') or "default"
            if redisUtil.getValue("rs_search_" + name) and redisUtil.getValue("rs_search_" + name) == 0:
                return {"k8scode": 423, "update_rep": 0, "dep_rep": 0}
            # if redisUtil.getValue("rs_search_" + name) == None:
            #    return {"k8scode": 403, "update_rep": 0, "dep_rep": 0}
            if not name:
                return {"k8scode": 404, "update_rep": 0, "dep_rep": 0}
            result = deployment._get_update_status(name, k8sNamespace=namespace)
            return result


class deployment_get_arg(Resource):
    def __init__(self):
        self.region = paramUtil.getInt(request,'location')
        Connect.init(Deployment, self.region)

    def get(self):
        if request.method == 'GET':
            name = request.args.get('jobName')
            namespace = request.args.get('k8sNamespace') or "default"
            result = deployment._get_deployment_info(name, region=self.region, k8sNamespace=namespace)
            return result


class jenkins_all_delete(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Services, self.region)
        Connect.init(Deployment, self.region)

    def delete(self):
        if request.method == 'DELETE':
            name = request.args.get('jobName')
            namespace = request.args.get('k8sNamespace') or "default"
            dep_del_result = deployment._del(name, k8sNamespace=namespace)
            svc_del_result = services._del(name, k8sNamespace=namespace)
            logutil.infoMsg(dep_del_result.get_data())
            logutil.infoMsg(svc_del_result)
            return {"k8scode": 200}

class deploymentList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Deployment, self.region)

    def get(self):
        region = paramUtil.getString(request , "location")
        k8sNamespace = paramUtil.getString(request , "k8sNamespace")
        return deployment.getDeploymentList(region , k8sNamespace)

class statefulsetList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Statefulset, self.region)

    def get(self):
        region = paramUtil.getString(request , "location")
        k8sNamespace = paramUtil.getString(request , "k8sNamespace")
        return statefulset.getStatefulsetList(region , k8sNamespace)

class getAvailableReplicas(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Statefulset, self.region)
    def get(self):
        region = paramUtil.getString(request , "location")
        k8sNamespace = paramUtil.getString(request , "k8sNamespace")
        name = paramUtil.getString(request , "name")
        return deployment.getAvailableReplicas(name , region , k8sNamespace)


if __name__ == '__main__':
    # deployment test
    # Connect.init(Deployment, region=ctc2cluster)
    # print deployment._get_deployment_info(name='nginxtest', region=ctc2cluster)
    # print deployment._get_update_status(name='nginxtest', region=ctc2cluster)
    # print deployment._del('nginxtest')

    # ingress test
    # Connect.init(Ingress, region=ctc2cluster)
    # print ingress._list()
    # print ingress._get('nginxtest')
    # print ingress._add(data1)
    # print ingress._replace(data1)
    # print ingress._del('nginxtest')

    pass