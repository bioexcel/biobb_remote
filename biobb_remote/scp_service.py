#! /usr/bin/python3

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "gelpi"
__date__ = "$08-March-2019  17:32:38$"

import sys
#import paramiko
from ssh_session import SshSession

session = SshSession(credentials_path=sys.argv[1])
session.run_sftp(sys.argv[2], sys.argv[3], sys.argv[4])
