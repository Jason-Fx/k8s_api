# coding=utf-8
import json
import traceback

import sys
from flask import Response

from pcGroup.log.logUtil import logUtil
from pcGroup.util.requestUtil import logutil
logutil = logUtil()

class Error:
    def __init__(self,error):
        # type: (object) -> object
        self.error=error
    def get_error_info(self):
        data = {}
      ##  data['k8scode'] = self.error.status
        data['message'] = json.loads(self.error.body)['message']
        data['k8scode']=self.error.status
        #return data
        return Response(data['message'], data['k8scode'])

    def get_status(self):
        data={}
        body=self.error.body
        status=self.error.status
        data['body']=body
        data['k8scode']=status
        return Response(data['body'],data['k8scode'])

    def get_code(self,data=None):
        if data == None:
            data = {}
        try:
            code = self.error.body
            logutil.infoMsg(self.error.body)
            code=json.loads(code)
            data['k8scode'] = int(code['code'])
            return Response(json.dumps(data), mimetype='application/json')
        except (Error,Exception) as e:
            logutil.errmsgStringIO(traceback,str(self.error))
            data['k8scode']=404
           # data['error_message']=str(e)
            return Response(json.dumps(data),mimetype='application/json')






