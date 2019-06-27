import pytest
import schematics.exceptions
from schematics import types

from terraformpy.objects import Data, Resource
from terraformpy.resource_collections import ResourceCollection, Variant

if hasattr(schematics.exceptions, 'ConversionError'):
    # schematics 2+
    SCHEMATICS_EXCEPTIONS = (
        schematics.exceptions.ValidationError,
        schematics.exceptions.ConversionError,
        schematics.exceptions.DataError,
    )
else:
    # schematics 1
    SCHEMATICS_EXCEPTIONS = (schematics.exceptions.ValidationError,)


def test_resource_collection():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.BooleanType(default=True)

        def create_resources(self):
            self.res1 = Resource('res1', 'foo', foo=self.foo)

    tc = TestCollection(foo='foo!')
    assert tc.foo == 'foo!'
    assert tc.res1.foo == 'foo!'
    assert tc.res1.id == '${res1.foo.id}'

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection()


def test_variants():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(default='default bar!')

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
        foo = types.StringType(required=True)
        bar = types.StringType(default='')
        baz = types.EmailType(required=True)

        def create_resources(self):
            pass

        def validate_foo(self, data, value):
            if not value.endswith('!'):
                raise schematics.exceptions.ValidationError('foo must end in !')

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection(foo='foo!')

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection(foo='foo!', baz='not an email')

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection(foo='no-exclaimation-mark', baz='baz@baz.com')

    tc = TestCollection(foo='foo!', baz='bbq@lol.tld')
    assert tc.baz == 'bbq@lol.tld'
    assert tc.foo == 'foo!'


def test_variant_defaults():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(default='default bar!')

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
        foo = types.StringType(required=True)

        def create_resources(self):
            self.res1 = Resource('res1', 'foo', foo=self.foo)

    tc = TestCollection(foo='foo!')

    assert tc.relative_file('foo') == '${file("${path.module}/tests/foo")}'


def test_typed_attr_as_strings():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(required=True)

        def create_resources(self):
            pass

    data = Data('data_type', 'data_id')

    tc = TestCollection(foo=data.baz, bar=data.baz["bbq"])
    assert tc.foo == '${data.data_type.data_id.baz}'
    assert tc.bar == '${data.data_type.data_id.baz["bbq"]}'
