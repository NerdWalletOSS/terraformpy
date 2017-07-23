import pytest
import schematics.types
import schematics.exceptions

from terraformpy.objects import Resource, TFObject
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
    assert Variant.CURRENT_VARIANT is None

    with Variant('foo'):
        assert Variant.CURRENT_VARIANT.name == 'foo'

        with Variant('bar'):
            assert Variant.CURRENT_VARIANT.name == 'bar'

        assert Variant.CURRENT_VARIANT.name == 'foo'

    assert Variant.CURRENT_VARIANT is None


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


def test_variant_defaults():
    class TestCollection(ResourceCollection):
        foo = Input()
        bar = Input('default bar!')

        def create_resources(self):
            self.res1 = Resource('res1', 'foo', foo=self.foo)

    with Variant('testing', foo='variant default foo!'):
        tc = TestCollection()
        assert tc.foo == 'variant default foo!'

    with Variant('testing2', bar='variant default bar!'):
        tc = TestCollection(foo='test foo!')
        assert tc.foo == 'test foo!'
        assert tc.bar == 'variant default bar!'

    with Variant('testing3'):
        tc = TestCollection(
            foo='test foo!',
            testing3_variant=dict(
                foo='testing3 foo!'
            )
        )
        assert tc.foo == 'testing3 foo!'
        assert tc.bar == 'default bar!'


def test_relative_file():
    class TestCollection(ResourceCollection):
        foo = Input()

        def create_resources(self):
            self.res1 = Resource('res1', 'foo', foo=self.foo)

    tc = TestCollection(foo='foo!')

    assert tc.relative_file('foo') == '${file("${path.module}/tests/foo")}'


def test_finalize_ordering():
    """Finalize should run in the reverse order that resource collections are created"""
    class TC1(ResourceCollection):
        def create_resources(self):
            self.finalized = False
            self.tc2 = None

        def finalize_resources(self):
            self.finalized = True
            assert self.tc2 is not None

    class TC2(ResourceCollection):
        tc1 = Input()

        def create_resources(self):
            pass

        def finalize_resources(self):
            self.tc1.tc2 = self

    tc1 = TC1()
    tc2 = TC2(tc1=tc1)

    assert not tc1.finalized

    TFObject.compile()

    assert tc1.finalized
    assert tc1.tc2 == tc2
