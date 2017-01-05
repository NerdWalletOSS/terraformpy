import pytest

from terraformpy.objects import Resource
from terraformpy.resource_collections import ResourceCollection, Input, MissingInput


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
