# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from random import Random
import socket
import curses
import os
import re
import datetime
import base64
import binascii
from docker import Client
from docker import errors
from pymongo import MongoClient
import logging
from logging.handlers import RotatingFileHandler
import subprocess
from flask import Flask, render_template, Response, send_from_directory
from flask import request
from flask import *
app = Flask(__name__, static_url_path='/root/docker_server')
app.debug = True

Rthandler = RotatingFileHandler('./logs/jxrobot_docker_server.log', maxBytes=10*1024*1024,backupCount=5)
Rthandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
Rthandler.setFormatter(formatter)
logging.getLogger('').addHandler(Rthandler)
logging.getLogger('').setLevel(logging.INFO)

gstoredb = None

def GetStoredb():
    global gstoredb
    if not gstoredb:
        gstoredb = MongoClient('mongodb://10.20.102.135:27017/')
    return gstoredb

def DockerClient(serverip):
    return Client(version='auto', base_url='tcp://%s:2375' % serverip)

def random_str(randomlength=15):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

def query_image_server(image_name):
    image_server = {}
    db = GetStoredb()
    collect = db['dockerdb']['image_server']
    result = collect.find({'image': image_name})
    if not result:
        return None
    for v in result:
        image_server[v['host']] = int(v['limit'])

    return image_server

def query_container_server(image_name, image_server):
    host_containers = {}
    for host,value in image_server.iteritems():
        cons = []
        cli = DockerClient(host)
        result =  cli.containers()
        for v in result:
            if v['Image'] == image_name:
                cons.extend(v['Names'])
        host_containers[host] = cons

    return host_containers

def query_containers(image_name, image_server, host_list):
    host_containers = {}
    for host,value in image_server.iteritems():
        if host_list and host not in host_list:
            continue

        cons = []
        cli = DockerClient(host)
        result =  cli.containers()
        for v in result:
            if v['Command']:
                command = v['Command'].split(' ')
                if len(command) > 3:
                    v['prodir'] = command[2]

                    codecmd = base64.b64decode(command[3])
                    v['procmd'] = codecmd.decode('gb2312').encode('utf8') 

            if v['Created']:
                dateArray = datetime.datetime.fromtimestamp(int(v['Created']))
                v['CreateTime'] = dateArray.strftime("%Y-%m-%d %H:%M:%S")
        
            if v['Image'] == image_name:
                cons.append(v)
        host_containers[host] = cons

    return host_containers

def stop_container_server(image_name, image_server, host_list):
    host_containers = {}
    for host,value in image_server.iteritems():
        if host_list and host not in host_list:
            continue

        cli = DockerClient(host)
        result =  cli.containers()
        for v in result:
            if v['Image'] == image_name:
                cli.stop(v['Id'])

def check_container_server(image_server, container_server):
    host_limit = {}
    for host,limit in image_server.iteritems():
        host_limit[host] = limit - len(container_server[host])

    return host_limit


def limit_container_server(image_server, container_server):
    host_limit = {}
    for host,limit in image_server.iteritems():
        host_limit[host] = {'limit': limit, 'running': len(container_server[host])}

    return host_limit

def check_host_limit(host_limit, num):
    total = 0
    for host,limit in host_limit.iteritems():
        total += limit

    if total < num:
        return True

    return False

def DockerContainerStart(cli,image_name,num,prodir,cmd_list,volumes):
    volumes_conf = []
    binds_conf = []
    if volumes and len(volumes) > 1:
        volumes_list = volumes.split('||')
        for v in volumes_list:
            if len(v) > 1:
                volumes_conf.append(v)
                binds_conf.append('%s:%s' % (v,v))

    cnt = 0
    host_config=cli.create_host_config(binds=binds_conf)

    while cnt < num:
        procmd = ''
        if len(cmd_list) > 0:
            procmd = cmd_list[0]
            cmd_list.remove(cmd_list[0])

        command='sh /home/run.sh %s "%s"' % (prodir, procmd)

        container = cli.create_container(image=image_name,
                                         volumes=volumes_conf,
                                         host_config=host_config,
                                         name=random_str(),
                                         command=command)

        response = cli.start(container=container.get('Id'))

        cnt += 1

