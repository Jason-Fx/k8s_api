from common import Constant
from control import configure


def init(object, region):
    # if not RegionDict().has_key(region):
    ##default region
    #    region =1
    v1client = configure.api_client(Constant.platformCode(region)).v1client
    v1betaclient = configure.api_client(Constant.platformCode(region)).v1betaclient
    appsv1client = configure.api_client(Constant.platformCode(region)).appsv1api
    object.v1client = v1client
    object.v1betaclient = v1betaclient
    object.appsv1api = appsv1client
    object.clustername = region
    print "connect:" + object.v1client.api_client.configuration.host
    print "connect:" + object.appsv1api.api_client.configuration.host
