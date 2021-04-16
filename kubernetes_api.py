# coding=utf-8
import json , os , sys
import alert.K8sAlert
sys.path.append(".")

from flask import Flask
from flask_restful import Api

import K8S_probe




import K8SInfo
import K8S_resouse
app = Flask(__name__)
api = Api(app)


if __name__ == '__main__':
    #daemon=app.run(host='0.0.0.0',port=5000,debug=True)
    api.add_resource(K8S_resouse.services_resource, '/api/v1/services/','/api/v1/services/<string:jobName>')
    api.add_resource(K8S_resouse.services_ip, '/api/v1/services/svc_ip/', '/api/v1/services/svc_ip/<string:jobName>')
    api.add_resource(K8S_resouse.deployment_resource, '/api/v1/deployments/', '/api/v1/deployments/<string:jobName>')
    api.add_resource(K8S_resouse.deployment_get_arg, '/api/v1/deployments/depArgsMsg/', '/api/v1/deployments/depArgsMsg/<string:jobName>')
    api.add_resource(K8S_resouse.endpoint_resource, '/api/v1/endpoints/', '/api/v1/endpoints/<string:jobName>')
    api.add_resource(K8S_resouse.pod_resource, '/api/v1/pods/', '/api/v1/pods/<string:jobName>')
    api.add_resource(K8S_resouse.pods_ip_with_create_status, '/api/v1/pods/ip_status/create/', '/api/v1/pods/ip_status/create/<string:jobName>')
    api.add_resource(K8S_resouse.pods_ip_with_delete_status, '/api/v1/pods/ip_status/delete/', '/api/v1/pods/ip_status/delete/<string:jobName>')
    api.add_resource(K8S_resouse.deployment_rs_status, '/api/v1/deployments/rs_status/', '/api/v1/deployments/rs_status/<string:jobName>')
    api.add_resource(K8S_resouse.getlog, '/api/v1/podlog/','/api/v1/podlog/<string:jobName>')
    api.add_resource(K8S_resouse.ingress_rule, '/api/v1/ingress/','/api/v1/ingress/<string:mName>')
    api.add_resource(K8S_resouse.ingress_rule_list,'/api/v1/list_ingress/','/api/v1/list_ingress/')

    api.add_resource(K8S_resouse.jenkins_all_delete,'/api/v1/cleanjob/',"/api/v1/cleanjob/<string:jobName>")
    api.add_resource(K8SInfo.podsList , '/api/v1/pods/list/' , '/api/v1/pods/list/')
    api.add_resource(K8SInfo.podsInfo , '/api/v1/pods/info/' , '/api/v1/pods/info/<string:name>/<int:page>')
    api.add_resource(K8SInfo.nodesList, '/api/v1/nodes/list/', '/api/v1/nodes/list/')

    api.add_resource(K8SInfo.svcList, '/api/v1/svc/list' , '/api/v1/svc/list/')
    api.add_resource(K8SInfo.namespaceList , '/api/v1/namespace/list' , '/api/v1/namespace/list')

    api.add_resource(K8S_resouse.deploymentList , '/api/v1/deployments/list' , '/api/v1/deployments/list')
    api.add_resource(K8S_resouse.statefulsetList , '/api/v1/statefulsets/list' , '/api/v1/statefulsets/list')
    api.add_resource(K8S_resouse.getAvailableReplicas , '/api/v1/deployments/availableReplicas' , '/api/v1/deployments/availableReplicas')



    #probe and alert
    api.add_resource(K8S_probe.PodProbe,'/api/podprobe/<string:podname>')
    api.add_resource(K8S_probe.SysconProbe, '/api/sysconprobe/<string:name>')
    api.add_resource(K8S_probe.SysconProbeByTime, '/api/sysconbytime/<string:podname>')
    api.add_resource(K8S_probe.SvcProbe, '/api/serviceprobe/<string:svcname>')
    api.add_resource(K8S_probe.PodProbeByTime,'/api/probebytime/<string:podname>')
    api.add_resource(K8S_probe.SvcProbeDetail, '/api/svcpodprobe/<string:svcname>')
    api.add_resource(alert.K8sAlert.AlertNow,'/api/alertnow')
    api.add_resource(alert.K8sAlert.AlertList, '/api/alertlist/<string:probetype>')

    #k8sEntryAccess
    api.add_resource(K8S_probe.statusBytimeController , '/api/k8sEntryStatusBytime/' , '/api/k8sEntryStatusBytime/<string:appName>')
    api.add_resource(K8S_probe.k8sEntryAccessTotal , '/api/k8sEntryAccessTotal/' , '/api/k8sEntryAccessTotal/<string:appName>')
    api.add_resource(K8S_probe.k8sEntryAccess , '/api/k8sEntryAccess/' , '/api/k8sEntryAccess/<string:appName>')

    app.run(host='0.0.0.0',port=5000,debug=False,threaded=True)


