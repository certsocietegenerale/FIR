from django.conf import settings


class FakeRequest(object):
    def __init__(self):
        self.base = ""
        if hasattr(settings, 'EXTERNAL_URL'):
            self.base = settings.EXTERNAL_URL
            if self.base.endswith('/'):
                self.base = self.base[:-1]

    def build_absolute_uri(self, location):
        return "{}{}".format(self.base, location)

request = FakeRequest()