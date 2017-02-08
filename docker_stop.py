# -*- coding: utf-8 -*-

import urllib
import urllib2


test_data = {'image':'jxrobotimage',
    'num':'1',

    'volumes':'/home/libg/Jx3Robot/Jx3Robot',

    'prodir':'/home/libg/Jx3Robot/Jx3Robot',

    'procmd':'./Jx3RobotD  -T SuperRobot:28    -a ouda -r 殴打   -t -l -e   -k 随机 -j 随机 -g 随机  -s 10.20.77.163 -p 1'}

test_data_urlencode = urllib.urlencode(test_data)

requrl = "http://10.20.102.228:5000/dockerstop"

req = urllib2.Request(url = requrl,data =test_data_urlencode)

print req

res_data = urllib2.urlopen(req)

res = res_data.read()

print res
