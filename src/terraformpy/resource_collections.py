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

import six
from schematics.exceptions import MockCreationError
from schematics.models import Model

from terraformpy.helpers import relative_file as _relative_file


class ResourceCollection(Model):
    """ResourceCollection is a specialized subclass of the schematics Model object that aims to keep the feel of the
    TFObject while providing full compatibility as a schematics Model.

    Unlike a model where you provide the data as a dict, you provide data as keyword args just like TFObject.

    By default the Variant object is used to lookup variant properites, but you can also provide a variant_name argument
    that will be used instead.

    Variant data is defined inside of a `foo_variant` block.

    .. code-block:: python

        MyResourceColection(
            count=2
            prod_variant=dict(
                count=4
            )
        )

    If the above block was defined within a `Variant('prod')` context then count would be 4, otherwise it would be 2.
    """

    def __init__(self, *args, **kwargs):
        variant_name = kwargs.pop('variant_name', None)

        # if we have positional arguments AND a context then we just want to do the schematics model thing and have
        # super up to the model to let things happen.  this is most likely happening because one resource collection
        # is being used as a reference in a modeltype
        if len(args) > 0 and kwargs.get('context') is not None:
            super(ResourceCollection, self).__init__(*args, **kwargs)
            return

        # there are still some places in underlying schematics stuff that
        # invoke model constructors in the traditional way, but without
        # context. get_mock_object() is one of these cases
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], dict):
            kwargs = args[0]
            args = tuple()

        if variant_name is None and Variant.CURRENT_VARIANT is not None:
            variant_name = Variant.CURRENT_VARIANT.name

            # update our raw data with the variant defaults
            kwargs.update(Variant.CURRENT_VARIANT.defaults)

        if variant_name is not None:
            # if there is then try fetching the val from inside the special variant attr
            variant_key = '{0}_variant'.format(Variant.CURRENT_VARIANT.name)
            variant_data = kwargs.get(variant_key, None)
            if variant_data is not None:
                kwargs.update(variant_data)

        # filter all of the variant data out
        kwargs = dict(
            (k, v)
            for k, v in six.iteritems(kwargs)
            if not k.endswith('_variant')
        )

        super(ResourceCollection, self).__init__(kwargs)

        self.validate()
        self.create_resources()

    def relative_file(self, filename):
        return _relative_file(filename, _caller_depth=2)

    def create_resources(self):
        raise NotImplementedError

    def finalize_resources(self):
        """This is called right before we compile everything.  It gives the collection a chance to generate any final
        resources prior to the compilation occuring.
        """
        pass


class Variant(object):
    """When used as a context manager it provides the ability for ResourceCollection's to vary their inputs based on a
    symbolc string name that allows you to define a resource collection for multiple environments where most of the
    inputs are shared, with only a few differences.

    Any kwargs passed to the constructor become defaults for non-variant inputs.  This allows you to supply inputs that
    are shared between many different ResourceCollections at the variant level so you don't need to pass them over and
    over again.
    """
    CURRENT_VARIANT = None

    def __init__(self, name, **kwargs):
        self.name = name
        self.defaults = kwargs
        self.previous_variant = None

    def __enter__(self):
        self.previous_variant = Variant.CURRENT_VARIANT
        Variant.CURRENT_VARIANT = self

    def __exit__(self, exc_type, exc_value, traceback):
        Variant.CURRENT_VARIANT = self.previous_variant
