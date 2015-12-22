import redis


class RedisManager(object):


    def __init__(self, r_server_addr="", r_username="", r_password=""):
        # TODO: Add username and password auth options
        self.r_server = redis.Redis(r_server_addr)

    def set_payload_hash(self, payload_data):
        payload_id = self.get_payload_id(payload_data)
        self.r_server.hmset(payload_id, payload_data)

    def get_payload_id(self, payload_data):
        return payload_data['task_id']

    def get_entire_payload(self, payload_id):
        return self.r_server.hgetall(payload_id)

    def get_payload_element(self, payload_id, hash_key):
        return self.r_server.hmget(payload_id, hash_key)
