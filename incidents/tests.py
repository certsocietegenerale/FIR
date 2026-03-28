from django.test import TestCase
from django.urls import reverse
import ast
from pathlib import Path


class LoginTemplateLocaleTestCase(TestCase):
    def test_login_template_uses_rtl_for_hebrew(self):
        response = self.client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="he")
        self.assertContains(response, 'lang="he"')
        self.assertContains(response, 'dir="rtl"')

    def test_login_template_does_not_use_rtl_for_english(self):
        response = self.client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="en-us")
        self.assertRegex(response.content.decode(), r'lang="en(?:-us)?"')
        self.assertNotContains(response, 'dir="rtl"')

    def test_hebrew_login_po_catalog_has_translated_auth_strings(self):
        catalogs = [
            (
                Path(__file__).resolve().parent / "locale" / "he" / "LC_MESSAGES" / "django.po",
                {
                    "Sign in &middot; FIR": "התחברות &middot; FIR",
                    "Sign in to FIR": "התחברות ל-FIR",
                    "Username": "שם משתמש",
                    "Remember me": "זכור אותי",
                    "Sign in": "התחבר",
                },
            ),
            (
                Path(__file__).resolve().parents[1]
                / "fir_auth_2fa"
                / "locale"
                / "he"
                / "LC_MESSAGES"
                / "django.po",
                {
                    "Sign in to FIR": "התחברות ל-FIR",
                    "Submit": "שלח",
                    "Back": "חזרה",
                    "Next": "הבא",
                },
            ),
        ]

        for catalog_path, required_translations in catalogs:
            entries = self._parse_po_entries(catalog_path)
            for msgid, msgstr in required_translations.items():
                self.assertIn(msgid, entries)
                self.assertEqual(entries[msgid], msgstr)

            for msgid, msgstr in entries.items():
                if msgid:
                    self.assertTrue(msgstr.strip(), f"Missing Hebrew translation for: {msgid}")

    @staticmethod
    def _parse_po_entries(path):
        entries = {}
        msgid = None
        msgstr = None
        mode = None

        def _decode_po_line(line):
            line = line.strip()
            if not (line.startswith('"') and line.endswith('"')):
                return ""
            return ast.literal_eval(line)

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("#"):
                continue
            if line.startswith("msgid "):
                msgid = _decode_po_line(line[5:].strip())
                msgstr = None
                mode = "msgid"
                continue
            if line.startswith("msgstr "):
                msgstr = _decode_po_line(line[6:].strip())
                mode = "msgstr"
                continue
            if line.startswith('"') and line.endswith('"'):
                if mode == "msgid" and msgid is not None:
                    msgid += _decode_po_line(line)
                elif mode == "msgstr" and msgstr is not None:
                    msgstr += _decode_po_line(line)
                continue
            if line == "" and msgid is not None and msgstr is not None:
                if msgid:
                    entries[msgid] = msgstr
                msgid = None
                msgstr = None
                mode = None

        if msgid and msgstr is not None:
            entries[msgid] = msgstr

        return entries