def DockerContainerBatchStart(host_limit, image_name, num, prodir, cmd_list, volumes):
    sum = 0
    for host,limit in host_limit.iteritems():
        if sum < num:
            cli = DockerClient(host)
            if (num - sum) > limit:
                DockerContainerStart(cli,image_name,limit,prodir,cmd_list,volumes)
                sum += limit
            else:
                DockerContainerStart(cli,image_name,(num - sum),prodir,cmd_list,volumes)
                sum = num
        else:
            break


@app.route('/')
def index():
    #return 'NONE!'
    return send_from_directory(os.getcwd(), 'main.html')

@app.route('/create',  methods=['POST', 'GET'])
def create():
    return send_from_directory(os.getcwd(), 'create.html')


@app.route('/query',  methods=['POST', 'GET'])
def query():
    return send_from_directory(os.getcwd(), 'query.html')


@app.route('/stop',  methods=['POST', 'GET'])
def stop():
    return send_from_directory(os.getcwd(), 'stop.html')

@app.route('/limit',  methods=['POST', 'GET'])
def limit():
    return send_from_directory(os.getcwd(), 'limit.html')

@app.route('/plan',  methods=['POST', 'GET'])
def plan():
    return send_from_directory(os.getcwd(), 'setplan.html')

@app.route('/plansearch',  methods=['POST', 'GET'])
def plansearch():
    return send_from_directory(os.getcwd(), 'planquery.html')

@app.route('/plansave',  methods=['POST', 'GET'])
def plansave():
    image_name = None
    volumes = None
    procmd_list = []
    cmd_list = []
    prodir = None
    procmd = None
    planname = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    #获取镜像名称
    if request.args.get('planname', ''):
        planname = request.args.get('planname', '')
    if request.form.get('planname', ''):
        planname = request.form.get('planname', '')

    #获取挂载目录配置
    if request.args.get('volumes', ''):
        volumes = request.args.get('volumes', '')
    if request.form.get('volumes', ''):
        volumes = request.form.get('volumes', '')

    #获取程序目录
    if request.args.get('prodir', ''):
        prodir = request.args.get('prodir', '')
    if request.form.get('prodir', ''):
        prodir = request.form.get('prodir', '')

    #获取程序命令
    procmd_list = request.form.getlist('procmd')
    if procmd_list and len(procmd_list) > 0:
        for procmd in procmd_list:
            procmd = procmd.decode('utf8').encode('gb2312')
            procmd =  base64.b64encode(procmd)
            cmd_list.append(procmd)

    if not image_name or not planname:
        return render_template('error.html',errmsg='image name and plan_name must be not null')

    try:
        planinfo = {}
        planinfo['image_name'] = image_name
        planinfo['volumes'] = volumes
        planinfo['procmd_list'] = procmd_list
        planinfo['cmd_list'] = cmd_list
        planinfo['prodir'] = prodir
        planinfo['planname'] = planname

        #保存方案
        db = GetStoredb()
        result = db['dockerdb']['docker_container_plan'].update(
                {'planname': planname, "image_name": image_name},
                planinfo,
                True
            )

        planlist = db['dockerdb']['docker_container_plan'].find({'image_name': image_name, 'planname': planname})

        if not planlist:
            return None

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('plan.html',planlist=planlist)

