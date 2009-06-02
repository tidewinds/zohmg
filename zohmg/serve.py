#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

import time

class Dispatch(object):
    def __init__(self, project_dir):
        from paste.urlparser import make_url_parser
        self.project_dir = project_dir
        # TODO: middleware app directory is hard wired.
        # TODO: why must we read files from file system? why not import the stuff we need?
        self.dispatch = make_url_parser({}, "/usr/local/lib/zohmg/middleware", "")
        print "[%s] Initialized data server dispatcher. Serving from %s." % (time.asctime(), project_dir)

    def __call__(self, environ, start_response):
        environ["zohmg_project_dir"] = self.project_dir
        print "[%s] Dispatching..." % time.asctime()
        return self.dispatch(environ, start_response)

def start(project_dir, host="localhost", port="8086"):
    from paste import httpserver
    app = Dispatch(project_dir)
    httpserver.serve(app, host=host, port=port)
