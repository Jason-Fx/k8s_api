# coding=utf-8

import time, json, traceback, datetime
from flask_restful import Resource
import pcGroup.util.requestUtil as pcreq
import pcGroup.util.numberFormat as pcnumf
from dateutil.relativedelta import relativedelta
from flask import request
import copy
import pcGroup.util.JsonResultUtil as JsonResultUtil
from pcGroup.log.logUtil import logUtil
import pcGroup.util.paramUtil as paramUtil
import Services.k8sEntryAccessService as k8sEntryAccessService

logutil = logUtil()

_url = "http://host:port/springcloud-metricbeat-*-%s,springcloud-metricbeat-*-%s/_search"
_newurl = "http://host:port/%s/_search"
_urldict = {"1": "http://host:port/%s/_search", "3": "http://host:port/%s/_search",
            "2": "http://aliyun:port/%s/_search"}
respon_header = {}
respon_header['Content-Type'] = 'application/json'
respon_header['Access-Control-Allow-Origin'] = '*'
respon_header['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
respon_header['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'

podtuple = ("probename", "querykey", "agg", "metricset")


def get_query(source, filters, starttime=None, endtime=None, sort=True, timestamp_field='@timestamp', desc=True,
              five=True, size=1):
    starttime = starttime
    endtime = endtime
    filters = copy.copy(filters)
    es_filters = {'filter': filters}
    if starttime and endtime:
        es_filters['filter'].insert(0, {'range': {timestamp_field: {'gt': starttime,
                                                                    'lte': endtime,
                                                                    "format": "epoch_millis"}}})
    if five:
        query = {'query': {'bool': es_filters}}
    else:
        query = {'query': {'filtered': es_filters}}
    if sort:
        query['sort'] = {timestamp_field: {'order': 'desc' if desc else 'asc'}}
    query['_source'] = source
    query['size'] = size
    return query


def preIndexDate(timeMs, format="%Y.%m.%d"):
    return time.strftime(format, time.localtime(timeMs / 1000))


def indexHandle(begin, end, index):
    dates = []
    baseMs = 3600 * 1000 * 24  # day
    # end = int(end)
    # begin = int(begin) + 8 * 3600 * 1000
    dateOffset = end - begin
    if dateOffset < baseMs * 2:
        begindate = preIndexDate(begin - 3600 * 1000 * 8)
        enddate = preIndexDate(end)
        dates = [begindate, enddate]
    elif dateOffset < baseMs * 10:
        begindate = preIndexDate(begin)
        enddate = preIndexDate(end)
        dt = datetime.datetime.strptime(begindate, "%Y.%m.%d")
        date = begindate[:]
        while date <= enddate:
            dates.append(date)
            dt = dt + relativedelta(days=1)
            date = dt.strftime("%Y.%m.%d")
    elif dateOffset < baseMs * 20:
        begindate = preIndexDate(begin)
        enddate = preIndexDate(end)
        dt = datetime.datetime.strptime(begindate, "%Y.%m.%d")
        date = begindate[:]
        while date <= enddate:
            dates.append(date[:-1] + "*")
            dt = dt + relativedelta(days=10)
            date = dt.strftime("%Y.%m.%d")
    else:
        begindate = preIndexDate(begin, "%Y.%m")
        enddate = preIndexDate(end, "%Y.%m")
        dt = datetime.datetime.strptime(begindate, "%Y.%m")
        date = begindate[:]
        while date <= enddate:
            dates.append(date + ".*")
            dt = dt + relativedelta(months=1)
            date = dt.strftime("%Y.%m")
    newIndex = ",springcloud-metricbeat-*-"
    indexs = newIndex.join(dates)
    return newIndex[1:] + indexs


class PublicProbe(Resource):
    def __init__(self):
        super(PublicProbe, self).__init__()
        self.now = time.time() - 10


class PodProbe(Resource):
    @staticmethod
    def getes(podname, location="1"):
        now = time.time() - 10
        strtime = time.strftime('%Y.%m.%d', time.localtime(now + 10))
        # url = _url % (strtime,strtime)
        url = _urldict[location] % (indexHandle(now * 1000, now * 1000, ""))
        # _request_body = {
        #     "size" : 1,
        #     "query": {
        #         "bool": {
        #             "filter": [{
        #                 "range": {
        #                     "@timestamp": {
        #                         "gte": int((now - 40) * 1000),
        #                         "lte": int(now * 1000),
        #                         "format": "epoch_millis"
        #                     }
        #                 }
        #             }, {
        #                 "query_string": {
        #                     "analyze_wildcard": True,
        #                     "query": "metricset.name:\"pod\" AND kubernetes.pod.name:(\"%s\")" % (podname)
        #                 }
        #             }
        #             ]}},
        #     "sort": {
        #         "@timestamp": {"order": "desc"}
        #     }
        # }

        basequery = {"query_string": {
            "analyze_wildcard": True,
            "query": "metricset.name:\"pod\" AND kubernetes.pod.name:(\"%s\")" % (podname)
        }}
        _request_body = get_query("*", [basequery], int((now - 40) * 1000), int(now * 1000))

        request_body = json.dumps(_request_body)
        data = pcreq.post(url, request_body)
        data = json.loads(data)
        data = data['hits']['hits'][0]['_source']['kubernetes']['pod']
        cpu_node_pct = data['cpu']['usage']['node']['pct']
        memory_usage = data['memory']['usage']['bytes']
        network_in = data['network']['rx']['bytes']
        network_out = data['network']['tx']['bytes']
        return {'CpuPct': cpu_node_pct, 'MemUsg': memory_usage, 'NetRx': network_in, 'NetTx': network_out}

    def get(self, podname):
        location = request.args.get("location")
        respon = PodProbe.getes(podname, location)
        for probe in respon:
            if probe == 'CpuPct':
                respon[probe] = pcnumf.numberPer(respon[probe] * 100, 0, 1)
            else:
                respon[probe] = pcnumf.bytesFormat(respon[probe], strShow=True)
        return (respon, 200, respon_header)


class SvcProbeDetail(Resource):
    def transfer(self, data):
        for probe in data:
            if probe == 'CpuPct':
                data[probe] = pcnumf.numberPer(data[probe] * 100, 0, 1)
            else:
                data[probe] = pcnumf.bytesFormat(data[probe], strShow=True)
        return None

    def get(self, svcname):
        responce = {}
        responce["other"] = []
        location = request.args.get("location")
        try:
            podnames = SvcProbe.getpodname(svcname, location=location)
        except:
            logutil.errmsgStringIO(traceback, "SvcProbeDetail Svc Error")
            return ({"code": "500", "data": "SvcProbeDetail Svc Error"}, 200, respon_header)
        TotalMem, TotalNetRx, TotalNetTx, TotalCpuPct = 0.0, 0.0, 0.0, 0.0
        try:
            podCount = 0
            for pod in podnames:
                try:
                    podprobe = PodProbe.getes(pod, location)
                    TotalMem = TotalMem + podprobe['MemUsg']
                    TotalNetRx = TotalNetRx + podprobe['NetRx']
                    TotalNetTx = TotalNetTx + podprobe['NetTx']
                    TotalCpuPct = TotalCpuPct + podprobe['CpuPct']
                    self.transfer(podprobe)
                    podprobe['podName'] = pod
                    responce["other"].append(podprobe)
                    podCount = podCount + 1
                except:
                    logutil.warnMsg("podname Error : " + pod)
            respon = {'TotalMem': TotalMem, 'TotalNetTx': TotalNetTx, 'TotalCpuPct': TotalCpuPct,
                      'TotalNetRx': TotalNetRx, 'TotalCount': podCount}
            for probe in respon:
                if probe == 'TotalCpuPct':
                    respon[probe] = pcnumf.numberPer(respon[probe] * 100, 0, 1)
                else:
                    respon[probe] = pcnumf.bytesFormat(respon[probe], strShow=True)
            responce["data"] = respon
            responce["code"] = 200
            return (responce, 200, respon_header)
        except:
            logutil.errmsgStringIO(traceback, 'Pod Error')
            return ({"code": "500", "data": "Pod Error"}, 200, respon_header)


class SvcProbe(Resource):
    def get(self, svcname):
        location = request.args.get("location")
        podnames = SvcProbe.getpodname(svcname, location=location)
        TotalMem, TotalNetRx, TotalNetTx, TotalCpuPct = 0.0, 0.0, 0.0, 0.0
        for pod in podnames:
            metricTotal = PodProbe.getes(pod, location)
            TotalMem = TotalMem + metricTotal['MemUsg']
            TotalNetRx = TotalNetRx + metricTotal['NetRx']
            TotalNetTx = TotalNetTx + metricTotal['NetTx']
            TotalCpuPct = TotalCpuPct + metricTotal['CpuPct']
        respon = {'TotalMem': TotalMem, 'TotalNetTx': TotalNetTx, 'TotalCpuPct': TotalCpuPct, 'TotalNetRx': TotalNetRx}
        for probe in respon:
            if probe == 'TotalCpuPct':
                respon[probe] = pcnumf.numberPer(respon[probe] * 100, 0, 1)
            else:
                respon[probe] = pcnumf.bytesFormat(respon[probe], strShow=True)
        return (respon, 200, respon_header)

    @staticmethod
    def getpodname(svcname, location="1"):
        now = time.time() - 11
        # _request_body = {
        #     "size" : 1,
        #     "query": {
        #         "bool": {
        #             "filter": [{
        #                 "range": {
        #                     "@timestamp": {
        #                         "gte": int((now - 30) * 1000),
        #                         "lte": int(now * 1000),
        #                         "format": "epoch_millis"
        #                     }
        #                 }
        #             }, {
        #                 "query_string": {
        #                     "analyze_wildcard": True,
        #                     "query": "docker.container.labels.name:\"%s\"" % (svcname)
        #                 }
        #             }
        #             ]}},
        #     "_source": [""],
        #     "aggs": {
        #         "1": {
        #             "terms": {"field": "docker.container.labels.io_kubernetes_pod_name"}
        #         }
        #     }
        # }
        basequery = {
            "query_string": {
                "analyze_wildcard": True,
                "query": "docker.container.labels.name:\"%s\"" % (svcname)
            }}
        _request_body = get_query("", [basequery], int((now - 50) * 1000), int(now * 1000))
        _request_body["aggs"] = {
            "1": {
                "terms": {"field": "docker.container.labels.io_kubernetes_pod_name", "size": 300}
            }
        }

        strtime = time.strftime('%Y.%m.%d', time.localtime(time.time()))
        # url = _newurl % (strtime, strtime)
        url = _urldict[location] % ("springcloud-metricbeat-*-" + strtime)
        request_body = json.dumps(_request_body)
        data = pcreq.post(url, request_body)
        data = json.loads(data)
        data = [podname['key'] for podname in data['aggregations']["1"]["buckets"]]
        return data


class PodProbeByTime(PublicProbe):
    def __init__(self):
        super(PodProbeByTime, self).__init__()
        try:
            FromTime = int(request.args.get('from'))
        except:
            FromTime = self.now - 900
        try:
            ToTime = int(request.args.get('to'))
        except:
            ToTime = self.now
        self.interval = pcnumf.timeInterval(FromTime, ToTime)
        self.FromTime = FromTime
        self.ToTime = ToTime
        strtime = time.strftime('%Y.%m.%d', time.localtime(ToTime + 10 - 8 * 60 * 60))
        nstrtime = time.strftime('%Y.%m.%d', time.localtime(FromTime + 10 - 8 * 60 * 60))
        # self.url = _url % (strtime, nstrtime)
        location = request.args.get("location")
        self.url = _urldict[location] % (
            indexHandle((self.FromTime + 10 - 8 * 60 * 60) * 1000, (self.ToTime + 10 - 8 * 60 * 60) * 1000, ""))
        self.metricset = ("CpuPct", "MemUsg", "NetTx", "NetRx")

    def getdw(self, data):
        dw = {}
        for _maxkey in data['aggregations']:
            if str(_maxkey) == 'CpuPct':
                dw[_maxkey] = "%"
            elif str(_maxkey) == 'groupDate':
                continue
            else:
                bytesValue = data['aggregations'][_maxkey]
                bytesValue = bytesValue['value']
                if float(bytesValue) > 1073741824:
                    dw[_maxkey] = "GB"
                elif float(bytesValue) > 1048576:
                    dw[_maxkey] = "MB"
                elif float(bytesValue) > 1024:
                    dw[_maxkey] = "KB"
                else:
                    dw[_maxkey] = "B"

    def get(self, podname):
        # _request_body = {
        #     "size": 0,
        #     "query": {
        #         "bool": {
        #             "filter": [{
        #                 "range": {
        #                     "@timestamp": {
        #                         "gte": int((self.FromTime - 100) * 1000),
        #                         "lte": int(self.ToTime * 1000),
        #                         "format": "epoch_millis"
        #                     }
        #                 }
        #             }, {
        #                 "query_string": {
        #                     "analyze_wildcard": True,
        #                     "query":  "metricset.name:\"pod\" AND kubernetes.pod.name:(\"%s\")" % (podname)
        #                 }
        #             }
        #             ]}
        #     },
        #     "aggs": {"groupDate": {
        #         "date_histogram": {
        #             "field": "@timestamp",
        #             "interval": str(self.interval) + "s"
        #         },
        #         "aggs": {
        #             "neto": {"avg": {"field": "kubernetes.pod.network.tx.bytes"}},
        #             "neti": {"avg": {"field": "kubernetes.pod.network.rx.bytes"}},
        #             "mem": {"avg": {"field": "kubernetes.pod.memory.usage.bytes"}},
        #             "cpu": {"avg": {"field": "kubernetes.pod.cpu.usage.node.pct"}}
        #         }},
        #         "NetTx": {"max": {"field": "kubernetes.pod.network.tx.bytes"}},
        #         "NetRx": {"max": {"field": "kubernetes.pod.network.rx.bytes"}},
        #         "MemUsg": {"max": {"field": "kubernetes.pod.memory.usage.bytes"}},
        #         "CpuPct": {"max": {"field": "kubernetes.pod.cpu.usage.node.pct"}}
        #     },
        #     "sort": {"@timestamp": {"order": "desc"}}
        # }

        basequery = {
            "query_string": {
                "analyze_wildcard": True,
                "query": "metricset.name:\"pod\" AND kubernetes.pod.name:(\"%s\")" % (podname)
            }}
        _request_body = get_query("*", [basequery], int((self.FromTime - 100) * 1000), int(self.ToTime * 1000))
        _request_body["aggs"] = {"groupDate": {
            "date_histogram": {
                "field": "@timestamp",
                "interval": str(self.interval) + "s"
            },
            "aggs": {
                "neto": {"avg": {"field": "kubernetes.pod.network.tx.bytes"}},
                "neti": {"avg": {"field": "kubernetes.pod.network.rx.bytes"}},
                "mem": {"avg": {"field": "kubernetes.pod.memory.usage.bytes"}},
                "cpu": {"avg": {"field": "kubernetes.pod.cpu.usage.node.pct"}}
            }},
            "NetTx": {"max": {"field": "kubernetes.pod.network.tx.bytes"}},
            "NetRx": {"max": {"field": "kubernetes.pod.network.rx.bytes"}},
            "MemUsg": {"max": {"field": "kubernetes.pod.memory.usage.bytes"}},
            "CpuPct": {"max": {"field": "kubernetes.pod.cpu.usage.node.pct"}}
        }

        request_body = json.dumps(_request_body)
        try:
            data = pcreq.post(self.url, request_body)
        except:
            return ({"code": "500", "data": "Post URL Error"}, 200, respon_header)
        try:
            data = json.loads(data)

            aggs = data['aggregations']["groupDate"]["buckets"]
            outer = {}
            inner = {}
            outer['code'] = 200
            outer['data'] = []
            for metric in self.metricset:
                inner[metric] = []
            dw = {}
            for _maxkey in data['aggregations']:
                if str(_maxkey) == 'CpuPct':
                    dw[_maxkey] = "%"
                elif str(_maxkey) == 'groupDate':
                    continue
                else:
                    bytesValue = data['aggregations'][_maxkey]
                    bytesValue = bytesValue['value']
                    if float(bytesValue) > 1073741824:
                        dw[_maxkey] = "GB"
                    elif float(bytesValue) > 1048576:
                        dw[_maxkey] = "MB"
                    elif float(bytesValue) > 1024:
                        dw[_maxkey] = "KB"
                    else:
                        dw[_maxkey] = "B"
            for agg in aggs:
                inner['CpuPct'].append([agg['key'], float(pcnumf.numberPer(agg['cpu']['value'] * 100, 0))])
                inner['MemUsg'].append([agg['key'], float(pcnumf.bytesFormat(agg['mem']['value'], type=dw['MemUsg']))])
                inner['NetRx'].append([agg['key'], float(pcnumf.bytesFormat(agg['neti']['value'], type=dw['NetRx']))])
                inner['NetTx'].append([agg['key'], float(pcnumf.bytesFormat(agg['neto']['value'], type=dw['NetTx']))])
            for key in inner:
                outer['data'].append({'dw': dw[key], 'type': key, 'data': inner[key]})

            return (outer, 200, respon_header)
        except:
            return ({"code": "404", "data": "Page not found"}, 200, respon_header)


class SysconProbe(PublicProbe):

    def getes(self, podname):
        basequery = {"query_string": {
            "analyze_wildcard": True,
            "query": "metricset.name:\"syscon\" AND kubernetes.pod.name:(\"%s\")" % (podname)
        }}
        now = time.time() - 40
        strtime = time.strftime('%Y.%m.%d', time.localtime(now + 20))
        _request_body = get_query("*", [basequery], int((now - 40) * 1000), int(now * 1000))
        request_body = json.dumps(_request_body)
        # url = _url % (strtime, strtime)
        location = request.args.get("location")
        url = _urldict[location] % (indexHandle(now * 1000, now * 1000, ""))
        data = pcreq.post(url, request_body)
        data = json.loads(data)
        try:
            data = data['hits']['hits'][0]
            data = data['_source']['k8spatch']['syscon']
        except Exception as err:
            return {'data': "no this pod " + str(err)}
        finWait2 = data['fin_wait2']
        established = data['established']
        finWait1 = data['fin_wait1']
        synRecv = data['syn_recv']
        synSent = data['syn_sent']
        timeWait = data['time_wait']
        closeWait = data['close_wait']

        return {'FinWait2': finWait2, 'FinWait1': finWait1, 'SynRecv': synRecv, 'SynSent': synSent,
                'TimeWait': timeWait, 'Established': established, 'CloseWait': closeWait}

    def get(self, name):
        try:
            # if not request.args.get('svc'):
            if not request.args.get('svc'):
                return (self.getes(name), 200, respon_header)
            elif not request.args.get('detail'):
                self.interval = 30
                return (self.getSvc(name), 200, respon_header)
            else:
                return (self.getAll(name), 200, respon_header)
        except Exception as err:
            return (err, 200, respon_header)

    def getAll(self, svcname):
        # podnames = SvcProbe.getpodname(svcname)
        # TotalSynS, TotalSynR, TotalCloseW, TotalTimeW, TotalEst, TotalFinW1, TotalFinW2 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        # for pod in podnames:
        #     getesdata = self.getes(pod)
        #     TotalFinW2 = TotalFinW2 +  getesdata['FinWait2']
        #     TotalFinW1 = TotalFinW1 +  getesdata['FinWait1']
        #     TotalSynR = TotalSynR +   getesdata['SynRecv']
        #     TotalSynS = TotalSynS +   getesdata['SynSent']
        #     TotalCloseW = TotalCloseW + getesdata['CloseWait']
        #     TotalTimeW = TotalTimeW + getesdata['TimeWait']
        #     TotalEst = TotalEst + getesdata['Established']
        #
        # respon = {'TotalFinW2': TotalFinW2, 'TotalFinW1': TotalFinW1, 'TotalSynR': TotalSynR,
        #           'TotalSynS': TotalSynS, 'TotalCloseW':TotalCloseW, 'TotalTimeW':TotalTimeW, 'TotalEst':TotalEst}
        # print(respon)
        # return respon

        responce = {}
        responce["other"] = []
        location = request.args.get("location")
        try:
            podnames = SvcProbe.getpodname(svcname, location=location)
        except:
            logutil.errmsgStringIO(traceback, "getAll Svc Error")
            return ({"code": "500", "data": "getAll Svc Error"}, 200, respon_header)
        TotalSynS, TotalSynR, TotalCloseW, TotalTimeW, TotalEst, TotalFinW1, TotalFinW2 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        try:
            podCount = 0
            for pod in podnames:
                try:
                    getesdata = self.getes(pod)
                    TotalFinW2 = TotalFinW2 + getesdata['FinWait2']
                    TotalFinW1 = TotalFinW1 + getesdata['FinWait1']
                    TotalSynR = TotalSynR + getesdata['SynRecv']
                    TotalSynS = TotalSynS + getesdata['SynSent']
                    TotalCloseW = TotalCloseW + getesdata['CloseWait']
                    TotalTimeW = TotalTimeW + getesdata['TimeWait']
                    TotalEst = TotalEst + getesdata['Established']
                    getesdata['podName'] = pod
                    responce["other"].append(getesdata)
                    podCount = podCount + 1
                except:
                    logutil.warnMsg("podname Error : " + pod)
            respon = {'TotalFinW2': TotalFinW2, 'TotalFinW1': TotalFinW1, 'TotalSynR': TotalSynR,
                      'TotalSynS': TotalSynS, 'TotalCloseW': TotalCloseW, 'TotalTimeW': TotalTimeW,
                      'TotalEst': TotalEst, 'TotalCount': podCount}
            responce["data"] = respon
            responce["code"] = 200
            return responce
        except:
            return {"code": "500", "data": "Pod Error"}

    def getSvc(self, svcname):
        basequery = {"query_string": {
            "analyze_wildcard": True,
            # "query": "metricset.name:\"syscon\" AND kubernetes.labels.name:(\"%s\")" % (svcname)
            "query": "metricset.name:\"syscon\" AND kubernetes.labels.app:(\"%s\")" % (svcname)
        }}
        now = time.time() - 40
        strtime = time.strftime('%Y.%m.%d', time.localtime(now + 20))
        _request_body = get_query("*", [basequery], int((now - 40) * 1000), int(now * 1000))
        _request_body["aggs"] = {"groupDate": {
            "date_histogram": {
                "field": "@timestamp",
                "interval": str(self.interval) + "s"
            },
            "aggs": {
                "closewait": {"sum": {"field": "k8spatch.syscon.close_wait"}},
                "synrecv": {"sum": {"field": "k8spatch.syscon.syn_recv"}},
                "synsent": {"sum": {"field": "k8spatch.syscon.syn_sent"}},
                "timewait": {"sum": {"field": "k8spatch.syscon.time_wait"}},
                "finwait1": {"sum": {"field": "k8spatch.syscon.fin_wait1"}},
                "finwait2": {"sum": {"field": "k8spatch.syscon.fin_wait2"}},
                "established": {"sum": {"field": "k8spatch.syscon.established"}}
            }}
        }

        request_body = json.dumps(_request_body)
        # url = _url % (strtime, strtime)
        location = request.args.get("location")
        url = _urldict[location] % (indexHandle(now * 1000, now * 1000, ""))
        data = pcreq.post(url, request_body)
        data = json.loads(data)
        data = data['aggregations']["groupDate"]["buckets"][0]

        finWait2 = data['finwait2']['value']
        established = data['established']['value']
        finWait1 = data['finwait1']['value']
        synRecv = data['synrecv']['value']
        synSent = data['synsent']['value']
        timeWait = data['timewait']['value']
        closeWait = data['closewait']['value']

        return {'FinWait2': finWait2, 'FinWait1': finWait1, 'SynRecv': synRecv, 'SynSent': synSent,
                'TimeWait': timeWait, 'Established': established, 'CloseWait': closeWait}

    def transfer(self):
        pass


class SysconProbeByTime(PublicProbe):
    def __init__(self):
        super(SysconProbeByTime, self).__init__()
        try:
            FromTime = int(request.args.get('from'))
        except:
            FromTime = self.now - 900
        try:
            ToTime = int(request.args.get('to'))
        except:
            ToTime = self.now
        self.interval = pcnumf.timeInterval(FromTime, ToTime)
        self.FromTime = FromTime
        self.ToTime = ToTime
        strtime = time.strftime('%Y.%m.%d', time.localtime(ToTime + 10 - 8 * 60 * 60))
        nstrtime = time.strftime('%Y.%m.%d', time.localtime(FromTime + 10 - 8 * 60 * 60))
        # self.url = _url % (strtime, nstrtime)
        location = request.args.get("location")
        self.url = _urldict[location] % (
            indexHandle((self.FromTime + 10 - 8 * 60 * 60) * 1000, (self.ToTime + 10 - 8 * 60 * 60) * 1000, ""))

    def get(self, podname):
        # _request_body = {
        #     "size": 0,
        #     "query": {
        #         "bool": {
        #             "filter": [{
        #                 "range": {
        #                     "@timestamp": {
        #                         "gte": int((self.FromTime - 100) * 1000),
        #                         "lte": int(self.ToTime * 1000),
        #                         "format": "epoch_millis"
        #                     }
        #                 }
        #             }, {
        #                 "query_string": {
        #                     "analyze_wildcard": True,
        #                     "query":  "metricset.name:\"pod\" AND kubernetes.pod.name:(\"%s\")" % (podname)
        #                 }
        #             }
        #             ]}
        #     },
        #     "aggs": {"groupDate": {
        #         "date_histogram": {
        #             "field": "@timestamp",
        #             "interval": str(self.interval) + "s"
        #         },
        #         "aggs": {
        #             "neto": {"avg": {"field": "kubernetes.pod.network.tx.bytes"}},
        #             "neti": {"avg": {"field": "kubernetes.pod.network.rx.bytes"}},
        #             "mem": {"avg": {"field": "kubernetes.pod.memory.usage.bytes"}},
        #             "cpu": {"avg": {"field": "kubernetes.pod.cpu.usage.node.pct"}}
        #         }},
        #         "NetTx": {"max": {"field": "kubernetes.pod.network.tx.bytes"}},
        #         "NetRx": {"max": {"field": "kubernetes.pod.network.rx.bytes"}},
        #         "MemUsg": {"max": {"field": "kubernetes.pod.memory.usage.bytes"}},
        #         "CpuPct": {"max": {"field": "kubernetes.pod.cpu.usage.node.pct"}}
        #     },
        #     "sort": {"@timestamp": {"order": "desc"}}
        # }

        basequery = {"query_string": {
            "analyze_wildcard": True,
            "query": "metricset.name:\"syscon\" AND kubernetes.pod.name:(\"%s\")" % (podname)
        }}

        _request_body = get_query("*", [basequery], int((self.FromTime - 100) * 1000), int(self.ToTime * 1000))
        _request_body["aggs"] = {"groupDate": {
            "date_histogram": {
                "field": "@timestamp",
                "interval": str(self.interval) + "s"
            },
            "aggs": {
                "closewait": {"avg": {"field": "k8spatch.syscon.close_wait"}},
                "synrecv": {"avg": {"field": "k8spatch.syscon.syn_recv"}},
                "synsent": {"avg": {"field": "k8spatch.syscon.syn_sent"}},
                "timewait": {"avg": {"field": "k8spatch.syscon.time_wait"}},
                "finwait1": {"avg": {"field": "k8spatch.syscon.fin_wait1"}},
                "finwait2": {"avg": {"field": "k8spatch.syscon.fin_wait2"}},
                "established": {"avg": {"field": "k8spatch.syscon.established"}}
            }}
        }

        request_body = json.dumps(_request_body)
        try:
            data = pcreq.post(self.url, request_body)
        except:
            return ({"code": "500", "data": "Post URL Error"}, 200, respon_header)
        try:
            data = json.loads(data)
            outer, inner = {}, {}
            aggs = data['aggregations']["groupDate"]["buckets"]
            outer['code'] = 200
            for agg in aggs:
                inner.setdefault('closewait', []).append([agg['key'], agg['closewait']['value']])
                inner.setdefault('synrecv', []).append([agg['key'], agg['synrecv']['value']])
                inner.setdefault('synsent', []).append([agg['key'], agg['synsent']['value']])
                inner.setdefault('finwait1', []).append([agg['key'], agg['finwait1']['value']])
                inner.setdefault('finwait2', []).append([agg['key'], agg['finwait2']['value']])
                inner.setdefault('timewait', []).append([agg['key'], agg['timewait']['value']])
                inner.setdefault('established', []).append([agg['key'], agg['established']['value']])
            for key in inner:
                outer.setdefault('data', []).append({'name': key, 'data': inner[key]})
            return (outer, 200, respon_header)
        except Exception as err:
            print(err)
            return ({"code": "404", "data": err}, 200, respon_header)

class statusBytimeController(Resource):
    def post(self , appName , location = 1):
        fullName = appName
        if location == 1:
            fullName = fullName + ".inm.com"
        startTimestamp = paramUtil.postGetInt(request , "startTimestamp")
        endTimestamp = paramUtil.postGetInt(request , "endTimestamp")
        return (json.loads(JsonResultUtil.__sucessful__(k8sEntryAccessService.statusBytime(startTimestamp , endTimestamp , fullName))), 200 , respon_header)

class k8sEntryAccess(Resource):
    def post(self , appName , location = 1):
        fullName = appName
        if location == 1:
            fullName = fullName + ".inm.com"
        startTimestamp = paramUtil.postGetInt(request , "startTimestamp")
        endTimestamp = paramUtil.postGetInt(request , "endTimestamp")
        return (json.loads(JsonResultUtil.__sucessful__(k8sEntryAccessService.urlStatusService(startTimestamp , endTimestamp , fullName))), 200 , respon_header)

class k8sEntryAccessTotal(Resource):
    def post(self , appName , location = 1):
        fullName = appName
        if location == 1:
            fullName = fullName + ".inm.com"
        startTimestamp = paramUtil.postGetInt(request , "startTimestamp")
        endTimestamp = paramUtil.postGetInt(request , "endTimestamp")
        return (json.loads(JsonResultUtil.__sucessful__(k8sEntryAccessService.accessTotalStatus(startTimestamp , endTimestamp , fullName))), 200 , respon_header)




if __name__ == "__main__":
    print(indexHandle(int(1573283357) * 1000, time.time() * 1000, ''))
    # now = time.time()
    # svcname = "xxx"
    # basequery = {
    #     "query_string": {
    #         "analyze_wildcard": True,
    #         "query": "docker.container.labels.name:\"%s\"" % (svcname)
    #     }}
    # _request_body = get_query("", [basequery], int((now - 30) * 1000), int(now * 1000))
    # _request_body["aggs"] = {
    #     "1": {
    #         "terms": {"field": "docker.container.labels.io_kubernetes_pod_name"}
    #     }
    # }
    # print(_request_body)
    # print(SysconProbe().get("test"))
    # print(SysconProbeByTime().get("test-deployment-554fc949f7-ck2hm"))
    # print(PodProbe().get("test-deployment-554fc949f7-ck2hm"))
