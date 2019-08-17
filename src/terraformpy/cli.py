"""
Copyright 2019 NerdWallet

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import imp
import json
import os
import sys

from terraformpy import compile


def main():
    """Compile *.tf.py files and run Terraform"""
    to_process = [
        ent
        for ent in os.listdir(os.getcwd())
        if ent.endswith('.tf.py')
    ]

    if len(to_process) == 0:
        print("terraformpy - Error loading config: No .tf.py files found in %s" % os.getcwd())
        sys.exit(1)

    print("terraformpy - Processing: %s" % ', '.join(to_process))

    # all we need to do is import our files
    # the nature of resource declaration will register all of the objects for us to compile
    for filename in to_process:
        imp.load_source(filename[:-6], filename)

    # now 'compile' everything that was registered, and write it out the tf.json file
    print("terraformpy - Writing main.tf.json")
    with open('main.tf.json', 'w') as fd:
        json.dump(compile(), fd, indent=4, sort_keys=True)

    if len(sys.argv) > 1:
        print("terraformpy - Running terraform: %s" % ' '.join(sys.argv[1:]))
        # replace ourself with terraform
        os.execvp("terraform", ["terraform"] + sys.argv[1:])
