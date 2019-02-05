from concurrent import futures
import time
import functools
import queue
import yaml
import grpc
from datetime import datetime
from collections import deque
from messenger_pb2 import text
import messenger_pb2
import messenger_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


queue_sender = {}
queue_lastcheck = {}
queue_restrict= {}
queue_group1= deque()
queue_group2= deque()

def lru(func):
    def wrapper_method(*args, **kwargs):
        func(*args, **kwargs)
        queue=args[1]
        message=args[0]
        if len(queue)<=4:
            queue.append(message)
        else:
            queue.popleft()
            queue.append(message)
    return wrapper_method
    
def rate(func):
    def wrapper_method(*args, **kwargs):
        message=args[0]
        current = datetime.now()
        limit=queue_restrict[message.sender].get()
        ETA = (current -  queue_lastcheck[message.sender].get()).total_seconds()
        queue_lastcheck[message.sender].put(current)
        limit = limit + ETA * (no_of_msgs / secs)
        if limit > no_of_msgs:
            limit = no_of_msgs
        if limit > 1.0:
            func(*args, **kwargs)
        queue_restrict[message.sender].put(limit-1.0)
    return wrapper_method


@rate
@lru
def msg_put(message,queue):
    for u in queue_sender:
        if (u!=message.sender):
            queue_sender[u].put(message)   
        
class Msgr(messenger_pb2_grpc.messengerServicer):
    
    def lru(self, message, context):
       while True:
            if message.sender in group1:
                if queue_group1:
                    for i in queue_group1:
                        message=i
                        if message:
                            yield message
                    break
                
                else:
                    return
            else:
                if queue_group2:
                    for i in queue_group2:
                        message=i
                        if message:
                            yield message
                    break
                
                else:
                    return
            
    
    def login(self, message, context):
        verify=messenger_pb2.text()
        if message.sender in users:
            verify.msg='yes'
        else:
            verify.msg='no'
            
        return verify

    def chatter(self, message, context):
        sender = message.sender      
        queue_sender[sender] = queue.Queue()
        queue_lastcheck[sender]=queue.Queue()
        queue_restrict[sender]=queue.Queue()
        queue_lastcheck[sender].put(datetime.now())
        queue_restrict[sender].put(no_of_msgs)
        while True:
            message = queue_sender[sender].get()
            if message:
                yield message
    
    def read(self, message, context):
        if message.sender in group1:
            msg_put(message,queue_group1)              
        else:
            msg_put(message,queue_group2)
        return text()


def serve():
    print('Spartan server started on port 3000')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messenger_pb2_grpc.add_messengerServicer_to_server(Msgr(), server)
    server.add_insecure_port('[::]:3000')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    no_of_msgs=3.0
    secs=30.0
    config=yaml.load(open('config.yaml'))
    groups=config.get('groups')
    group1=groups.get('group1')
    group2=groups.get('group2')
    users=config.get('users')
    serve()
