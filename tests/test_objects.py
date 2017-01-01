import pytest

from terraformpy import TFObject, Data, Resource, Variable


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
    with pytest.raises(RuntimeError):
        assert var1.id, 'nope!  vars do not have attrs!'


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
