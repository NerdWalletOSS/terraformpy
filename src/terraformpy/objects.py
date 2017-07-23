"""Terraform "objects"

This module provides a set of classes that can be used to build Terraform configurations in a (mostly) declarative way,
while also leveraging Python to add some functional aspects to automate some of the more repetitive aspects of HCL.
"""
import collections
import six

from .resource_collections import ResourceCollection, Variant


def recursive_update(dest, source):
    """Like dict.update, but recursive"""
    for key, val in six.iteritems(source):
        if isinstance(val, collections.Mapping):
            recurse = recursive_update(dest.get(key, {}), val)
            dest[key] = recurse
        else:
            dest[key] = val
    return dest


# Provider names are duplicate keys in the resulting json, so we need a way to represent that
class DuplicateKey(str):
    def __hash__(self):
        return id(self)


class TFObject(object):
    _instances = None
    _frozen = False

    # When recursively compiling, the "type" of object that is written out to the terraform definition needs to point to
    # the top-most subclass of TFobject.  For example, if you create a subclass of Resource named MyResource any
    # instances still needs to be written out to the json as "resource" and not "myresource".  This must be set to an
    # appropriate value at each specific subclass that maps to a terraform resource type.
    TF_TYPE = None

    def __new__(cls, *args, **kwargs):
        # create the instance
        inst = super(TFObject, cls).__new__(cls, *args, **kwargs)

        assert inst.TF_TYPE is not None, "Bad programmer.  Set TF_TYPE on %s" % cls.__name__

        # register it on the class
        try:
            cls._instances.append(inst)
        except AttributeError:
            cls._instances = [inst]

        # return it
        return inst

    @classmethod
    def reset(cls):
        def recursive_reset(cls):
            cls._instances = None
            for klass in cls.__subclasses__():
                recursive_reset(klass)
        recursive_reset(cls)
        TFObject._frozen = False

    @classmethod
    def compile(cls):
        TFObject._frozen = True

        # allow resource collections to have a final hurrah before we compile
        if ResourceCollection._instances:
            for collection in reversed(ResourceCollection._instances):
                collection.finalize_resources()

        def recursive_compile(cls):
            results = []
            try:
                for instance in cls._instances:
                    output = instance.build()
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


class NamedObject(TFObject):
    """Named objects are the Terraform definitions that only have a single name component (i.e. variable or output)"""
    def __init__(self, _name, _values=None, **kwargs):
        """When creating a TF Object you can supply _values if you want to directly influence the values of the object,
        like when you're creating security group rules and need to specify `self`
        """
        self._name = _name
        self._values = _values or {}

        if Variant.CURRENT_VARIANT is None:
            self._values.update(kwargs)
        else:
            for name in kwargs:
                if not name.endswith('_variant'):
                    self._values[name] = kwargs[name]
                elif name == '{0}_variant'.format(Variant.CURRENT_VARIANT.name):
                    self._values.update(kwargs[name])

    def __setattr__(self, name, value):
        if '_values' in self.__dict__ and name in self.__dict__['_values']:
            self.__dict__['_values'][name] = value
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        """This is here as a safety so that you cannot generate hard to debug .tf.json files"""
        if not TFObject._frozen and name in self._values:
            return self._values[name]
        raise AttributeError("%ss does not provide attribute interpolation through attribute access!" %
                             self.__class__.__name__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._name == other._name and self._values == other._values

    def __ne__(self, other):
        return not self.__eq__(other)

    def build(self):
        result = {
            self.TF_TYPE: {
                self._name: self._values
            }
        }
        return result

    def __repr__(self):
        return "{0} {1}".format(type(self), self._name)


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
    def __init__(self, _type, _name, **kwargs):
        super(TypedObject, self).__init__(_name, **kwargs)
        self._type = _type

        try:
            if Provider.CURRENT_PROVIDER._name == self._type.split('_')[0]:
                self._values['provider'] = Provider.CURRENT_PROVIDER.as_provider()
        except AttributeError:
            # CURRENT_PROVIDER is None
            pass

    def __eq__(self, other):
        return super(TypedObject, self).__eq__(other) and self._type == other._type

    @property
    def terraform_name(self):
        return '.'.join([self._type, self._name])

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
        return '${{{0}.{1}}}'.format(self.terraform_name, name)

    def build(self):
        result = {
            self.TF_TYPE: {
                self._type: {
                    self._name: self._values
                }
            }
        }
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

    def __enter__(self):
        assert self._values['alias'], "Providers must have an alias to be used as a context manager!"
        self._previous_provider = Provider.CURRENT_PROVIDER
        Provider.CURRENT_PROVIDER = self

    def __exit__(self, exc_type, exc_value, traceback):
        Provider.CURRENT_PROVIDER = self._previous_provider

    def as_provider(self):
        return '.'.join([self._name, self._values['alias']])

    # override build to support duplicate key values
    def build(self):
        result = {
            self.TF_TYPE: {
                DuplicateKey(self._name): self._values
            }
        }
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
        return '${{var.{0}}}'.format(self._name)

    def __str__(self):
        return self.__repr__()


class Output(NamedObject):
    """Represents a Terraform output"""
    TF_TYPE = "output"


class Data(TypedObject):
    """Represents a Terraform data source"""
    TF_TYPE = "data"

    @property
    def terraform_name(self):
        return '.'.join(['data', super(Data, self).terraform_name])


class Resource(TypedObject):
    """Represents a Terraform resource"""
    TF_TYPE = "resource"
