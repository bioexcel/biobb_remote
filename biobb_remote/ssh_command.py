#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
from ssh_session import SshSession

if __name__ == "__main__":
    session = SshSession(credentials_path=sys.argv[1])
    (stdin, stdout, stderr) = session.run_command(sys.argv[2])
    print(''.join(stdout))
    print(''.join(stderr), file=sys.stderr)
