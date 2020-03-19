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

Terraform "objects"

This module provides a set of classes that can be used to build Terraform configurations in a (mostly) declarative way,
while also leveraging Python to add some functional aspects to automate some of the more repetitive aspects of HCL.
"""
import collections

import six
from schematics.types import compound

from .resource_collections import Variant


def recursive_update(dest, source):
    """Like dict.update, but recursive"""
    for key, val in six.iteritems(source):
        if isinstance(val, collections.Mapping):
            recurse = recursive_update(dest.get(key, {}), val)
            dest[key] = recurse
        else:
            dest[key] = val
    return dest


class DuplicateKey(str):
    """DuplicateKey provides a native string (str) replacement that can be used as a
    dictionary key that will serialize out to JSON and maintain the duplicity.

    This is needed because the JSON representation of HCL requires duplicate keys for
    provider resources, which is technically not against the JSON spec[1].

    Insertion order is preserved by using a counter value as the hash value per unique
    key that is generated using this class.

    [1]: https://stackoverflow.com/a/21833017/11439015
    """

    _next_hash = collections.defaultdict(lambda: 0)

    def __new__(cls, key):
        inst = super(DuplicateKey, cls).__new__(cls, key)

        inst._hash = hash((key, DuplicateKey._next_hash[key]))
        DuplicateKey._next_hash[key] += 1

        return inst

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._hash == other._hash

    def __lt__(self, other):
        if self.__class__ == other.__class__:
            return self._hash < other._hash
        return super(DuplicateKey, self).__lt__(other)

    def __le__(self, other):
        if self.__class__ == other.__class__:
            return self._hash <= other._hash
        return super(DuplicateKey, self).__le__(other)

    def __gt__(self, other):
        if self.__class__ == other.__class__:
            return self._hash > other._hash
        return super(DuplicateKey, self).__gt__(other)

    def __ge__(self, other):
        if self.__class__ == other.__class__:
            return self._hash >= other._hash
        return super(DuplicateKey, self).__ge__(other)


class OrderedDict(compound.DictType):
    """
    A schematic DictType that preserves key insertion order
    """

    def __init__(self, *args, **kwargs):
        super(OrderedDict, self).__init__(*args, **kwargs)
        self.native_type = collections.OrderedDict

    def convert(self, value, context=None):
        # okay, this is a little wasteful for the purpose of not having to
        # copy-paste the implementation that might currently exist
        # in compound.DictType
        # so sure, we iterate over the type a couple of times, but this way
        # we get their validators and updates to their validators
        temp_data = super(OrderedDict, self).convert(value, context)

        # so now, temp_data is a dict filled with the correct (and coerced)
        # values, we just want it to be ordered now based on how `value`
        # was passed in
        # let's trust the validators in `convert()` and not check key existance
        data = collections.OrderedDict()
        for k in value.keys():
            data[k] = temp_data[k]

        return data


class TFObject(object):
    _instances = None
    _frozen = False
    _hooks = None

    def __new__(cls, *args, **kwargs):
        # create the instance
        inst = super(TFObject, cls).__new__(cls)

        # register it on the class
        try:
            cls._instances.append(inst)
        except AttributeError:
            cls._instances = [inst]

        # return it
        return inst

    @classmethod
    def add_hook(cls, object_type, hook):
        """Add a hook for the given object type

        The hook will receive the full built object and is expected to return the updated object to be used when
        recursively adding to the final output.

        Generally you will want to use the add_hook method on the final object type (i.e. Resource.add_hook) instead
        of this method, as the other add_hook methods provide sugar for typed and named objects.

        See NamedObject.add_hook and TypedObject.add_hook
        """
        try:
            TFObject._hooks[object_type].append(hook)
        except TypeError:
            TFObject._hooks = {object_type: [hook]}
        except KeyError:
            TFObject._hooks[object_type] = [hook]

    @classmethod
    def reset(cls):
        def recursive_reset(cls):
            cls._instances = None
            for klass in cls.__subclasses__():
                recursive_reset(klass)

        recursive_reset(cls)
        TFObject._frozen = False
        TFObject._hooks = None

    @classmethod
    def compile(cls):
        TFObject._frozen = True

        def recursive_compile(cls):
            results = []
            try:
                for instance in cls._instances:
                    output = instance.build()

                    for object_type in output:
                        try:
                            hooks = TFObject._hooks[object_type]
                        except (TypeError, KeyError):
                            pass
                        else:
                            for hook in hooks:
                                output = hook(output)

                    results.append(output)
            except TypeError:
                pass

            for klass in cls.__subclasses__():
                results += recursive_compile(klass)
            return results

        configs = recursive_compile(cls)

        result = {}
        for config in configs:
            result = recursive_update(result, config)
        return result

    def build(self):
        raise NotImplementedError


class Terraform(TFObject):
    """Represents Terraform configuration.

    See: https://www.terraform.io/docs/configuration/terraform.html
    """

    @classmethod
    def add_hook(cls, hook):
        TFObject.add_hook("terraform", hook)

    def __init__(self, _values=None, **kwargs):
        self._values = _values or {}
        self._values.update(kwargs)

    def build(self):
        return {"terraform": self._values}


class NamedObject(TFObject):
    """Named objects are the Terraform definitions that only have a single name component (i.e. variable or output)"""

    # When recursively compiling, the "type" of object that is written out to the terraform definition needs to point to
    # the top-most subclass of TFobject.  For example, if you create a subclass of Resource named MyResource any
    # instances still needs to be written out to the json as "resource" and not "myresource".  This must be set to an
    # appropriate value at each specific subclass that maps to a terraform resource type.
    TF_TYPE = None

    @classmethod
    def add_hook(cls, object_name, hook):
        """Add a hook for anything that's a direct subclass of NamedObject (i.e. Provider, Variable, etc)

        Unlike the TFobject.add_hook method the hook added for a named object receives just the output for the object
        name, rather than the full compiled output.

        For example::

            Provider.add_hook("aws", my_hook)
            Provider("aws", alias="aws")

        Then your my_hook function would be called like::

            my_hook({"alias": "aws"})

        """

        def named_hook(output):
            for output_name in output[cls.TF_TYPE]:
                if output_name != object_name:
                    continue

                output[cls.TF_TYPE][output_name] = hook(
                    output[cls.TF_TYPE][output_name]
                )

            return output

        TFObject.add_hook(cls.TF_TYPE, named_hook)

    def __init__(self, _name, _values=None, **kwargs):
        """When creating a TF Object you can supply _values if you want to directly influence the values of the object,
        like when you're creating security group rules and need to specify `self`
        """
        assert self.TF_TYPE is not None, (
            "Bad programmer.  Set TF_TYPE on %s" % self.__class__.__name__
        )

        self._name = _name
        self._values = _values or {}

        if Variant.CURRENT_VARIANT is None:
            self._values.update(kwargs)
        else:
            for name in kwargs:
                if not name.endswith("_variant"):
                    self._values[name] = kwargs[name]
                elif name == "{0}_variant".format(Variant.CURRENT_VARIANT.name):
                    self._values.update(kwargs[name])

    def __setattr__(self, name, value):
        if "_values" in self.__dict__ and name in self.__dict__["_values"]:
            self.__dict__["_values"][name] = value
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        """This is here as a safety so that you cannot generate hard to debug .tf.json files"""
        if not TFObject._frozen and name in self._values:
            return self._values[name]
        raise AttributeError(
            "%ss does not provide attribute interpolation through attribute access!"
            % self.__class__.__name__
        )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self._name == other._name
            and self._values == other._values
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def build(self):
        result = {self.TF_TYPE: {self._name: self._values}}
        return result

    def __repr__(self):
        return "{0} {1}".format(type(self), self._name)


class TypedObjectAttr(str):
    """TypedObjectAttr is a wrapper returned by TypedObject for attributes accessed which don't exist.

    The main use case for needing an attr wrapper is accessing interpolated map values, such as those from the
    aws_kms_secrets resource.  We want to support both string-based and integer-based attribute access. Per the
    documentation here:

    https://www.terraform.io/docs/configuration/expressions.html#indices-and-attributes

    However, of note, it appears that several resources - varying by provider version - fail to fully implement both
    specs.  After testing, it appears that dot-separated attributes are more consistently supported. As such, we want
    to return values such as:

    ${resource_type.resource_name.attribute.key_name}
    """

    def __new__(cls, terraform_name, name, item=None):
        obj = super(TypedObjectAttr, cls).__new__(
            cls, "${{{0}.{1}}}".format(terraform_name, cls._name_with_index(name, item))
        )
        obj._terraform_name = terraform_name
        obj._name = name
        obj._item = item
        return obj

    @staticmethod
    def _name_with_index(name, item):
        if item is None:
            return name
        else:
            return "{0}.{1}".format(name, item)

    def __getitem__(self, item):
        return TypedObjectAttr(
            self._terraform_name, self._name_with_index(self._name, self._item), item
        )

    def __getattr__(self, item):
        return TypedObjectAttr(
            self._terraform_name, self._name_with_index(self._name, self._item), item
        )


class TypedObject(NamedObject):
    """Represents a Terraform object that has both a type and name (i.e. resource or data).

    When you access an attribute of an instance of this class it will return the correct interpolation syntax for that
    object.

    .. code-block:: python

        instance = Resource('aws_instance', 'my_instance', ...)
        assert instance.id == '${aws_instance.my_instance.id}'

    This allows you to build up configurations using the instances of the objects as a shortcut to writing out all of
    the interpolation syntax.
    """

    @classmethod
    def add_hook(cls, object_type, hook):
        """Add a hook for the given object type

        Unlike TFObject.add_hook your hook function will be called with the ID of the typed object and its attributes
        rather than the full compiled ouput.

        For example::

            Resource.add_hook("aws_instance", my_hook)
            Resource("aws_instance", "my_instance", instance_type="c5.large")

        Then your my_hook function would be called like::

            my_hook("my_instance", {"instance_type": "c5.large"})

        """

        def typed_hook(output):
            for output_type in output[cls.TF_TYPE]:
                if output_type != object_type:
                    continue

                for object_id in output[cls.TF_TYPE][object_type]:
                    output[cls.TF_TYPE][object_type][object_id] = hook(
                        object_id, output[cls.TF_TYPE][object_type][object_id]
                    )

            return output

        TFObject.add_hook(cls.TF_TYPE, typed_hook)

    def __init__(self, _type, _name, **kwargs):
        super(TypedObject, self).__init__(_name, **kwargs)
        self._type = _type

        try:
            if (
                "provider" not in kwargs
                and Provider.CURRENT_PROVIDER._name == self._type.split("_")[0]
            ):
                self._values["provider"] = Provider.CURRENT_PROVIDER.as_provider()
        except AttributeError:
            # CURRENT_PROVIDER is None
            pass

    def __eq__(self, other):
        return super(TypedObject, self).__eq__(other) and self._type == other._type

    @property
    def terraform_name(self):
        return ".".join([self._type, self._name])

    def interpolated(self, name):
        """If you reference an attr on a TFObject that was provided as a value you will always get back the python object
        instead of the Terraform interpolation string.  If you want the interpolation string this can be used to get it.
        If you don't do this then you can end up without the implicit dependency and can have failures due to ordering.

        Example:

        .. code-block:: python

            role = Resource(
                'aws_iam_role', 'my_role',
                name='my-role',
                ...
            )
            Resource(
                'aws_iam_role_policy_attachment', 'role_attachment',
                role=role.interpolated('name'),
                ...
            )
        """
        try:
            TFObject._frozen = True
            return getattr(self, name)
        finally:
            TFObject._frozen = False

    def __getattr__(self, name):
        if not TFObject._frozen and name in self._values:
            return self._values[name]
        return TypedObjectAttr(self.terraform_name, name)

    def build(self):
        result = {self.TF_TYPE: {self._type: {self._name: self._values}}}
        return result

    def __repr__(self):
        return "{0} {1} {2}".format(type(self), self._type, self._name)

    def __str__(self):
        return self.__repr__()


class Provider(NamedObject):
    """Represents a Terraform provider configuration.

    Providers can be used as context managers, and then provide themselves to all objects created while the context is
    active:

    .. code-block:: python

        with Provider("aws", region="us-west-2", alias="west2"):
            sg = Resource('aws_security_group', 'sg', ingress=['foo'])

        assert sg.provider == 'aws.west2'
    """

    TF_TYPE = "provider"
    CURRENT_PROVIDER = None

    def __init__(self, *args, **kwargs):
        super(Provider, self).__init__(*args, **kwargs)
        self._key = DuplicateKey(self._name)

    def __enter__(self):
        assert self._values[
            "alias"
        ], "Providers must have an alias to be used as a context manager!"
        self._previous_provider = Provider.CURRENT_PROVIDER
        Provider.CURRENT_PROVIDER = self

    def __exit__(self, exc_type, exc_value, traceback):
        Provider.CURRENT_PROVIDER = self._previous_provider

    def as_provider(self):
        return ".".join([self._name, self._values["alias"]])

    # override build to support duplicate key values
    def build(self):
        result = {self.TF_TYPE: {self._key: self._values}}
        return result


class Variable(NamedObject):
    """Represents a Terraform variable

    You can reference the interpolation syntax for a Variable instance by simply using it as a string.

    .. code-block:: python

        var = Variable('my_var', default='foo')
        assert var == '${var.my_var}'
    """

    TF_TYPE = "variable"

    def __repr__(self):
        return "${{var.{0}}}".format(self._name)

    def __str__(self):
        return self.__repr__()


class Output(NamedObject):
    """Represents a Terraform output"""

    TF_TYPE = "output"


class Module(NamedObject):
    """Represents a Terraform module"""

    TF_TYPE = "module"


class Data(TypedObject):
    """Represents a Terraform data source"""

    TF_TYPE = "data"

    @property
    def terraform_name(self):
        return ".".join(["data", super(Data, self).terraform_name])


class Resource(TypedObject):
    """Represents a Terraform resource"""

    TF_TYPE = "resource"
