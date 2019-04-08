#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import pickle
from Crypto.PublicKey import RSA


class sshCredentials():
    """ Generation of ssl credentials for remote execution """
    def __init__(self, host, userid):
        self.host=host
        self.userid=userid
      
    def generate(self, output_path='',public_key_path=''):
        key = RSA.generate(2048)
        self.private = key.exportKey('PEM')
        self.public = key.publickey().exportKey('OpenSSH')
        
        if output_path != '':
            with open(output_path, 'wb') as keys_file:
                pickle.dump(self, keys_file)
            with open(public_key_path, "w") as pubkey_file:
                pubkey_file.write(self.public.decode('utf-8'))
        return self
    
if __name__ == "__main__":
    host = sys.argv[1]
    userid = sys.argv[2]
    output_path = sys.argv[3]
    public_key_path = sys.argv[4]
    credentials = sshCredentials(host,userid).generate(output_path, public_key_path)
    
    
