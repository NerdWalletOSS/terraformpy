import pytest
import schematics.types
import schematics.exceptions

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
    assert tc.res1.foo == 'foo!'
    assert tc.res1.id == '${res1.foo.id}'

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

    tc = make_collection()
    assert tc.bar == 'default bar!'

    with Variant('prod'):
        tc = make_collection()
        assert tc.bar == 'prod bar!'

    with Variant('stage'):
        tc = make_collection()
        assert tc.bar == 'stage bar!'


def test_multiple_variants():
    with Variant('foo'):
        with pytest.raises(AssertionError):
            with Variant('bar'):
                pass


def test_schematics():
    class TestCollection(ResourceCollection):
        foo = schematics.types.StringType(required=True)
        bar = schematics.types.StringType()
        baz = schematics.types.EmailType(required=True)

        def create_resources(self):
            pass

    with pytest.raises(schematics.exceptions.ValidationError):
        TestCollection(foo='foo!')

    with pytest.raises(schematics.exceptions.ValidationError):
        TestCollection(foo='foo!', baz='not an email')

    tc = TestCollection(foo='foo!', baz='bbq@lol.tld')
    assert tc.baz == 'bbq@lol.tld'
    assert tc.foo == 'foo!'
