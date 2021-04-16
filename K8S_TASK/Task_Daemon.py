# coding=utf-8
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(os.getcwd())
import ConfigParser
import traceback
from time import sleep
import thread
import requests
from flask import json
from common import Connect
from control import Deployment, Services, configure
from control.Deployment import deployment
from control.Services import services
from pcGroup.log.logUtil import logUtil
from pcGroup.util import redisUtil
from pcGroup.util.httpsqs_api import HttpsqsClient
from pcGroup.util.requestUtil import logutil

logutil = logUtil()
cp = ConfigParser.SafeConfigParser()
##check_config() return {project_dir,host}
host = configure.check_config()[1]
project_dir = configure.check_config()[0]
mainConf = project_dir + "/conf/main.conf"
cp.read(mainConf)
TaskServer = cp.get("TaskQue", "server")


def post_job_state(jobname, state, message, opt):
    endpoint = r"/v1/mservice/k8s/queueInfo/"
    url = ''.join([host, endpoint])
    data = {}
    data['jobName'] = jobname
    State = ""
    if state == 0:
        State = "doing"
        redisUtil.setValue("rs_search_" + jobname, 1)
    elif state == 1:
        State = "done"
        redisUtil.setValue("rs_search_" + jobname, 1)
    elif state == 2:
        State = "error"
        redisUtil.setValue("rs_search_" + jobname, 0, expire=601)
    else:
        raise "post_job_state(state:" + str(message) + ")" + " args error"
    data['state'] = State
    data['message'] = message
    data['opt'] = opt
    try:
        r = requests.post(url, data=data)
    except:
        ##log traceback
        logutil.errmsgStringIO(traceback, "post_job_state lookback failed")
        sleep(2)
        # retry
        post_job_state(jobname, state, message, opt)
    print r.status_code
    print data


