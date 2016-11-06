from pyterraform import TFObject, Data, Resource, Variable


def test_registered_objects():
    obj1 = TFObject()
    assert TFObject._instances == [obj1]


def test_named_object():
    var = Variable('var1', default='foo')

    assert var.name == 'var1'
    assert var.values == {
        'default': 'foo'
    }


def test_typed_object():
    ami = Data("aws_ami", "ecs_ami",
               most_recent=True,
               filter=[
                   dict(name="name", values=["*amazon-ecs-optimized"]),
                   dict(name="owner-alias", values=["amazon"]),
               ])

    assert ami.type == 'aws_ami'
    assert ami.name == 'ecs_ami'
    assert ami.values == {
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
