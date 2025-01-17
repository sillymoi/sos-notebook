#!/usr/bin/env python
#
# Copyright (c) Bo Peng and the University of Texas MD Anderson Cancer Center
# Distributed under the terms of the 3-clause BSD License.

import argparse
import json
import os
import shutil
import sys

from IPython.utils.tempdir import TemporaryDirectory
from jupyter_client.kernelspec import KernelSpecManager
from jupyter_contrib_core.notebook_compat import nbextensions
from traitlets.config.manager import BaseJSONConfigManager

_py_ver = sys.version_info
if _py_ver.major == 2 or (_py_ver.major == 3 and
                          (_py_ver.minor, _py_ver.micro) < (6, 0)):
    raise SystemError(
        'sos requires Python 3.6 or higher. Please upgrade your Python {}.{}.{}.'
        .format(_py_ver.major, _py_ver.minor, _py_ver.micro))

kernel_json = {
    "argv": [
        sys.executable, "-m", "sos_notebook.kernel", "-f", "{connection_file}"
    ],
    "display_name": "SoS",
    "language": "sos",
}


def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False  # assume not an admin on non-Unix platforms


def get_install_sos_kernel_spec_parser():
    parser = argparse.ArgumentParser(
        description='Install KernelSpec for sos Kernel')
    prefix_locations = parser.add_mutually_exclusive_group()
    prefix_locations.add_argument(
        '--user',
        help='Install KernelSpec in user homedirectory',
        action='store_true')
    prefix_locations.add_argument(
        '--sys-prefix',
        help='Install KernelSpec in sys.prefix. Useful in conda / virtualenv',
        action='store_true',
        dest='sys_prefix')
    prefix_locations.add_argument(
        '--prefix', help='Install KernelSpec in this prefix', default=None)
    return parser


def install_sos_kernel_spec(user, prefix):

    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable
        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, sort_keys=True)
        # Copy resources once they're specified
        shutil.copy(
            os.path.join(os.path.split(__file__)[0], 'kernel.js'),
            os.path.join(td, 'kernel.js'))
        shutil.copy(
            os.path.join(os.path.split(__file__)[0], 'logo-64x64.png'),
            os.path.join(td, 'logo-64x64.png'))

        KS = KernelSpecManager()
        KS.install_kernel_spec(td, 'sos', user=user, prefix=prefix)
        destination = KS._get_destination_dir('sos', user=user, prefix=prefix)
        print(f'sos jupyter kernel spec is installed to {destination}')


def install_config(user, prefix):
    config_dir = nbextensions._get_config_dir(user=user, sys_prefix=prefix)

    # Set extra template path
    cm = BaseJSONConfigManager(config_dir=os.path.join(config_dir, 'nbconfig'))
    keyname = 'sos_notebook_console_panel'
    config = cm.get('notebook')
    if keyname not in config:
        config[keyname] = 'auto'
        # avoid warnings about unset version
        cm.set('notebook', config)
    print(f'Settings added or updated in {config_dir}/nbconfig/notebook.json')


if __name__ == '__main__':
    parser = get_install_sos_kernel_spec_parser()
    args = parser.parse_args()
    user = False
    prefix = None
    if args.sys_prefix:
        prefix = sys.prefix
    elif args.prefix:
        prefix = args.prefix
    elif args.user or not _is_root():
        user = True

    install_sos_kernel_spec(user, prefix)
    install_config(user, prefix)
