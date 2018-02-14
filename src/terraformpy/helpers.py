import inspect
import os


def relative_file(filename, _caller_depth=1):
    """Given a filename that is relative to the caller of this function this will return a string to be used in
    resource definitions where you need to load a file.

    Given that Terraform's path.module will always point to the main.tf.json path and we need to retrieve files from
    other directories (i.e. from modules) this provides a convenient way to write a file reference without needing
    to do all of the relative pathing and ../../../..

    .. code-block:: python

        class MyThing(ResourceCollection):
            def create_resources(self):
                self.thing = Resource(
                    'some_resource', 'my_thing',
                    template=self.relative_file('files/foo.json')
                )

    And the resulting JSON in main.tf.json will look like:

    .. code-block:: json

        "template": "${file(\"${path.module}/../../../modules/mything/files/foo.json\")}",

    """
    return '${{file("{0}")}}'.format(relative_path(filename, _caller_depth=_caller_depth+1))


def relative_path(path, _caller_depth=1):
    caller = inspect.stack()[_caller_depth]
    return '${{path.module}}/{0}'.format(
        os.path.relpath(os.path.join(os.path.dirname(caller[1]), path))
    )
