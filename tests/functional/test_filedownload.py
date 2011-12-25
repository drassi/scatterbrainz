from scatterbrainz.tests import *

class TestFiledownloadController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='filedownload', action='index'))
        # Test response...
