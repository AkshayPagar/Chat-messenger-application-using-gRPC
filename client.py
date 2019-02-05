# noinspection PyUnresolvedReferences
import pkg_resources  # pyinstaller packaging require
from concurrent import futures
import threading
import grpc
import sys
import yaml
import hashlib
import base64
import messenger_pb2
import messenger_pb2_grpc
from Crypto.Cipher import AES
from Crypto import Random



def clientread(iter_m):
        for message in iter_m:
                aes = AES.new(key, AES.MODE_CFB, IV[0])
                final=aes.decrypt(base64.b64decode(message.msg))	
                print('[%s]: %s' % (message.sender, final.decode()))

def run():
    with grpc.insecure_channel('localhost:3000') as channel:
        stub = messenger_pb2_grpc.messengerStub(channel)
        print("Connected to Spartan Server at port 3000.")
        
        sender=sys.argv[1]

        verify=stub.login(messenger_pb2.text(sender=sender))
        if verify.msg != 'yes':
                print('User not registered')
                return
        
        print("You are now chatting with:")
        if sender in group1:
                print(group1)
        else:
                print(group2)
        
        Retrieve=input("Do you want to retrieve previous messages(yes or no): ")
        if Retrieve == 'yes':
                messages = stub.lru(messenger_pb2.text(sender=sender))
                clientread(messages)

        iter_m = stub.chatter(messenger_pb2.text(sender=sender))
        
        
        t = threading.Thread(target=clientread, args=(iter_m,))
        t.start()
        while True:
                cipher = AES.new(key, AES.MODE_CFB, IV[0])
                message=messenger_pb2.text(sender=sender, msg=base64.b64encode(cipher.encrypt(input())))
                stub.read(message)
  
        t.join()
        

if __name__ == '__main__':
        config=yaml.load(open('keys.yaml'))
        key=config.get('key')
        IV=config.get('iv')
        group1=config.get('group1')
        group2=config.get('group2')
        key = hashlib.sha256(key[0].encode()).digest()
        run()
