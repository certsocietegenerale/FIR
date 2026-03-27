from django.test import TestCase
from django.urls import reverse


class LoginTemplateLocaleTestCase(TestCase):
    def test_login_template_uses_rtl_for_hebrew(self):
        response = self.client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="he")
        self.assertContains(response, 'lang="he"')
        self.assertContains(response, 'dir="rtl"')

    def test_login_template_does_not_use_rtl_for_english(self):
        response = self.client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="en-us")
        self.assertRegex(response.content.decode(), r'lang="en(?:-us)?"')
        self.assertNotContains(response, 'dir="rtl"')