@app.route('/planquery',  methods=['POST', 'GET'])
def planquery():
    image_name = None
    planname = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    #获取方案名称
    if request.args.get('planname', ''):
        planname = request.args.get('planname', '')
    if request.form.get('planname', ''):
        planname = request.form.get('planname', '')


    if not image_name and not planname:
        return render_template('error.html',errmsg='image name and plan_name must be not null')

    try:
        #查询方案
        db = GetStoredb()

        if image_name and planname:
            planlist = db['dockerdb']['docker_container_plan'].find({'image_name': image_name, 'planname': planname})
        elif image_name and not planname:
            planlist = db['dockerdb']['docker_container_plan'].find({'image_name': image_name})
        else:
            planlist = db['dockerdb']['docker_container_plan'].find({'planname': planname})

        if not planlist:
            return None

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('plan.html',planlist=planlist)


@app.route('/plandel',  methods=['POST', 'GET'])
def plandel():
    image_name = None
    planname = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    #获取方案名称
    if request.args.get('planname', ''):
        planname = request.args.get('planname', '')
    if request.form.get('planname', ''):
        planname = request.form.get('planname', '')


    if not image_name or not planname:
        return render_template('error.html',errmsg='image name and plan_name must be not null')

    try:
        #查询方案
        db = GetStoredb()

        result = db['dockerdb']['docker_container_plan'].remove({'image_name': image_name, 'planname': planname})

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('del.html',planname=planname)


@app.route('/planstart',  methods=['POST', 'GET'])
def planstart():

    image_name = None
    planname = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    #获取方案名称
    if request.args.get('planname', ''):
        planname = request.args.get('planname', '')
    if request.form.get('planname', ''):
        planname = request.form.get('planname', '')

    if not image_name or not planname:
        return render_template('error.html',errmsg='image name and plan_name must be not null')

    #查询方案
    db = GetStoredb()
    planlist = db['dockerdb']['docker_container_plan'].find({'image_name': image_name, 'planname': planname})

    if not planlist :
        return render_template('error.html',errmsg='image name and planname must be not null')

    plan = planlist[0]

    volumes = plan['volumes']
    cmd_list = plan['cmd_list']
    num = len(cmd_list)
    prodir = plan['prodir']

    if not image_name :
        return render_template('error.html',errmsg='image name must be not null')

    try:
        #查询DB 获取image所在的机器
        image_server_list = query_image_server(image_name)
        if len(image_server_list) < 1:
            return render_template('error.html',errmsg='image server not found')

        #查询机器上image容器的情况
        container_server_list = query_container_server(image_name, image_server_list)

        #确定部署机器的ip
        host_limit = check_container_server(image_server_list, container_server_list)

        #检查是否超过启动上限
        if check_host_limit(host_limit, num):
            return render_template('error.html',errmsg='container process num over the limit')

        #启动容器
        DockerContainerBatchStart(host_limit, image_name, num, prodir, cmd_list, volumes)

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('plan_result.html',plan=plan)


@app.route('/dockerstart',  methods=['POST', 'GET'])
def dockerstart():
    image_name = None
    volumes = None
    num = 0
    procmd_list = []
    cmd_list = []
    prodir = None
    procmd = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    #获取挂载目录配置
    if request.args.get('volumes', ''):
        volumes = request.args.get('volumes', '')
    if request.form.get('volumes', ''):
        volumes = request.form.get('volumes', '')

    #获取程序目录
    if request.args.get('prodir', ''):
        prodir = request.args.get('prodir', '')
    if request.form.get('prodir', ''):
        prodir = request.form.get('prodir', '')

    #获取程序命令
    procmd_list = request.form.getlist('procmd')
    if procmd_list and len(procmd_list) > 0:
        num = len(procmd_list)
        for procmd in procmd_list:
            procmd = procmd.decode('utf8').encode('gb2312')
            procmd =  base64.b64encode(procmd)
            cmd_list.append(procmd)

    if not image_name :
        return render_template('error.html',errmsg='image name must be not null')

    try:
        #查询DB 获取image所在的机器
        image_server_list = query_image_server(image_name)
        if len(image_server_list) < 1:
            return render_template('error.html',errmsg='image server not found')

        #查询机器上image容器的情况
        container_server_list = query_container_server(image_name, image_server_list)

        #确定部署机器的ip
        host_limit = check_container_server(image_server_list, container_server_list)

        #检查是否超过启动上限
        if check_host_limit(host_limit, num):
            return render_template('error.html',errmsg='container process num over the limit')

        #启动容器
        DockerContainerBatchStart(host_limit, image_name, num, prodir, cmd_list, volumes)

    except Exception as e:
        return render_template('error.html',errmsg=str(e))


    return render_template('succ.html')

