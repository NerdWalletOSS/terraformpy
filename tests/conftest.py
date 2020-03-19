import pytest

from terraformpy import TFObject


@pytest.fixture(autouse=True, scope="function")
def reset_tfobject():
    TFObject.reset()
