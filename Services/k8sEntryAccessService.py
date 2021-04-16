# coding=utf-8
import  pcGroup.util.timeUtil as timeUtil
import  json
from pcGroup.elasticSearch.searchUtil import searchUtil
import pcGroup.util.numberFormat as numberFormat

def statusBytime(startTimestamp , endTimestamp , appName):
    urlPrefix = "logstash-k8s-entry-tengine-access-"
    inStartTimestamp = startTimestamp
    inEndTimestamp = endTimestamp
    if endTimestamp > 1000000000000:
        inStartTimestamp = startTimestamp / 1000
        inEndTimestamp = endTimestamp / 1000
    urlIndex = timeUtil.getIndexBetweenDays(urlPrefix , inStartTimestamp , inEndTimestamp , fullDate=True)
    interval = numberFormat.timeInterval(inStartTimestamp , inEndTimestamp)
    #print urlIndex ,  interval
    pData = {
        "query": {
            "bool": {
                "must": [
                    {"range": {
                        "@timestamp": {
                            "from": startTimestamp,
                            "to":  endTimestamp
                        }
                    }
                    },
                    {"term": {
                        "iHost.keyword": {
                            "value": appName
                        }
                    }
                    }
                ]

            }
        },"size":0,"aggs": {"groupDate":{
            "date_histogram": {
                "field": "@timestamp",
                "interval": str(interval) + "s"
            }, "aggs": {
                "status": {
                    "terms": {
                        "field": "status",
                        "size": 10
                    }
                }
            }
        }
        }
    }
    pDataStr = json.dumps(pData)
    print pDataStr
    searchutil = searchUtil()
    ret = searchutil.searchELT(urlIndex,type="k8sEntryAccess" , postData=pDataStr , cache=False)
    retJson = json.loads(ret)
    datas = []
    retMap = {} ; retSTotal = [] ; retS200 = [] ; retS403 = [] ; retS404 = [] ; retS4xx = [] ; retS500 = [] ; retS504 = [] ; retS5xx = []
    timeBuckets = retJson["aggregations"]["groupDate"]["buckets"]
    for i in range(0 , len(timeBuckets)):
        retTmpSTotal = [] ; retTmpS200 = [] ; retTmpS403 = [] ; retTmpS404 = [] ; retTmpS4xx = [] ; retTmpS500 = [] ; retTmpS504 = [] ; retTmpS5xx = []
        retTmpMap = {}
        retTmpMap["s4xx"] = 0 ; retTmpMap["s5xx"] = 0
        retTmpMap["s200"] = 0 ; retTmpMap["s301"] = 0 ; retTmpMap["s302"] = 0 ; retTmpMap["s403"] = 0 ; retTmpMap["s404"] = 0
        retTmpMap["s500"] = 0 ; retTmpMap["s502"] = 0 ; retTmpMap["s503"] = 0 ; retTmpMap["s504"] = 0
        statusBuckets = timeBuckets[i]["status"]["buckets"]
        for j in range(0 ,len(statusBuckets)):
            retTmpMap["s" + str(statusBuckets[j]["key"])] = statusBuckets[j]["doc_count"]
            if statusBuckets[j]["key"] >=400 and statusBuckets[j]["key"] < 500:
                retTmpMap["s4xx"] = retTmpMap["s4xx"]  + statusBuckets[j]["doc_count"]
            if statusBuckets[j]["key"] >=500 and statusBuckets[j]["key"] < 600:
                retTmpMap["s5xx"] = retTmpMap["s5xx"]  + statusBuckets[j]["doc_count"]
        retTmpSTotal.append(timeBuckets[i]["key"]) ; retTmpSTotal.append(timeBuckets[i]["doc_count"])
        retTmpS200.append(timeBuckets[i]["key"]) ; retTmpS200.append(retTmpMap["s200"])
        retTmpS403.append(timeBuckets[i]["key"]) ; retTmpS403.append(retTmpMap["s403"])
        retTmpS4xx.append(timeBuckets[i]["key"]) ; retTmpS4xx.append(retTmpMap["s4xx"])
        retTmpS404.append(timeBuckets[i]["key"]) ; retTmpS404.append(retTmpMap["s404"])
        retTmpS500.append(timeBuckets[i]["key"]) ; retTmpS500.append(retTmpMap["s500"])
        retTmpS504.append(timeBuckets[i]["key"]) ; retTmpS504.append(retTmpMap["s504"])
        retTmpS5xx.append(timeBuckets[i]["key"]) ; retTmpS5xx.append(retTmpMap["s5xx"])
        retSTotal.append(retTmpSTotal) ; retS200.append(retTmpS200) ; retS403.append(retTmpS403) ; retS404.append(retTmpS404) ; retS4xx.append(retTmpS4xx)
        retS500.append(retTmpS500) ; retS504.append(retTmpS504) ; retS5xx.append(retTmpS5xx)
    retMap["name"] = "ALL" ; retMap["data"] = retSTotal ; datas.append(retMap)
    retMap = {}
    retMap["name"] = "200" ; retMap["data"] = retS200 ; datas.append(retMap)
    retMap = {}
    retMap["name"] = "403" ; retMap["data"] = retS403 ; datas.append(retMap)
    retMap = {}
    retMap["name"] = "404" ; retMap["data"] = retS404 ; datas.append(retMap)
    retMap = {}
    retMap["name"] = "4xx" ; retMap["data"] = retS4xx ; datas.append(retMap)
    retMap = {}
    retMap["name"] = "500" ; retMap["data"] = retS500 ; datas.append(retMap)
    retMap = {}
    retMap["name"] = "504" ; retMap["data"] = retS504 ; datas.append(retMap)
    return  json.dumps(datas)


