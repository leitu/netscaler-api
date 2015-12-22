"""storage.py - Module for performing storage "actions" """
__author__ = "atu"
__version__ = "0.0.1"

from lib.nsnitro.nsresources import *
from lib import config


import base64
import re
import logging
import logging.config
import os
import json
import unittest


path = os.path.dirname(os.path.realpath(__file__))
loggingpath = path + '/logger_cfg.json'

with open(loggingpath, 'rt') as f:
    loggingconfig = json.load(f)

logging.config.dictConfig(loggingconfig)



class Load(object):
    def __init__(self, params):
        self.params = params
        self.loadbalance = self.params.get('loadbalance')
        apiconn = Connect(self.loadbalance)
        self.conn = apiconn.ns_connect()

    def execute_method(self, params, actions):
        '''
        Used to select which method to run from a dict
        @type action: str
        @param action: action to look up as a string
        @type actions: dict
        @param actions: a dictionary containing action as key and all possible methods[0] and their arguments[1][*]
        @rtype: bool
        @return: returns true or false from invoked method
        '''
        action = params.get('action').lower()
        if action in actions:
            if actions[action][1]:
                params['status'] = actions[action][0](*actions[action][1])
                params['reason'] = ""
                payload = json.dumps(params)
                return str(payload)
            else:
                params['status'] = actions[action][0]()
                params['reason'] = ""
                payload = json.dumps(params)
                return str(payload)
        else:
            logging.error("action: {} is not a known action type".format(action))
            errormsg = 'status="Failed" reason="Unknown action ({}) requested"'.format(action)
            raise ClusterException(errormsg, self.params)

    def run(self):
        '''
        Main point of entry for code
        @return: string
        '''
        # Perform lb operation
        if self.params.get('object').lower() == "lbvserver":
            provision = Provision(self.conn, self.params.get('arguments', {}).get('vip'), self.params.get('arguments', {}).get('clientid') )
            # actions = action: [method_name, [*args]]
            actions = {'create': [provision.create_all, [self.params.get('arguments',{}).get('appservers')]],
                       'disable': [provision.disable_lbvserver, None],
                       'delete': [provision.delete_lbvserver, None]
                       }
            return self.execute_method(self.params, actions)

        # TODO Create clone class (object) and actions

        # Perform server operation
        elif self.params.get('object').lower() == "appserver":
            provision = Provision(self.conn, self.params.get('arguments', {}).get('vip'), self.params.get('arguments', {}).get('clientid') )
            actions = {'create': [provision.create_server, [self.params.get('arguments',{}).get('appservers')]],
                       'disable': [provision.disable_server, None],
                       'delete': [provision.delete_server, None]
                       }
            return self.execute_method(self.params, actions)

        # Perform service operation
        elif self.params.get('object').lower() == "service":
            provision = Provision(self.conn, self.params.get('arguments', {}).get('vip'), self.params.get('arguments', {}).get('clientid') )
            actions = {'create': [provision.create_service, [self.params.get('arguments',{}).get('appservers')]],
                       'disable': [provision.disable_service, None],
                       'delete': [provision.delete_service, None]
                       }
            return self.execute_method(self.params, actions)


        else:
            logging.error("object: {} is not a known action type".format(object))
            errormsg = 'status="Failed" reason="Unknown object ({}) requested"'.format(object)
            raise LBException(errormsg, self.params)


class Connect(object):
    def __init__(self,loadbalance):
        self.loadbalance = loadbalance
        self.username = base64.b64decode(config.username)
        self.password = base64.b64decode(config.password)

    def ns_connect(self):
        nitro = NSNitro(self.loadbalance, self.username, self.password, useSSL=False)
        nitro.login()
        logging.info("Setup connection for vserver: {} user: {}".format(self.loadbalance, self.username))
        return nitro


