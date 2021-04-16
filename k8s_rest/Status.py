# coding=utf-8
import json
import thread
import traceback

import redis
import requests
from flask_restful import Resource

import pcGroup
from pcGroup.util.redisUtil import setValue, getValue

url='http://127.0.0.1:8080/api/v1/'
redishost='127.0.0.1'

pcGroup.util.redisUtil .pool= redis.ConnectionPool(host=redishost, port=6379)

class k8s_request_info:
    def __init__(self,type):
        self.kind=type
        self.responedata={}
        self.responedata['k8scode']=''
        self.responedata['body'] = ''
        self.responedata['reason'] = ''
        self.get_data()

    def get_data(self):
        data = {}
        try:
            result = requests.get(url + self.kind)
            self.responedata['k8scode'] = result.status_code
            self.responedata['body'] = result.json()
            self.responedata['reason'] = result.reason
        except Exception as e:
            print e
            traceback()
        return self.responedata

    def item(self):
        return self.responedata['body']['items']

class nodes_info:
    @staticmethod
    def nodesinfo():
        nodes_info=k8s_request_info('nodes')
        nodes_info_list=[]
        run_pod=0
        max_run_pod=0
        for node in nodes_info.item():
            nodedata = {}
            nodedata['name']=node.get('metadata').get('name')
            nodedata['memory']=node.get('status').get('capacity').get('memory')
            nodedata['maxpods']=node.get('status').get('capacity').get('pods')
            node_info=  k8s_request_info('pods?fieldSelector=spec.nodeName%3D'+nodedata['name']+'%2Cstatus.phase%21%3DFailed%2Cstatus.phase%21%3DSucceeded')
            nodedata['pod']=len(node_info.item())
            run_pod=run_pod+int(nodedata['pod'])
            max_run_pod=max_run_pod+int(nodedata['maxpods'])
            poddata = []
            for pod in  node_info.item():
                if pod.get('metadata').get('namespace') == 'default':
                    pass
                else:
                    continue
                data={}
                if pod.get('status').get('phase')=='Running':
                    data['name']=pod.get('metadata').get('labels').get('name')
                    data['podname']=pod.get('metadata').get("name")
                    if data['name']!=None:
                        vpn_redis.put(data['name'],data['podname'],999999)
                    # if len(pod.get('status').get('containerStatuses'))>1:
                    #     for docker in pod.get('status').get('containerStatuses'):
                    #         if docker.get('name')==data['name']:
                    #             data['dockerid']=docker.get('containerID')
                    # else:
                    #     data['dockerid']=pod.get('status').get('containerStatuses')[0].get('containerID')

                    data['podip']=pod.get('status').get('podIP')
                    poddata.append(data)
            #nodedata['poddata']=poddata
            nodes_info_list.append(nodedata)
        nodes_info.responedata['body']=nodes_info_list
        nodes_info.responedata['running_pod']=run_pod
        nodes_info.responedata['max_run_pod']=max_run_pod
        return nodes_info.responedata


class pods_info:
    @staticmethod
    def get_pod_name(name,refresh=True):
        podname=vpn_redis.get(name)

        try:
            if bool(refresh)==True:
                #refresh
                thread.start_new_thread(nodes_info.nodesinfo,())
                podname=vpn_redis.get(name)
            return podname
        except Exception as e:
            print e,"get_pod_name"
class vpn_redis:
    @staticmethod
    def put(key,value,expire):
        setValue(key,value,expire)
    @staticmethod
    def get(key):
        return getValue(key)


if __name__ == '__main__':
    print pods_info.get_pod_name('crazyvpn100')








