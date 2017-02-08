# -*- coding: utf-8 -*-

from docker import Client
from docker import errors
import base64
import binascii




def sss(ddd):
    ddd = [9,9,9,9]

cli = Client(version='auto', base_url='tcp://127.0.0.1:2375')
result =  cli.containers()
print '\n\n'
print result

zzz = 'sh /home/run.sh /home/libg/Jx3Robot/Jx3Robot Li9KeDNSb2JvdEQgLVQgU3VwZXJSb2JvdDo1MCAtYSBsYWl0dWFuIC1yIMC0zcWwySAtbCAtZSAtayDL5rv6IC1qIMvmu/ogLWcgy+a7+iAtcyAxMC4yMC45Ni4xNTUgLXAgMTAw'
ppp = zzz.split(' ')

print ppp

print ppp[2]

print ppp[3]

#procmd.decode('utf8').encode('gb2312')

rrr = base64.b64decode(ppp[3])

print rrr

ttt = rrr.decode('gb2312').encode('utf8')

print ttt

kkk = [1,2,3,4]
for v in kkk:
    v = v + 1

print kkk

sss(kkk)

print kkk
