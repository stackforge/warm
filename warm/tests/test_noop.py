
from warm.openstack.common import test


class TestCase(test.BaseTestCase):

    def test_noop(self):
        self.assertTrue(True)