class Provision(object):
    def __init__(self, apiconnection, clientid, vip):
        self.vip = vip
        self.clientid = clientid
        self.vipname = self.clientid + '_vip_' + self.vip
        self.conn = apiconnection


  #Get splash
    def get_splash(self):
        vnames = NSVServer.get_all(self.conn)
        vname_list = []
        for vname in vnames:
            vname_list.append(vname.get_name())
        #matching = [ s for s in vname_list if "splash" in s]
        matching = filter(lambda x: 'splash' in x, vname_list)
        return matching

  #create server
    def create_server(self, appservers):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            addserver = NSServer()
            addserver.set_name(server_name)
            addserver.set_ipaddress(appservers[i])
            NSServer.add(self.conn, addserver)

    #create service
    def create_service(self, appservers):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            addservice = NSService()
            if i == 0:
                addservice.set_name(server_name + ':8010')
                addservice.set_servername(server_name)
                addservice.set_servicetype("TCP")
                addservice.set_port(8010)
                addservice.set_maxclient('0')
                addservice.set_maxreq('0')
                addservice.set_cip('DISABLED')
                addservice.set_usip('NO')
                addservice.set_sp('OFF')
                addservice.set_clttimeout('9000')
                addservice.set_svrtimeout('9000')
                addservice.set_cka('YES')
                addservice.set_tcpb('NO')
                addservice.set_cmp('NO')
                addservice.set_appflowlog('DISABLED')
                NSService.add(self.conn, addservice)

                addservice.set_name(server_name + ':8011')
                addservice.set_servername(server_name)
                addservice.set_servicetype("HTTP")
                addservice.set_port(8011)
                addservice.set_maxclient('0')
                addservice.set_maxreq('0')
                addservice.set_cip('DISABLED')
                addservice.set_usip('NO')
                addservice.set_sp('OFF')
                addservice.set_clttimeout('180')
                addservice.set_svrtimeout('360')
                addservice.set_cka('YES')
                addservice.set_tcpb('NO')
                addservice.set_cmp('NO')
                addservice.set_appflowlog('DISABLED')
                NSService.add(self.conn, addservice)
            addservice.set_name(server_name + ':8080')
            addservice.set_servername(server_name)
            addservice.set_servicetype("HTTP")
            addservice.set_maxclient('0')
            addservice.set_maxreq('0')
            addservice.set_cip('ENABLED')
            addservice.set_cipheader("X-Forwarded-For")
            addservice.set_usip('NO')
            addservice.set_sp('OFF')
            addservice.set_clttimeout('180')
            addservice.set_svrtimeout('360')
            addservice.set_cka('YES')
            addservice.set_tcpb('NO')
            addservice.set_cmp('NO')
            addservice.set_appflowlog('DISABLED')
            addservice.set_port(8080)
            NSService.add(self.conn, addservice)

    #create  LB vserver
    def create_lbvserver(self, matching):
        ports = [ '8010', '8011', '443', '80']
        for i, v in enumerate(ports):
            lbvserver = NSLBVServer()
            lbvserver.set_ipv46(self.vip)
            lbvserver.set_clttimeout('180')
            lbvserver.set_persistencetype("NONE")
            lbvserver.set_appflowlog('DISABLED')
            if v == '8010':
                lbvserver.set_name(self.vipname + ":8010")
                lbvserver.set_port(8010)
                lbvserver.set_servicetype("TCP")
                lbvserver.set_clttimeout("9000")
            elif v == '8011':
                lbvserver.set_name(self.vipname + ":8011")
                lbvserver.set_port(8011)
                lbvserver.set_servicetype("HTTP")
            elif v == '443':
                lbvserver.set_name(self.vipname + ":443")
                lbvserver.set_port(443)
                lbvserver.set_persistencetype("COOKIEINSERT")
                lbvserver.set_servicetype("SSL")
                lbvserver.set_backupvserver(matching[1])
            elif v == '80':
                lbvserver.set_name(self.vipname)
                lbvserver.set_port(80)
                lbvserver.set_servicetype("HTTP")
                lbvserver.set_backupvserver(matching[0])
            NSLBVServer.add(self.conn, lbvserver)


   #bind lbvserver
    def bind_lbvserver(self, appservers):
        ports = [ '8010', '8011', '443', '80']
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            lbbinding = NSLBVServerServiceBinding()
            lbbinding.set_name(self.vipname)
            lbbinding.set_servicename(server_name + ':8080')
            NSLBVServerServiceBinding.add(self.conn, lbbinding)
            lbbinding.set_name(self.vipname + ":443")
            lbbinding.set_servicename(server_name + ':8080')
            NSLBVServerServiceBinding.add(self.conn, lbbinding)
            if i == 0:
                lbbinding.set_name(self.vipname + ':8010')
                lbbinding.set_servicename(server_name + ':8010')
                NSLBVServerServiceBinding.add(self.conn, lbbinding)
                lbbinding.set_name(self.vipname + ':8011')
                lbbinding.set_servicename(server_name + ':8011')
                NSLBVServerServiceBinding.add(self.conn, lbbinding)

    #bind po licy
    def bind_lbvserver_rewritepolicy(self):
        lbvserverrewritepolicybinding = NSLBVServerRewritePolicyBinding()
        lbvserverrewritepolicybinding.set_name(self.vipname)
        lbvserverrewritepolicybinding.set_policyname('HTTPS-REDIRECT')
        lbvserverrewritepolicybinding.set_priority('50')
        lbvserverrewritepolicybinding.set_gotopriorityexpression('END')
        NSLBVServerRewritePolicyBinding.add(self.conn, lbvserverrewritepolicybinding)
        lbvserverrewritepolicybinding = NSLBVServerRewritePolicyBinding()
        lbvserverrewritepolicybinding.set_name(self.vipname + ":443")
        lbvserverrewritepolicybinding.set_policyname('X-FORWARDED-PROTO')
        lbvserverrewritepolicybinding.set_priority('50')
        lbvserverrewritepolicybinding.set_gotopriorityexpression('END')
        lbvserverrewritepolicybinding.set_bindpoint('REQUEST')
        NSLBVServerRewritePolicyBinding.add(self.conn, lbvserverrewritepolicybinding)


   #bind lbmonit
    def bind_lbmonitor(self):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            lbmonitorbinding = NSLBMonitorServiceBinding()
            lbmonitorbinding.set_monitorname('offload_amiup.jsp')
            lbmonitorbinding.set_servicename(server_name + ":8080")
            NSLBMonitorServiceBinding.add(self.conn, lbmonitorbinding)

    #seti sslv3 disabled
    def disable_sslv3(self):
        lbvserverssl = NSSSLVServer()
        lbvserverssl.set_vservername(self.vipname + ":443")
        lbvserverssl.set_ssl3('DISABLED')
        NSSSLVServer.update(self.conn,lbvserverssl)

    #bind ceirtificate
    def bind_cert(self, certkey='wildcard.digi'):
        lbvservercertbinding = NSSSLVServerSSLCertKeyBinding()
        lbvservercertbinding.set_vservername(self.vipname + ":443")
        lbvservercertbinding.set_certkeyname(certkey)
        NSSSLVServerSSLCertKeyBinding.add(self.conn,lbvservercertbinding)

    def get_server(self, appservers):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            getserver = NSServer()
            getserver.set_name(server_name)
            getserver = getserver.get(self.conn, getserver)
            logger.info("Server {} has status {}".format(getserver.get_name(), getserver.get_state()))


    def get_service(self, appservers):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            getservice = NSService()
            if i == 0:
                getservice.set_name(server_name + ':8010')
                NSService.get(self.conn, getservice)
                getservice.set_name(server_name + ':8011')
                NSService.add(self.conn, getservice)
            getservice.set_name(server_name + ':8080')
            NSService.get(self.conn, getservice)
            logger.info("Has service {}".format(getservice.get_name()))


    def get_lbvserver(self):
        ports = [ '8010', '8011', '443', '80']
        for i, v in enumerate(ports):
            getlbvserver = NSLBVServer()
            if v == '8010':
                getlbvserver.set_name(self.vipname + ":8010")
            elif v == '8011':
                getlbvserver.set_name(self.vipname + ":8011")
            elif v == '443':
                getlbvserver.set_name(self.vipname + ":443")
            elif v == '80':
                getlbvserver.set_name(self.vipname)
            getlbvserver = NSLBVServer.get(self.conn, getlbvserver)
            logger.info("Has LB service {}".format(getlbvserver.get_name()))

    def disable_server(self):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            disableserver = NSServer()
            disableserver.set_name(server_name)
            NSServer.disable(self.conn, disableserver)
            logger.info("Server disabled")

    def disable_service(self, appservers):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            disableservice = NSService()
            if i == 0:
                disableservice.set_name(server_name + ':8010')
                NSService.disable(self.conn, disableservice)
                disableservice.set_name(server_name + ':8011')
                NSService.disable(self.conn, disableservice)
            disableservice.set_name(server_name + ':8080')
            NSService.disable(self.conn, disableservice) 


    def disable_lbvserver(self):
        ports = [ '8010', '8011', '443', '80']
        for i, v in enumerate(ports):
            disablelbvserver = NSLBVServer()
            if v == '8010':
                disablelbvserver.set_name(self.vipname + ":8010")
            elif v == '8011':
                disablelbvserver.set_name(self.vipname + ":8011")
            elif v == '443':
                disablelbvserver.set_name(self.vipname + ":443")
            elif v == '80':
                disablelbvserver.set_name(self.vipname)
            NSLBVServer.disable(self.conn, disablelbvserver)
            logger.warning("Server disabled")

    def delete_server(self):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            deleteserver = NSServer()
            deleteserver.set_name(server_name)
            NSServer.delete(self.conn, deleteserver)
            logger.warning("Server deleted")

    def delete_service(self, appservers):
        for i in range(len(appservers)):
            server_name = self.clientid + '_app' + str(i+1) + '_' + appservers[i]
            deleteservice = NSService()
            if i == 0:
                deleteservice.set_name(server_name + ':8010')
                NSService.delete(self.conn, deleteservice)
                deleteservice.set_name(server_name + ':8011')
                NSService.delete(self.conn, deleteservice)
            deleteservice.set_name(server_name + ':8080')
            NSService.delete(self.conn, deleteservice)
            logger.warning("Service deleted")

    def delete_lbvserver(self):
        ports = [ '8010', '8011', '443', '80']
        for i, v in enumerate(ports):
            deletelbvserver = NSLBVServer()
            if v == '8010':
                deletelbvserver.set_name(self.vipname + ":8010")
            elif v == '8011':
                deletelbvserver.set_name(self.vipname + ":8011")
            elif v == '443':
                deletelbvserver.set_name(self.vipname + ":443")
            elif v == '80':
                deletelbvserver.set_name(self.vipname)
            NSLBVServer.delete(self.conn, deletelbvserver)
            logger.warning("Server deleted")


    def create_all(self, appservers):
        logging.info("Start provision")
        matching = self.get_splash()
        self.create_server(self.clientid, appservers)
        self.create_service(self.clientid, appservers)
        self.create_lbvserver(self.clientid, matching)
        self.bind_lbvserver(appservers)
        self.bind_lbvserver_rewritepolicy()
        self.bind_lbmonitor()
        self.disable_sslv3()
        self.bind_cert()
        logging.info("Provision is done")


class LBException(Exception):
    def __init__(self, msg, params):
        self.msg = msg
        self.params = params

    def __str__(self):
        payload = self.params
        status = re.search('status=\"(\w*)\"', self.msg)
        reason = re.search('reason=\"(.*)\"', self.msg)
        payload['status'] = status.group(1)
        payload['reason'] = reason.group(1)
        logging.error("Provision {} - {}".format(payload.get('status'), payload.get('reason')))
        payload = json.dumps(payload)
        return str(payload)
