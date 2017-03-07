import pytest

from terraformpy.objects import Resource
from terraformpy.resource_collections import ResourceCollection, Input, MissingInput, Variant


def test_resource_collection():
    class TestCollection(ResourceCollection):
        foo = Input()
        bar = Input(True)

        def create_resources(self):
            self.res1 = Resource('res1', 'foo', foo=self.foo)

    tc = TestCollection(foo='foo!')
    assert tc.foo == 'foo!'
    assert tc.res1.foo == '${res1.foo.foo}'
    assert tc.res1._values['foo'] == 'foo!'

    with pytest.raises(MissingInput):
        TestCollection()


def test_variants():
    class TestCollection(ResourceCollection):
        foo = Input()
        bar = Input('default bar!')

        def create_resources(self):
            self.res1 = Resource('res1', 'foo', foo=self.foo)

    def make_collection():
        return TestCollection(
            foo='foo!',

            prod_variant=dict(
                bar='prod bar!'
            ),

            stage_variant=dict(
                bar='stage bar!'
            )
        )

    with Variant('prod'):
        tc = make_collection()
        assert tc.bar == 'prod bar!'

    with Variant('stage'):
        tc = make_collection()
        assert tc.bar == 'stage bar!'
