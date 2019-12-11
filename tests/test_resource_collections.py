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

import pytest
import schematics.exceptions
from schematics import types
from schematics.types import compound

from terraformpy.objects import Data, Resource
from terraformpy.resource_collections import ResourceCollection, Variant

if hasattr(schematics.exceptions, "ConversionError"):
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
            self.res1 = Resource("res1", "foo", foo=self.foo)

    tc = TestCollection(foo="foo!")
    assert tc.foo == "foo!"
    assert tc.res1.foo == "foo!"
    assert tc.res1.id == "${res1.foo.id}"

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection()


def test_variants():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(default="default bar!")

        def create_resources(self):
            self.res1 = Resource("res1", "foo", foo=self.foo)

    def make_collection():
        return TestCollection(
            foo="foo!",
            prod_variant=dict(bar="prod bar!"),
            stage_variant=dict(bar="stage bar!"),
        )

    tc = make_collection()
    assert tc.bar == "default bar!"

    with Variant("prod"):
        tc = make_collection()
        assert tc.bar == "prod bar!"

    with Variant("stage"):
        tc = make_collection()
        assert tc.bar == "stage bar!"


def test_multiple_variants():
    assert Variant.CURRENT_VARIANT is None

    with Variant("foo"):
        assert Variant.CURRENT_VARIANT.name == "foo"

        with Variant("bar"):
            assert Variant.CURRENT_VARIANT.name == "bar"

        assert Variant.CURRENT_VARIANT.name == "foo"

    assert Variant.CURRENT_VARIANT is None


def test_schematics():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(default="")
        baz = types.EmailType(required=True)

        def create_resources(self):
            pass

        def validate_foo(self, data, value):
            if not value.endswith("!"):
                raise schematics.exceptions.ValidationError("foo must end in !")

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection(foo="foo!")

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection(foo="foo!", baz="not an email")

    with pytest.raises(SCHEMATICS_EXCEPTIONS):
        TestCollection(foo="no-exclaimation-mark", baz="baz@baz.com")

    tc = TestCollection(foo="foo!", baz="bbq@lol.tld")
    assert tc.baz == "bbq@lol.tld"
    assert tc.foo == "foo!"


def test_variant_defaults():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(default="default bar!")

        def create_resources(self):
            self.res1 = Resource("res1", "foo", foo=self.foo)

    with Variant("testing", foo="variant default foo!"):
        tc = TestCollection()
        assert tc.foo == "variant default foo!"

    with Variant("testing2", bar="variant default bar!"):
        tc = TestCollection(foo="test foo!")
        assert tc.foo == "test foo!"
        assert tc.bar == "variant default bar!"

    with Variant("testing3"):
        tc = TestCollection(foo="test foo!", testing3_variant=dict(foo="testing3 foo!"))
        assert tc.foo == "testing3 foo!"
        assert tc.bar == "default bar!"


def test_relative_file():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)

        def create_resources(self):
            self.res1 = Resource("res1", "foo", foo=self.foo)

    tc = TestCollection(foo="foo!")

    assert tc.relative_file("foo") == '${file("${path.module}/tests/foo")}'


def test_typed_attr_as_strings():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(required=True)

        def create_resources(self):
            pass

    data = Data("data_type", "data_id")

    tc = TestCollection(foo=data.baz, bar=data.baz["bbq"])
    assert tc.foo == "${data.data_type.data_id.baz}"
    assert tc.bar == "${data.data_type.data_id.baz.bbq}"


def test_typed_attr_as_int():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(required=True)

        def create_resources(self):
            pass

    data = Data("data_type", "data_id")

    tc = TestCollection(foo=data.baz[0], bar=data.baz[1])
    assert tc.foo == "${data.data_type.data_id.baz.0}"
    assert tc.bar == "${data.data_type.data_id.baz.1}"


def test_typed_item_recursion():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(required=True)

        def create_resources(self):
            pass

    data = Data("data_type", "data_id")

    tc = TestCollection(
        foo=data.baz[0]["resource_collection"]["resource"],
        bar=data.baz[1]["resource_collection"]["resource"],
    )
    assert tc.foo == "${data.data_type.data_id.baz.0.resource_collection.resource}"
    assert tc.bar == "${data.data_type.data_id.baz.1.resource_collection.resource}"


def test_typed_attr_recursion():
    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(required=True)

        def create_resources(self):
            pass

    data = Data("data_type", "data_id")

    tc = TestCollection(
        foo=data.baz[0].resource_collection.resource,
        bar=data.baz[1].resource_collection.resource,
    )
    assert tc.foo == "${data.data_type.data_id.baz.0.resource_collection.resource}"
    assert tc.bar == "${data.data_type.data_id.baz.1.resource_collection.resource}"


def test_model_type():
    class C1(ResourceCollection):
        foo = types.StringType(required=True)

        def create_resources(self):
            pass

    class C2(ResourceCollection):
        c1 = compound.ModelType(C1, required=True)

        def create_resources(self):
            pass

    c1 = C1(foo="foo")
    c2 = C2(c1=c1)

    assert c2.c1.foo == "foo"


def test_mock_object_creation():
    class C1(ResourceCollection):
        foo = types.StringType(required=True)

        def create_resources(self):
            pass

    class TestCollection(ResourceCollection):
        foo = types.StringType(required=True)
        bar = types.StringType(required=True)
        baz = types.IntType(required=True)
        c1 = compound.ModelType(C1, required=True)

        def create_resources(self):
            pass

    tc = TestCollection.get_mock_object()

    # When the bug presented itself, these fields would have been set to None
    # because the original get_mock_object implementation passes the fields
    # as a single dictionary. There is probably a more elegant way to do this,
    # but it's sufficient that the objects can be created without errors
    assert tc.foo is not None
    assert tc.bar is not None
    assert tc.baz is not None
    assert tc.c1.foo is not None
