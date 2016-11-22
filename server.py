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
The docstring for a module should generally list the classes, exceptions and functions (and any other objects) that are exported by the module, with a one-line summary of each. 
"""

import collections
import json
import os
import time
import urllib

import requests
# for objectstorage
import swiftclient
from flask import Flask, Response, jsonify, request, send_file
from keystoneclient import client
from swiftclient import ClientException

PORT = os.getenv('VCAP_APP_PORT', '5000')
app = Flask(__name__)
JSC = {'Content-Type':'application/json'}

@app.route('/')
def Welcome():
    return app.send_static_file("index.html")


@app.route('/obj/<container>/<filename>', methods=['GET'])
def GetObjectStorage(container, filename):
    if container and filename:
        if 'VCAP_SERVICES' in os.environ:
            credinfo = json.loads(os.environ['VCAP_SERVICES'])['Object-Storage'][0]['credentials']
            authurl = credinfo['auth_url'] + '/v3'
            projectId = credinfo['projectId']
            region = credinfo['region']
            userId = credinfo['userId']
            password = credinfo['password']
        else:
            return ("cannot find vcap services", 500, {'Content-Type':'text/plain'})

        try:
            print "GETTING the object for container: "+container+" and filename: "+filename
            ibmobjectstoreconn = swiftclient.Connection(key=password, authurl=authurl, auth_version='3', os_options={"project_id": projectId,"user_id": userId,"region_name": region})
            obj = ibmobjectstoreconn.get_object(container, filename)
            print "Got the object for container: "+container+" and filename: "+filename

            if filename.endswith('.txt'):
                return Response(obj[1], mimetype='text/plain', status=200)
            elif filename.endswith('.csv'):
                return Response(obj[1], mimetype='text/csv', status=200)
            elif filename.endswith('.json'):
                return Response(obj[1], mimetype='application/json', status=200)
            else:
                return Response(obj[1], mimetype='application/binary', status=200)
        except ClientException as ce:
            themsg = '{"message":"'+ce.msg+'","containername":"'+container+'","filename":"'+filename+'"}'
            return (themsg, 404, JSC)

    else:
        return (json.dumps({'type':'Error: Bad Request', 'description':'missing parameter Object storage container name or file name or both. Usage: https://<hostname>.mybluemix.net/obj/containername/filename'}), 400, JSC)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(PORT), threaded=True, debug=True)