def accessTotalStatus(startTimestamp , endTimestamp , appName):
    urlPrefix = "logstash-k8s-entry-tengine-access-"
    inStartTimestamp = startTimestamp
    inEndTimestamp = endTimestamp
    if endTimestamp > 1000000000000:
        inStartTimestamp = startTimestamp / 1000
        inEndTimestamp = endTimestamp / 1000
    urlIndex = timeUtil.getIndexBetweenDays(urlPrefix , inStartTimestamp , inEndTimestamp , fullDate=True)
    #print urlIndex
    pData = {
        "query": {
            "bool": {
                "must": [
                    {"range": {
                        "@timestamp": {
                            "from": startTimestamp,
                            "to":  endTimestamp
                        }
                    }
                    },
                    {"term": {
                        "iHost.keyword": {
                            "value": appName
                        }
                    }
                    }
                ]

            }
        },"size":0,"aggs" : {
                        "status": {
                            "terms" : {
                                "field" : "status"
                            }
                        },
                        "method": {
                            "terms": {
                                "field" : "method.keyword"
                            }
                        },
                        "req_time": {"avg": {
                            "field": "req_time"
                            }
                        }
        }
    }
    pDataStr = json.dumps(pData)
    searchutil = searchUtil()
    ret = searchutil.searchELT(urlIndex,type="k8sEntryAccess" , postData=pDataStr , cache=False)
    retJson = json.loads(ret)
    totalBuckets = retJson["aggregations"]
    #print uriBuckets
    retTmpMap = {}
    statusBuckets = totalBuckets["status"]["buckets"]
    methodBuckets = totalBuckets["method"]["buckets"]
    retTmpMap["s4xx"] = 0 ; retTmpMap["s5xx"] = 0 ; retTmpMap["Other"] = 0
    retTmpMap["s200"] = 0 ; retTmpMap["s301"] = 0 ; retTmpMap["s302"] = 0 ; retTmpMap["s403"] = 0 ; retTmpMap["s404"] = 0
    retTmpMap["s500"] = 0 ; retTmpMap["s502"] = 0 ; retTmpMap["s503"] = 0 ; retTmpMap["s504"] = 0
    retTmpMap["sGET"] = 0 ; retTmpMap["sPOST"] = 0 ; retTmpMap["sHEAD"] = 0
    for j in range(0 ,len(statusBuckets)):
        retTmpMap["s" + str(statusBuckets[j]["key"])] = statusBuckets[j]["doc_count"]
        if statusBuckets[j]["key"] >=400 and statusBuckets[j]["key"] < 500:
            retTmpMap["s4xx"] = retTmpMap["s4xx"]  + statusBuckets[j]["doc_count"]
        if statusBuckets[j]["key"] >=500 and statusBuckets[j]["key"] < 600:
            retTmpMap["s5xx"] = retTmpMap["s5xx"]  + statusBuckets[j]["doc_count"]
    for e in range(0 , len(methodBuckets)):
        if methodBuckets[e]["key"] != "GET" and methodBuckets[e]["key"] != "POST" and methodBuckets[e]["key"] != "HEAD":
            retTmpMap["Other"] = retTmpMap["Other"] + methodBuckets[e]["doc_count"]
        else:
            retTmpMap["s" + methodBuckets[e]["key"]] = methodBuckets[e]["doc_count"]
    retTmpMap["totalCon"] = retJson["hits"]["total"] ; retTmpMap["totalResTime"] = format(totalBuckets["req_time"]["value"],'.3f')
    retTmpMap["totalS200"] = retTmpMap["s200"] ; retTmpMap["totalS403"] = retTmpMap["s403"] ; retTmpMap["totalS4xx"] = retTmpMap["s4xx"]
    retTmpMap["totalS500"] = retTmpMap["s500"] ; retTmpMap["totalS504"] = retTmpMap["s504"] ; retTmpMap["totalS5xx"] =retTmpMap["s5xx"]
    return json.dumps(retTmpMap)


