# coding=utf-8
from __future__ import print_function
import traceback , json
import kubernetes.client
from kubernetes import client
from kubernetes.client import V1ExecAction
from kubernetes.client import V1Handler
from kubernetes.client import V1Lifecycle
from kubernetes.client import V1PodDNSConfig
from kubernetes.client.rest import ApiException
import configure
from control.parse_error import Error
from pcGroup.util import redisUtil
from pcGroup.log.logUtil import logUtil
import datetime
logutil = logUtil()
v1betaclient = configure.api_client('ctccluster').v1betaclient
v1client = configure.api_client('ctccluster').v1client

def is_state(state, type):
    ##只有pods存在时才会运行本函数，默认为create，不存在返回404,本函数运行失败则返回null。
    ifrunning = state.running
    ifterminated = state.terminated
    ifwaiting = state.waiting
    if type == 'delete':
        if ifterminated:
            return "deleting"
        else:
            return "error"
    elif type == 'create':
        if ifrunning:
            return "running"
        if ifterminated:
            return "error"
        if ifwaiting:
            reson = state.waiting.reason
            logutil.infoMsg("get_create_pod_status:" + reson)
            if reson == "ContainerCreating":
                return "creating"
            elif reson == "Pending":
                return "creating"
            else:
                return "error"
        logutil.infoMsg("type None")

