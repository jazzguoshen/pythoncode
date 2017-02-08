# -*- coding: utf-8 -*-


from docker import Client
from docker import errors
import base64
import binascii

cli = Client(version='auto', base_url='tcp://127.0.0.1:2375')
result =  cli.containers()
print result

import sys
print(sys.getdefaultencoding())

cmd = './Jx3RobotD -T SuperRobot:10 -a huou -r 互殴 -l -e -k 随机 -j 随机 -g 随机 -s 10.20.96.155 -p 1'

cmd.decode('utf8').encode('gb2312')

print cmd

dumpdata = base64.b64encode(cmd)

print 'dumpdata:', dumpdata

www = 'Li9KeDNSb2JvdEQgIC1UIFN1cGVyUm9ib3Q6MTAgICAtYSBodW91IC1yILulxbkgICAgLWwgLWUgICAtayDL5rv6IC1qIMvmu/ogLWcgy+a7+iAgLXMgMTAuMjAuOTYuMTU1IC1wIDEx'

ddd = base64.b64decode(www)

print ddd
