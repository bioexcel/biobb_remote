#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import pickle
from paramiko.rsakey import RSAKey
from io import StringIO


class sshCredentials():
    """ Generation of ssl credentials for remote execution """
    def __init__(self, host, userid, nbits=2048):
        self.host=host
        self.userid=userid
        self.key = RSAKey.generate(nbits)
          
    def save(self, output_path='', public_key_path=''):        
        if output_path != '':
            with open(output_path, 'wb') as keys_file:
                private = StringIO()
                self.key.write_private_key(private)
                pickle.dump(
                    {
                        'userid': self.userid,
                        'host': self.host,
                        'key': private
                    }, keys_file)
            with open(public_key_path, "w") as pubkey_file:
                pubkey_file.write(self.get_public_str())
                
    def get_public_str(self, suffix='@biobb'):
        return '{} {} {}{}\n'.format(self.key.get_name(), self.key.get_base64(), self.userid, suffix)
    
if __name__ == "__main__":
    host = sys.argv[1]
    userid = sys.argv[2]
    output_path = sys.argv[3]
    public_key_path = sys.argv[4]
    credentials = sshCredentials(host,userid).save(output_path, public_key_path)
    
    