namespace = 'default' # str | object name and auth scope, such as for teams and projects
body=kubernetes.client.V1Pod() # ExtensionsV1beta1Deployment |
pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)
class pods:

    @staticmethod
    def _list(name , pages , nextPages , location = 1):
        try:
            #label_selector: str | A selector to restrict the list of returned objects by their labels. Defaults to everything. (optional)
            label_selector = ""
            #int limit: limit is a maximum number of responses to return for a list call. If more items exist, the server will set the `continue` field on the list metadata to a value that can be used with the same initial query to retrieve the next set of results. Setting a limit may return fewer than the requested amount of items (up to zero items) in the event all requested objects are filtered out and clients should only use the presence of the continue field to determine whether more results are available. Servers may choose not to support the limit argument and will return all of the available results. If limit is specified and the continue field is empty, clients may assume that no more results are available. This field is not supported if watch is true.  The server guarantees that the objects returned when using continue will be identical to issuing a single list call without a limit - that is, no objects created, modified, or deleted after the first request is issued will be included in any subsequent continued requests. This is sometimes referred to as a consistent snapshot, and ensures that a client that is using limit to receive smaller chunks of a very large result can ensure they see all possible objects. If objects are updated during a chunked list the version of the object that was present at the time the first list result was calculated is returned.
            limit = 10
            #str _continue: The continue option should be set when retrieving more results from the server. Since this value is server defined, clients may only use the continue value from a previous query result with identical query parameters (except for the value of continue) and the server may reject a continue value it does not recognize. If the specified continue value is no longer valid whether due to expiration (generally five to fifteen minutes) or a configuration change on the server the server will respond with a 410 ResourceExpired error indicating the client must restart their list without the continue field. This field is not supported when watch is true. Clients may start a watch from the last resourceVersion value returned by the server and not miss any modifications.
            _continue = ""
            if name != "ALL":
                label_selector = "name=" + name
                if int(location) == 5:
                    label_selector = "app=" + name
            ret = None
            key = "pods" + name + str(pages)
            ContinueKey = "pods" + name + str(pages) + "continue"
            nextContinueKey = "pods" + name + str(nextPages) + "continue"
            redisRet = redisUtil.getValue(key)
            if redisRet != None:
                print("RedisResult : " + redisRet)
                logutil.infoMsg("RedisResult : " + redisRet)
                #return redisRet
            if pages == 0:
                ret = v1client.list_pod_for_all_namespaces( limit = limit , label_selector = label_selector , watch=False)
            else:
                redisConRet = redisUtil.getValue(ContinueKey)
                if redisConRet == None:
                    ret = v1client.list_pod_for_all_namespaces( limit = limit , label_selector = label_selector , watch=False)
                else:
                    ret = v1client.list_pod_for_all_namespaces(_continue = redisConRet , limit = limit , label_selector = label_selector , watch=False)
                print("Conkey : " + ContinueKey)
            #ret = v1.list_pod_for_all_namespaces(label_selector = label_selector , watch=False)
            result = {}
            resultList = []
            #print(ret)

            print("_continue Next:" + str(ret.metadata._continue) )
            print("pages : " + str(pages))
            for i in ret.items:
                #print("%s\t%s\t%s" % (i.status.pod_ip,  i.metadata.name, i.status.phase))
                result["name"] = i.metadata.name
                result["namespace"] = i.metadata.namespace
                if i.status.phase == "Failed" and i.status.reason == ("Evicted" or "OutOfmemory"):
                    continue
                result["podIp"] = i.status.pod_ip
                result["status"] = i.status.phase
                result["restartCount"]=0
                result["startAt"]=""
                result["containerName"] = i.spec.containers[0].name
                for conta in i.status.container_statuses:
                    ##if no labels, traceback.
                    if conta.name==i.spec.containers[0].name:
                        result["restartCount"] = conta.restart_count
                        try:
                            cnDatetime = conta.state.running.started_at + datetime.timedelta(hours=8)
                            result["startAt"] = cnDatetime.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            traceback.print_exc()
                            logutil.errmsgStringIO(traceback,"startAt")
                if len(i.spec.containers)<2:
                    result["podtype"]="test"
                else:
                    result["podtype"]="product"

                commands = i.spec.containers[0].command
                #print(commands)
                command = "Null"
                image = "Null"
                if commands != None and len(commands) > 0:
                    command = ""
                    for j in range(0 , len(commands)):
                        command = "%s %s" % (command , commands[j])
                    result["command"] = command
                try:
                    image = i.spec.containers[0].image
                except:
                    image = "get Error"
                limitTag = i.spec.containers[0].resources.limits
                if limitTag == None:
                    result["lResource"] = "None"
                else:
                    result["lResource"] = i.spec.containers[0].resources.limits
                if image != None and len(image) > 0:
                    result["image"] = image
                if i.metadata.name == "":
                    break
                resultList.append(result)
                result = {}
            _continue = str(ret.metadata._continue)
            redisUtil.setValue(nextContinueKey, _continue , 300)
            redisUtil.setValue(key , json.dumps(resultList))
            return json.dumps(resultList)
            #用于打印看结果
            #return json.dumps(str(ret).replace("\'","\"").replace("\\","").replace("\n",""))
        except ApiException as e:
            logutil.errmsgStringIO(traceback , 'pods list error')
            raise Exception
            #return Error(e).get_code()

    @staticmethod
    def _add(name=None,image=None,cpu=None,memNum=None,port=None):
        labels={"name":name}
        body=kubernetes.client.V1Pod()
        print (body)
        pretty = True
        try:
            data = {}
            namespace = 'default'
            result = v1client.create_namespaced_pod_with_http_info(namespace, body, pretty=pretty)
            data['k8scode'] = result[1]
            print (data)
            return data
        except (ApiException,Exception) as e:
            logutil.infoMsg("pod add error:"+name)
            return Error(e).get_code()


    @staticmethod
    def _del(name):
        data = {}
        try:
            namespace = 'default'
            result = v1client.delete_namespaced_pod_with_http_info(name, namespace, kubernetes.client.V1DeleteOptions())[1]
            data['k8scode'] = result
            return data
        except (ApiException,Exception) as e:
            logutil.infoMsg("pod del error:"+name)
            return Error(e).get_code(data=data)
    @staticmethod
    def get_pod_ip(name,type):
        data = {}
        data['ip'] = 'None'
        data['state']='None'
        try:
            namespace='default'
            result=v1client.read_namespaced_pod(name,namespace)
            container_status=result.status.container_statuses[0]
            data['ip']=result.status.pod_ip
            data['k8scode'] = 200
            data['state']=is_state(container_status.state,type)
            return data
        except (ApiException,Exception) as e:
            logutil.infoMsg("get_podip error:"+name)
            return Error(e).get_code(data=data)
    @staticmethod
    def _del_collection(name):
        label_selector='name='+name
        try:
            data={}
            namespace='default'
            rev=v1client.delete_collection_namespaced_pod_with_http_info(namespace,label_selector=label_selector)[1]
            data['k8scode'] = rev
            return data
        except (ApiException,Exception) as e:
            logutil.infoMsg("collection_pod del error:"+name)
            return Error(e).get_code()


    @staticmethod
    def get_pod_num(name):
      data={}
      pod_num=None
      label_selector = "name="+name
      try:
         result=v1client.list_namespaced_pod(namespace,label_selector=label_selector)
         pod_num = len(result.items)
      except (ApiException,Exception) as e:
         logutil.errmsgStringIO(traceback,"get_pod_num error")
         return pod_num;
      return pod_num






