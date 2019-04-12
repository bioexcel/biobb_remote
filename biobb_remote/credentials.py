#! /usr/bin/python3
""" Module to handle ssh credentials (userid, host, private_keys) """

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
from ssh_session import sshCredentials

if len(sys.argv) < 2:
    print("Usage: credentials host_name user_id credentials_file [public_key_file]")
    sys.exit()
pkey_file_path = None
if len(sys.argv) == 5:
    pkey_file_path = sys.argv[4]

credentials = sshCredentials(sys.argv[1], sys.argv[2])
credentials.generate_key()
credentials.save(sys.argv[3], pkey_file_path)
if not pkey_file_path:
    print(credentials.get_public_str())
