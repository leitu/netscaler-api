import netscaler

arguments = {
    "task_id": "3b7727d6-3833-4dcc-8fe5-d85f12d1eadb",
    "creation_time": "YYYY/MM/DD-HH:MM:SS",
    "user": "foo",
    "loadbalance": "lb1-1-tr1.mhint",
    "action": "Create",
    "object": "lbvserver",
    "arguments": {
        "vip": "192.168.2.1",
        "clientid": "123456",
        "appservers": ["10.10.3.1","10.10.3.3"]
    }
}


provision = netscaler.Load(arguments)
try:
    result = provision.run()
except Exception as e:
    print str(e)