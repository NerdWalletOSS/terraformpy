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

import collections
import json

import pytest
import schematics.types
import six

from terraformpy import Data, DuplicateKey, Module, OrderedDict, Provider, Resource, Terraform, TFObject, Variable, Variant


def test_object_instances():
    res = Resource('res1', 'foo', attr='value')
    var = Variable('var1', default='foo')

    assert TFObject._instances is None
    assert Resource._instances == [res]
    assert Variable._instances == [var]


def test_named_object():
    var = Variable('var1', default='foo')

    assert var._name == 'var1'
    assert var._values == {
        'default': 'foo'
    }


def test_typed_object():
    ami = Data("aws_ami", "ecs_ami",
               most_recent=True,
               filter=[
                   dict(name="name", values=["*amazon-ecs-optimized"]),
                   dict(name="owner-alias", values=["amazon"]),
               ])

    assert ami._type == 'aws_ami'
    assert ami._name == 'ecs_ami'
    assert ami._values == {
        'most_recent': True,
        'filter': [
            dict(name="name", values=["*amazon-ecs-optimized"]),
            dict(name="owner-alias", values=["amazon"]),
        ]
    }


def test_compile():
    TFObject.reset()

    Resource('res1', 'foo', attr='value')
    Resource('res1', 'bar', attr='other')
    Variable('var1', default='value')

    assert TFObject.compile() == {
        'resource': {
            'res1': {
                'foo': {
                    'attr': 'value',
                },
                'bar': {
                    'attr': 'other',
                }
            },
        },
        'variable': {
            'var1': {
                'default': 'value'
            }
        }
    }


def test_getattr():
    res1 = Resource('res1', 'foo', attr='value')
    assert res1.id == '${res1.foo.id}'

    var1 = Variable('var1', default='value')
    assert '{0}'.format(var1) == '${var.var1}'
    with pytest.raises(AttributeError):
        assert var1.id, 'nope!  vars do not have attrs!'


def test_setattr():
    res1 = Resource('res1', 'foo', attr='value')

    assert res1.attr == "value"
    assert res1._values['attr'] == "value"

    res1.not_tf_attr = "value"
    assert res1.not_tf_attr == "value"
    assert 'not_tf_attr' not in res1._values


def test_tf_type():
    TFObject.reset()

    class TestResource(Resource):
        pass

    TestResource('res1', 'foo', attr='value')

    assert TFObject.compile() == {
        'resource': {
            'res1': {
                'foo': {
                    'attr': 'value',
                }
            }
        }
    }


def test_access_before_compile():
    sg = Resource('aws_security_group', 'sg', ingress=['foo'])

    assert sg.id == '${aws_security_group.sg.id}'
    assert sg.ingress == ['foo']

    TFObject._frozen = True

    assert sg.ingress == '${aws_security_group.sg.ingress}'


def test_object_variants():
    with Variant('foo', default='value'):
        sg = Resource(
            'aws_security_group', 'sg',
            foo_variant=dict(ingress=['foo']),
            bar_variant=dict(ingress=['bar'])
        )

        assert sg.ingress == ['foo']

        # objects do not pickup defaults from variants
        assert sg.default != 'value'


def test_provider_context():
    with Provider("aws", region="us-east-1", alias="east1"):
        sg1 = Resource('aws_security_group', 'sg', ingress=['foo'])

        # Since thing1 is not an aws_ resource it will not get the provider by default
        thing1 = Resource('some_thing', 'foo', bar='baz')

        # var1 is not a typedobject so it will not get a provider either
        var1 = Variable('var1', default='foo')

        with Provider("aws", region="us-west-2", alias="west2"):
            sg2 = Resource('aws_security_group', 'sg', ingress=['foo'])

    assert sg1.provider == 'aws.east1'
    assert sg2.provider == 'aws.west2'

    # thing1's provider is the default interpolation string
    assert thing1.provider == '${some_thing.foo.provider}'

    # var1 will raise a AttributeError
    with pytest.raises(AttributeError):
        assert var1.provider


