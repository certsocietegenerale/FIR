from fir_artifacts.artifacts import AbstractArtifact
import re


class Phone(AbstractArtifact):
    key = "phone"
    display_name = "Phone Numbers"
    regex = r"""(?P<search>
        \+\d{1,3}                                  # country code
        [ \t.\-()]*                                # optional separators (no newlines)
        (?:\(?\d{1,4}\)?[ \t.\-()]*)?              # optional area code
        \d{1,4}                                    # main number start
        (?:[ \t.\-()]*\d{2,4}){1,4}                # remaining groups
    )"""

    @classmethod
    def find(cls, data):
        results = []
        _re = re.compile(cls.regex, re.VERBOSE)
        for match in re.finditer(_re, data):
            raw = match.group("search")
            # remove (0) if any
            raw = raw.replace("(0)", "")
            # remove common separators
            cleaned = re.sub(r"[()\t \xa0\-\.]", "", raw)
            digits_only = re.sub(r"\D", "", cleaned)
            if len(digits_only) < 9 or len(digits_only) > 15:
                # Invalid phone numbers
                continue
            results.append(cleaned)
        return results
