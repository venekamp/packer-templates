#!/usr/bin/env python

import argparse
import json
import os.path
import re
import subprocess
import shutil
import sys
from collections import OrderedDict


############################################################
def print_verbose(*args):
    if verbose:
        for arg in args:
            sys.stdout.write(arg)

        sys.stdout.write('\n')
        sys.stdout.flush()

############################################################
def destroy_VM_if_running(vm_name):
    vm_running = re.compile(vm_name)
    running_vms = subprocess.check_output(['VBoxManage', 'list', 'vms'])

    if vm_running.search(running_vms):
        print 'The', vm_name, 'is running. Bringing it down first. ',

        p = subprocess.Popen(['vagrant', 'destroy', '-f'])
        p.wait()

        print '[done]'

############################################################
def add_box_to_repository(vm_name, config_filename):
    print 'Adding ' + vm_name + ' to the repository',

    p = subprocess.Popen(['vagrant', 'box', 'add',
        '--name', vm_name,
        config_filename])

    p.wait()

    print '[done]'

############################################################
class ChecksumError(Exception):
    def __init__(self, output):
        self.output = output
    def __str__(self):
        return repr(self.output)

def calculate_checksum(box_filename):
    find_checksum = re.compile('.*= ([0-9a-z]*)')

    try:
        output = subprocess.check_output(["openssl", "sha1", box_filename])
    except OSError as e:
        raise ChecksumError('openssl executable not found.')

    remove_newline = re.compile('(.*)\n')
    result = remove_newline.search(output)
    if result:
        output = result.group(1)

    try:
        checksum = find_checksum.search(output).group(1)
    except  AttributeError:
        raise ChecksumError(output)

    return checksum


############################################################
def retrieve_json_config(config_filename):
    config = """
    {
        "name": "centos7",
        "description": "Base box with CentOS 7 and VBox Guest Additions",
        "versions": []
    }"""

    if os.path.isfile(config_filename):
        print_verbose('Using existing config file')
        with open(config_filename, 'r') as config_file:
            json_config = json.load(config_file, object_pairs_hook=OrderedDict)
    else:
        print_verbose('Generating new config file')
        json_config = json.loads(config, object_pairs_hook=OrderedDict)

    return json_config


############################################################
def add_box_to_config(json_config, box_url, box_version, box_checksum):
    box_version_template = """
    {
        "version": "---VERSION---",
        "providers": [{
            "name": "virtualbox",
            "url": "URL",
            "checksum_type": "sha1",
            "checksum": "CHECKSUM"
        }]
    }
    """

    box_versions = json_config['versions']

    new_box = json.loads(box_version_template)
    new_box['version'] = box_version
    new_box['providers'][0]['url'] = box_url
    new_box['providers'][0]['checksum'] = box_checksum

    box_versions.append(new_box)

    json_config['versions'] = box_versions

    return json_config


############################################################
def write_json_config(config_filename, json_config):
    new_config = json.dumps(json_config, sort_keys=False, indent=4)

    # Remove trailing while space. Yucky!
    remove_white_space = re.compile('\s*$', re.MULTILINE)
    new_config = remove_white_space.sub('', new_config)

    with open(config_filename, "w") as config_file:
        config_file.write(new_config)


############################################################
def update_config(config_filename, box_name, box_version):
    try:
        box_checksum = calculate_checksum(box_name)
        print_verbose('Checksum:             \033[35m', box_checksum, '\033[39m')

        box_url = 'file://' + os.getcwd() + '/' + box_name
        print_verbose('box_url:              \033[32m', box_url, '\033[39m')

        json_config = retrieve_json_config(config_filename)
        json_config = add_box_to_config(json_config, box_url, box_version, box_checksum)
        print_verbose('Resulting config file')
        print_verbose(json.dumps(json_config, sort_keys=False, indent=4))
        write_json_config(config_filename, json_config)
    except ChecksumError as e:
        print 'Error:  Checksum could not be determined.'
        print 'reason: ' + e.output



parser = argparse.ArgumentParser(
        description = 'Adding a Vagrant box to a local repository.')

parser.add_argument(
        'config_path',
        help = 'path where the config file is')

parser.add_argument(
        'version',
        help = 'version number of the new box')

parser.add_argument(
        '--box-path',
        default = 'boxes/',
        required = False,
        help = 'Path where boxes are stored (default: boxes)')

parser.add_argument(
        '--box-name',
        required = False,
        help = 'name of the new box')

parser.add_argument(
        '--verbose',
        default = False,
        required = False,
        action = 'store_true',
        help = 'set verbose output')

args = parser.parse_args()

if args.box_name:
    vm_name = args.box_name
else:
    #  Assume the name of the VM will be the same as the current directory
    cwd = os.getcwd()
    vm_name = os.path.basename(cwd)

version = args.version
config_path = args.config_path

if not config_path.endswith('/'):
    config_path = config_path + '/'

box_path = args.box_path;
if not box_path.endswith('/'):
    box_path = box_path + '/'

verbose = args.verbose

print_verbose('Virtual Machine name: \033[32m', vm_name, '\033[39m')
print_verbose('Version:              \033[32m', version, '\033[39m')
print_verbose('config_path:          \033[32m', config_path, '\033[39m')
print_verbose('box_path:             \033[32m', box_path, '\033[39m')

src_box = 'artifacts/vagrant/' + vm_name + '.box'
dest_box = box_path + vm_name + '-' + version + '.box'

config_filename = config_path + vm_name + '.json'

try:
    destroy_VM_if_running(vm_name)
    shutil.move(src_box, dest_box)
    update_config(config_filename, dest_box, version)
    add_box_to_repository(vm_name, config_filename)
except Exception as ex:
    template = "An exception of type {0} occured. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print message
