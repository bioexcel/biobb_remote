#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import pickle
from io import StringIO
from paramiko.rsakey import RSAKey


class sshCredentials():
    """ Generation of ssl credentials for remote execution """
    def __init__(self, host='', userid=''):
        self.host = host
        self.userid = userid
        self.key = None

    def load_from_file(self, credentials_path):
        try:
            file = open(credentials_path, 'rb')
            data = pickle.load(file)
        except IOError as err:
            print(err, file=sys.stderr)
            sys.exit()
        self.host = data['host']
        self.userid = data['userid']
        self.key = RSAKey.from_private_key(StringIO(data['key'].getvalue()))

    def set_login(self, host, userid):
        self.host = host
        self.userid = userid

    def generate_key(self, nbits=2048):
        self.key = RSAKey.generate(nbits)

    def save(self, output_path='', public_key_path=None):
        if output_path != '':
            with open(output_path, 'wb') as keys_file:
                private = StringIO()
                self.key.write_private_key(private)
                pickle.dump(
                    {
                        'userid': self.userid,
                        'host': self.host,
                        'data': private
                    }, keys_file)
            if public_key_path is not None:
                with open(public_key_path, "w") as pubkey_file:
                    pubkey_file.write(self.get_public_str())
            else:
                print(self.get_public_str())

    def get_public_str(self, suffix='@biobb'):
        return '{} {} {}{}\n'.format(
            self.key.get_name(), self.key.get_base64(), self.userid, suffix
        )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: credentials host_name user_id credentials_file [public_key_file]")
        sys.exit()
    pkey_file_path = None
    if len(sys.argv) == 5:
        pkey_file_path = sys.argv[4]

    credentials = sshCredentials(sys.argv[1], sys.argv[2])
    credentials.generate_key()
    credentials.save(sys.argv[3], pkey_file_path)
