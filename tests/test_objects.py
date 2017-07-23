import pytest

import json
from terraformpy import TFObject, Data, Resource, Variable, Variant, DuplicateKey, Provider


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


def test_duplicate_key():
    x = {DuplicateKey("mysql"): {"user": "wyatt"}, DuplicateKey("mysql"): {"user": "wyatt"}}
    encoded = json.dumps(x, sort_keys=True)
    desired = '{"mysql": {"user": "wyatt"}, "mysql": {"user": "wyatt"}}'
    assert encoded == desired


# Make sure provider supports duplicate key names
def test_provider():
    TFObject.reset()

    Provider("mysql", host="db-wordpress")
    Provider("mysql", host="db-finpro")

    result = json.dumps(TFObject.compile(), sort_keys=True)
    desired = '{"provider": {"mysql": {"host": "db-wordpress"}, "mysql": {"host": "db-finpro"}}}'

    assert result == desired


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