def urlStatusService(startTimestamp , endTimestamp , appName):
    urlPrefix = "logstash-k8s-entry-tengine-access-"
    inStartTimestamp = startTimestamp
    inEndTimestamp = endTimestamp
    if endTimestamp > 1000000000000:
        inStartTimestamp = startTimestamp / 1000
        inEndTimestamp = endTimestamp / 1000
    urlIndex = timeUtil.getIndexBetweenDays(urlPrefix , inStartTimestamp , inEndTimestamp , fullDate=True)
    urlIndex = urlIndex.replace(",logstash-k8s-entry-tengine-access-2020-08-16" ,"")
    pData = {
        "query": {
            "bool": {
                "must": [
                    {"range": {
                        "@timestamp": {
                            "from": startTimestamp,
                            "to":  endTimestamp
                        }
                    }
                    },
                    {"term": {
                        "iHost.keyword": {
                            "value": appName
                        }
                    }
                    }
                ]

            }
        },"size":0,"aggs" : {
            "uri" :
                {
                    "terms" : {
                        "field" : "uri.keyword" ,
                        "size": 30
                    },
                    "aggs" : {
                        "status": {
                            "terms" : {
                                "field" : "status"
                            }
                        },
                        "method": {
                            "terms": {
                                "field" : "method.keyword"
                            }
                        }
                    }
                }
        }
    }
    pDataStr = json.dumps(pData)
    searchutil = searchUtil()
    ret = searchutil.searchELT(urlIndex,type="k8sEntryAccess" , postData=pDataStr , cache=False)
    retJson = json.loads(ret)
    retList = []
    uriBuckets = retJson["aggregations"]["uri"]["buckets"]
    #print uriBuckets
    for i in range(0, len(uriBuckets)):
        #status: 200,301,302,404,403,4xx,500,502,503,504,5xx;method:GET,POST,HEAD,other
        retTmpMap = {}
        retTmpMap["uriKey"] = uriBuckets[i]["key"]
        retTmpMap["uriValue"] = uriBuckets[i]["doc_count"]
        statusBuckets = uriBuckets[i]["status"]["buckets"]
        methodBuckets = uriBuckets[i]["method"]["buckets"]
        retTmpMap["s4xx"] = 0 ; retTmpMap["s5xx"] = 0 ; retTmpMap["Other"] = 0
        retTmpMap["s200"] = 0 ; retTmpMap["s301"] = 0 ; retTmpMap["s302"] = 0 ; retTmpMap["s403"] = 0 ; retTmpMap["s404"] = 0
        retTmpMap["s500"] = 0 ; retTmpMap["s502"] = 0 ; retTmpMap["s503"] = 0 ; retTmpMap["s504"] = 0
        retTmpMap["sGET"] = 0 ; retTmpMap["sPOST"] = 0 ; retTmpMap["sHEAD"] = 0
        for j in range(0 ,len(statusBuckets)):
            retTmpMap["s" + str(statusBuckets[j]["key"])] = statusBuckets[j]["doc_count"]
            if statusBuckets[j]["key"] >=400 and statusBuckets[j]["key"] < 500:
                retTmpMap["s4xx"] = retTmpMap["s4xx"]  + statusBuckets[j]["doc_count"]
            if statusBuckets[j]["key"] >=500 and statusBuckets[j]["key"] < 600:
                retTmpMap["s5xx"] = retTmpMap["s5xx"]  + statusBuckets[j]["doc_count"]
        for e in range(0 , len(methodBuckets)):
            if methodBuckets[e]["key"] != "GET" and methodBuckets[e]["key"] != "POST" and methodBuckets[e]["key"] != "HEAD":
                retTmpMap["Other"] = retTmpMap["Other"] + methodBuckets[e]["doc_count"]
            else:
                retTmpMap["s" + methodBuckets[e]["key"]] = methodBuckets[e]["doc_count"]
        retList.append(retTmpMap)
    return json.dumps(retList)


if __name__ == "__main__":
    #print urlStatusService(1597540039000,1597651039000)
    statusBytime(1597650039000,1597651039000 , "pc-ad-analysis-post-core.inm.com")