#!/usr/bin/env python

# serve some json on a platter,
# make it fresh.

import zohmgapp

if __name__ == '__main__':
    import sys,time
    import simplejson as json
    from paste import httpserver
    sys.stderr.write(time.asctime() + " - service ready.\n")
    zohmg = zohmgapp.zohmg("webmetrics")
    httpserver.serve(zohmg.app, host='localhost', port='8086')
    print "ok, done."