@app.route('/dockerstop', methods=['POST', 'GET'])
def dockerstop():

    image_name = None
    hosts = None
    host_list = None
 
    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    if request.args.get('host', ''):
        hosts = request.args.get('host', '')
    if request.form.get('host', ''):
        hosts = request.form.get('host', '')

    if not image_name :
        return render_template('error.html',errmsg='image name must be not null')
    
    if hosts and len(hosts) > 1:
        host_list = hosts.split(' ')

    try:
        #查询DB 获取image所在的机器
        image_server_list = query_image_server(image_name)
        if len(image_server_list) < 1:
            return render_template('error.html',errmsg='image server not found')
        
        #停止机器上image容器
        stop_container_server(image_name, image_server_list, host_list)

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('succ.html')

@app.route('/dockerquery', methods=['POST', 'GET'])
def dockerquery():

    image_name = None
    hosts = None
    host_list = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    if request.args.get('host', ''):
        hosts = request.args.get('host', '')
    if request.form.get('host', ''):
        hosts = request.form.get('host', '')

    if not image_name :
        return render_template('error.html',errmsg='image name must be not null')

    if hosts and len(hosts) > 1:
        host_list = hosts.split(' ')

    try:
        #查询DB 获取image所在的机器
        image_server_list = query_image_server(image_name)
        if len(image_server_list) < 1:
            return render_template('error.html',errmsg='image server not found')

        #查询机器上image容器
        containers = query_containers(image_name, image_server_list, host_list)

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('query_result.html',image_name=image_name,containers=containers)


@app.route('/dockerdel', methods=['POST', 'GET'])
def dockerdel():

    image_name = None
    container_id = None
    host = None
    host_list = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    if request.args.get('container_id', ''):
        container_id = request.args.get('container_id', '')
    if request.form.get('container_id', ''):
        container_id = request.form.get('container_id', '')

    if request.args.get('host', ''):
        host = request.args.get('host', '')
    if request.form.get('host', ''):
        host = request.form.get('host', '')

    if not image_name or not container_id or not host:
        return render_template('error.html',errmsg='image name and container id and host must be not null')

    try:
        cli = DockerClient(host)
        cli.stop(container_id)

        #查询DB 获取image所在的机器
        image_server_list = query_image_server(image_name)
        if len(image_server_list) < 1:
            return render_template('error.html',errmsg='image server not found')

        #查询机器上image容器
        containers = query_containers(image_name, image_server_list, host_list)

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('query_result.html',image_name=image_name,containers=containers)


@app.route('/dockerlimit', methods=['POST', 'GET'])
def dockerlimit():

    image_name = None

    #获取镜像名称
    if request.args.get('image', ''):
        image_name = request.args.get('image', '')
    if request.form.get('image', ''):
        image_name = request.form.get('image', '')

    if not image_name :
        return render_template('error.html',errmsg='image name must be not null')

    try:
        #查询DB 获取image所在的机器
        image_server_list = query_image_server(image_name)
        if len(image_server_list) < 1:
            return render_template('error.html',errmsg='image server not found')

        #查询机器上image容器的情况
        container_server_list = query_container_server(image_name, image_server_list)

        #汇总数据
        host_limit = limit_container_server(image_server_list, container_server_list)

    except Exception as e:
        return render_template('error.html',errmsg=str(e))

    return render_template('limit_result.html',image_name=image_name,host_limit=host_limit)


if __name__ == '__main__':
    
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    app.run(host='10.20.102.228')
