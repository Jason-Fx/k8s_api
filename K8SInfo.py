#!/usr/bin/python
#-*- coding: utf-8 -*-

from flask import request
from flask_restful import  Resource , reqparse

from common import Connect
from control import Pods, Nodes, Services, Namespace, Component
from control.Pods import pods
from control.configure import cp
from control.Nodes import *
from control.Services import services
from control.Namespace import  k8sNamespace
from flask import make_response
import json , traceback

import pcGroup.util.JsonResultUtil as JsonResultUtil
from pcGroup.log.logUtil import logUtil
logutil = logUtil()

##使用前必须注册 Connect.init(模块名."集群名称")

class podsInfo(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Pods, self.region)


    def get(self , name , page):
        response = None
        try:
            #result = JsonResultUtil.__sucessful__(pods._list(name , page , 1))
            #logutil.loggerwarn("pods Info Result : " + json.dumps(result))
            nextPages = int(page) + 1
            response = make_response(JsonResultUtil.__sucessful__(pods._list(name , page , nextPages , self.region)))
        except:
            response = make_response(JsonResultUtil.__fail__("\"get podsInfo Error\""))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

class podsList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Pods,self.region)



    def get(self):
        nowPages = None
        nextPages = None

        try:
            nowPages = request.args.get("page")
            #nowPages = data.get('page')
            print "nowPages:" + str(nowPages)
        except:
            print "nowPages: Error"
            logutil.errmsgStringIO(traceback , "page Error")
        if nowPages == None:
            nowPages = 0
            nextPages = 1
        else:
            nextPages = int(nowPages) + 1
        response = None
        try:
            result = JsonResultUtil.__sucessful__(pods._list("ALL" , nowPages , nextPages))
            logutil.warnMsg("pods List result : " + result)
            response = make_response(result)
        except Exception as e:
            response = make_response(JsonResultUtil.__fail__("\"Api Errpr\""))
            logutil.errmsgStringIO(traceback , "Api Error")
        #response = make_response(pods._list("ALL"))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

class nodesList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Nodes,self.region)

    def get(self):
        response = make_response(JsonResultUtil.__sucessful__(nodes._list()))
        #response = make_response(pods._list("ALL"))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

class svcList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Services,self.region)

    def get(self):
        namespace = request.args.get('k8sNamespace') or "default"
        response = make_response(JsonResultUtil.__sucessful__(json.dumps(services.svc_list(lType="otherInfo", k8sNamespace=namespace))))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

class namespaceList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Namespace,self.region)

    def get(self):
        response = make_response(JsonResultUtil.__sucessful__(json.dumps(k8sNamespace._list())))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

class componentStatusList(Resource):
    def __init__(self):
        self.region = request.args.get('location')
        Connect.init(Component, self.region)