class work_put:
    def __init__(self, data):
        print data
        typelist = {"pod", "deployment", "services"}
        optlist = {"delete", "create", "update"}
        self.region = data.get('location')
        self.type = data["type"]
        self.opt = data["opt"]
        self.jobname = data["jobName"]
        self.namespace = data.get("k8sNamespace") or "default"
        self.body = data["body"]
        if self.type not in typelist:
            post_job_state(self.jobname, 2, "type not in typelist,working not running", self.opt())
        if self.opt not in optlist:
            post_job_state(self.jobname, 2, "type not in typelist,working not running", self.opt())
        work_put.act_int(self)

    @staticmethod
    def cpunum(cputype):
        try:
            ##cpytype==0,最多使用1核
            if cputype == 0:
                return 1
            ##cpytype == 0, 最多使用2核
            elif cputype == 1:
                return 2
        ##default num
        except:
            return 1

    # 判断动作类型
    def act_int(self):
        if self.type == "pod":
            self.pod_action()
        if self.type == "deployment":
            Connect.init(Deployment, self.region)
            Connect.init(Services, self.region)
            self.dep_action()
        if self.type == "services":
            self.svc_action()
            Connect.init(services, self.region)

    # deployments动作
    def dep_action(self):
        if self.opt == "create":
            name = self.jobname
            namespace = self.namespace
            replicas = self.body["replicas"]
            port = self.body["port"]
            image = self.body["imageName"]
            service = self.body["service"]
            cputype = self.body["cpuType"]
            memnum = self.body["memNum"]
            cpunum = self.cpunum(cputype)
            healthUrl = self.body["healthUrl"]
            logutil.infoMsg("create dep")
            data = deployment._add(name, replicas, port, image, cpunum, memnum, healthUrl, self.region, k8sNamespace=namespace).get_data()
            data = json.loads(data)
            data['name'] = name
            if int(data['k8scode']) == 422:
                logutil.infoMsg(self.jobname + " Httpcode 422 Unprocessable args" + self.opt)
                post_job_state(self.jobname, 2, "Httpcode 422 Unprocessable args", self.opt)
            elif int(data['k8scode']) in range(200, 299):
                logutil.infoMsg(self.jobname + str(data['k8scode']) + " OK" + self.opt)
                post_job_state(self.jobname, 1, "Httpcode " + str(data['k8scode']) + " OK", self.opt)
            elif int(data['k8scode']) == 409:  ## need delete dep
                logutil.infoMsg(self.jobname + " Httpcode 409 deployment exists" + self.opt)
                post_job_state(self.jobname, 1, "Httpcode 409 deployment exists", self.opt)
            else:
                logutil.infoMsg(self.jobname + " Httpcode " + str(data['k8scode']) + " Unknow state " + self.opt)
                post_job_state(self.jobname, 2, "Httpcode " + str(data['k8scode']) + " Unknow state ", self.opt)
            if service == 'True':
                svcdata = services._add(name, port, k8sNamespace=namespace)
                if svcdata['k8scode'] != range(200, 299) or 409:
                    logutil.infoMsg(
                        self.jobname + " Httpcode " + str(data['k8scode']) + " service create failure " + self.opt)
                    post_job_state(self.jobname, 2, "Httpcode " + str(data['k8scode']) + " service create failure ",
                                   self.opt)
        elif self.opt == "delete":
            data = deployment._del(self.jobname, k8sNamespace=self.namespace).get_data()
            data = json.loads(data)
            if int(data['k8scode']) == 200 or 404:
                logutil.infoMsg(self.jobname + " Httpcode " + str(data['k8scode']) + " delete OK " + self.opt)
                post_job_state(self.jobname, 1, "Httpcode " + str(data['k8scode']) + "delete OK", self.opt)
            else:
                logutil.infoMsg(self.jobname + " Httpcode " + str(data['k8scode']) + " delete failure " + self.opt)
                post_job_state(self.jobname, 2, "Httpcode " + str(data['k8scode']) + "delete failure", self.opt)
                logutil.infoMsg("delete dep")
        elif self.opt == "update":
            name = self.jobname
            namespace = self.namespace
            print type(self.body)
            print type(self.body["replicas"])
            replicas = self.body["replicas"]
            port = self.body["port"]
            image = self.body["imageName"]
            cputype = self.body["cpuType"]
            memnum = self.body["memNum"]
            cpunum = self.cpunum(memnum)
            healthUrl = self.body["healthUrl"]
            logutil.infoMsg("update dep")
            data = deployment._update(name, replicas, port, image, cpunum, memnum, healthUrl, self.region, k8sNamespace=namespace).get_data()
            data = json.loads(data)
            data['name'] = name
            if int(data['k8scode']) == 422:
                post_job_state(self.jobname, 2, "Httpcode 422 Unprocessable args", self.opt)
            elif int(data['k8scode']) in range(200, 299):
                post_job_state(self.jobname, 1, "Httpcode " + str(data['k8scode']) + " OK", self.opt)
            elif int(data['k8scode']) == 409:  ## need delete dep
                post_job_state(self.jobname, 2, "Httpcode 409 deployment exists", self.opt)
            else:
                post_job_state(self.jobname, 2, "Httpcode " + str(data['k8scode']) + " Unknow state ", self.opt)

    # pod动作
    def pod_action(self):
        if self.opt == "create":
            logutil.infoMsg("create pod")
        elif self.opt == "delete":
            logutil.infoMsg("delete pod")

    # services动作
    def svc_action(self):
        if self.opt == "create":
            logutil.infoMsg("create svc")
        elif self.opt == "delete":
            logutil.infoMsg("delete svc")

            # deployment_task.create(deploymentbody)


class task_daemon():
    @staticmethod
    def get_sqs_data():
        print("taskServer" + TaskServer)
        sqs = HttpsqsClient(TaskServer)
        data = sqs.get("ManageJob")
        return data

    def start(self):
        print("task start")
        while True:
            sleep(1)
            try:
                data = task_daemon.get_sqs_data()
                if data == None:
                    sleep(0.1)
                    #        logutil.infoMsg("no tasking,sleep 10s")
                    continue
                #        print "=================================================="
                data = json.loads(data)
                logutil.infoMsg("tasking:" + str(data))
                ##init peer state
                post_job_state(data['jobName'], 0, "None", data['opt'])
                thread.start_new_thread(work_put, (data,))
            #        print "=================================================="
            except Exception as e:
                ##log
                logutil.errmsgStringIO(traceback, "Task_Daemon.py thread error")
                # post_job_state(data['jobName'], 2, "thread error", data['opt'])
        return



if __name__ == '__main__':
    # 任务启动
    sqs_task=task_daemon().start()
    # print type(data)
    # work_put(data)