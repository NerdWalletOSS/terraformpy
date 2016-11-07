import imp
import json
import logging
import os
import sys

import click

from terraformpy import compile
logging.basicConfig()

log = logging.getLogger(__name__)


@click.command()
@click.option('-D', '--debug', is_flag=True)
def main(debug=False):
    to_process = [
        ent
        for ent in os.listdir(os.getcwd())
        if ent.endswith('.tf.py')
    ]
    if len(to_process) == 0:
        log.error("Error loading config: No Terraformpy (.tf.py) files found in %s", os.getcwd())
        sys.exit(1)

    log.debug("terraformpy - processing: %s", to_process)

    # all we need to do is import our files
    # the nature of resource declaration will register all of the objects for us to compile
    for filename in to_process:
        tfpy = imp.load_source(filename[:-6], filename)

        # run the .main() function on the module, ignore it if the module hasn't defined one
        try:
            tfpy.main()
        except AttributeError:
            pass

    print json.dumps(compile(), indent=4, sort_keys=True)
