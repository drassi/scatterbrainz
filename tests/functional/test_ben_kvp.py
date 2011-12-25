from scatterbrainz.tests import *

class TestBenKvpController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='ben_kvp', action='index'))
        # Test response...