def test_explicit_provider():
    # When a resource is given an explicit provider argument it should take precendence
    # Even if we're in a provider resource block
    p1 = Provider("aws", region="us-west-2", alias="west2")
    with Provider("aws", region="us-east-1", alias="east1"):
        sg1 = Resource("aws_security_group", "sg", ingress=["foo"], provider=p1.as_provider())
        sg2 = Resource("aws_security_group", "sg", ingress=["foo"])

        with Provider("aws", region="eu-west-2", alias="london"):
            sg3 = Resource("aws_security_group", "sg", ingress=["foo"])

    assert sg1.provider == "aws.west2"
    assert sg2.provider == "aws.east1"
    assert sg3.provider == "aws.london"


def test_ordered_dict():
    typ = OrderedDict(schematics.types.IntType)

    keys = ["hello", "world", "crazy", "beans"]
    od = collections.OrderedDict()
    for k in keys:
        od[k] = 0

    assert list(typ.convert(od).keys()) == keys


# Make sure provider supports duplicate key names
def test_provider():
    TFObject.reset()

    Provider("mysql", host="db-wordpress")
    Provider("mysql", host="db-finpro")

    seen = []
    for data in six.itervalues(compiled["provider"]):
        seen.append(data["host"])

    seen.sort()
    assert seen == ["db-finpro", "db-wordpress"]


def test_interpolated():
    foo = Resource('aws_security_group', 'sg', name='sg')

    assert foo.name == 'sg'
    assert foo.interpolated('name') == '${aws_security_group.sg.name}'

    # call .name again to ensure ._frozen is reset correctly and we can still mutate the original
    assert foo.name == 'sg'


def test_equality():
    # NamedObject
    p1 = Provider("mysql", host="db")
    p2 = Provider("mysql", host="db")
    v1 = Variable("mysql", host="db")
    assert p1 == p2
    assert p1 != v1

    # TypedObject
    r1 = Resource('aws_security_group', 'sg', name='sg')
    r2 = Resource('aws_security_group', 'sg', name='sg')
    d1 = Data('aws_security_group', 'sg', name='sg')
    assert r1 == r2
    assert r1 != d1

    # Invalid comparisons
    assert r1 != "string"
    assert r1 != 0


def test_terraform_config():
    tf = Terraform(
        backend=dict(
            s3=dict(
                bucket='bucket'
            )
        )
    )

    assert tf.build() == {
        'terraform': {
            'backend': {
                's3': {
                    'bucket': 'bucket'
                }
            }
        }
    }


def test_attr_map_access():
    secrets = Data(
        "aws_kms_secrets", "test",
        secret=[
            {
                "name": "foo",
                "payload": "bar",
            },
        ]
    )

    assert secrets.plaintext["foo"] == '${data.aws_kms_secrets.test.plaintext.foo}'


def test_module():
    mod = Module(
        "consul",
        source="hashicorp/consul/aws",
        version="0.0.5",
        servers=3
    )

    assert mod.build() == {
        "module": {
            "consul": {
                "source": "hashicorp/consul/aws",
                "version": "0.0.5",
                "servers": 3
            }
        }
    }


def test_duplicate_key_collisions():
    """When creating two different types of Provider objects they would collide with
    each other during recursive update because they had the same __hash__ value

    The fix was use the hash() value of the key being provide PLUS our incremented ID

    This test covers that by making sure that all of the expected providers are in our
    compiled output.
    """
    TFObject.reset()

    Provider("aws", alias="aws1")
    Provider("aws", alias="aws2")
    Provider("mysql", alias="mysql1")
    Provider("mysql", alias="mysql2")

    assert len(Provider._instances) == 4

    compiled = Provider.compile()

    seen = []
    for data in six.itervalues(compiled["provider"]):
        seen.append(data["alias"])

    seen.sort()
    assert seen == ["aws1", "aws2", "mysql1", "mysql2"]
