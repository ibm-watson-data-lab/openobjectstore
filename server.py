# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
The docstring for a module should generally list the classes,
exceptions and functions (and any other objects) that are exported by
the module, with a one-line summary of each.
"""

# import collections
import json
import os
# import time
# import urllib

# import requests
# for objectstorage
import swiftclient
from flask import Flask, Response #, jsonify, request, send_file
from keystoneclient import client
from swiftclient import ClientException
from swiftclient.service import SwiftService, SwiftError

PORT = os.getenv('VCAP_APP_PORT', '5000')
app = Flask(__name__)

if 'VCAP_SERVICES' in os.environ:
    credinfo = json.loads(os.environ['VCAP_SERVICES'])['Object-Storage'][0]['credentials']
    authurl = credinfo['auth_url'] + '/v3'
    projectId = credinfo['projectId']
    region = credinfo['region']
    userId = credinfo['userId']
    password = credinfo['password']
    projectname = credinfo['project']
    domainName = credinfo['domainId']

thehost = "http://0.0.0.0:5000"
if 'VCAP_APPLICATION' in os.environ:
    appinfo = json.loads(os.environ['VCAP_APPLICATION'])
    thehost = "https://" + appinfo['application_uris'][0]

@app.route('/')
def Welcome():
    return app.send_static_file("index.html")

@app.route('/obj', methods=['GET'])
def GetObjStoreInfo():
    try:
        ibmobjectstoreconn = swiftclient.Connection(key=password, authurl=authurl, auth_version='3', os_options={"project_id": projectId,"user_id": userId,"region_name": region})
        conns = []
        for container in ibmobjectstoreconn.get_account()[1]:
            container['accessURL'] = thehost + "/obj/" + container['name']
            container['objects'] = container['count']
            del container['count'] 
            conns.append(container)
        jconns = '{"containers":'+json.dumps(conns)+'}'
        return Response(jconns, mimetype='application/json', status=200)
    except ClientException as ce:
        return MakeJSONMsgResponse({"message":ce.msg,"containername":container,"filename":filename}, 404)

@app.route('/obj/<container>', methods=['GET'])
def GetObjStoContainerInfo(container):
    try:
        ibmobjectstoreconn = swiftclient.Connection(key=password, authurl=authurl, auth_version='3', os_options={"project_id": projectId,"user_id": userId,"region_name": region})
        objs = []
        for data in ibmobjectstoreconn.get_container(container)[1]:
            del data['hash']
            data['downloadURL'] = thehost + "/obj/" + container + "/" + data['name']
            objs.append(data)
        jobjs = '{"objects":'+json.dumps(objs)+'}'
        return Response(jobjs, mimetype='application/json', status=200)
    except ClientException as ce:
        return MakeJSONMsgResponse({"message":ce.msg+". Bad container name?","containername":container}, 404)

@app.route('/obj/<container>/<filename>', methods=['GET'])
def GetObjectStorage(container, filename):
    if 'VCAP_SERVICES' not in os.environ:
        return MakeJSONMsgResponse({"message":"cannot authenticate"}, 500)

    try:
        ibmobjectstoreconn = swiftclient.Connection(key=password, authurl=authurl, auth_version='3', os_options={"project_id": projectId,"user_id": userId,"region_name": region})
        obj = ibmobjectstoreconn.get_object(container, filename)

        if filename.endswith('.txt'):
            return Response(obj[1], mimetype='text/plain', status=200)
        elif filename.endswith('.csv'):
            return Response(obj[1], mimetype='text/csv', status=200)
        elif filename.endswith('.json'):
            return Response(obj[1], mimetype='application/json', status=200)
        else:
            return Response(obj[1], mimetype='application/binary', status=200)
    except ClientException as ce:
        return MakeJSONMsgResponse({"message":ce.msg,"containername":container,"filename":filename}, 404)

def MakeJSONMsgResponse(themsg, statuscode):
    return Response(json.dumps(themsg), mimetype='application/json', status=statuscode)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(PORT), threaded=True, debug=True)
