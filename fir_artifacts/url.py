import re

from fir_artifacts.artifacts import AbstractArtifact


class URL(AbstractArtifact):
    key = 'url'
    display_name = 'URLs'
    regex = r"""
        (?P<search>
          ((?P<scheme>[\w]{2,9}):\/\/)?
          ([\S]*\:[\S]*\@)?
          (?P<hostname>(
                      ((([\w\-]+\.)+)
                      ([a-zA-Z]{2,6}))
                      |([\d+]{1,3}\.[\d+]{1,3}\.[\d+]{1,3}\.[\d+]{1,3})
                      )
          )

          (\:[\d]{1,5})?
          (?P<path>(\/[\/\~\w\-_%\.\*\#\$&%]*)?
            (\?[\~\w\-_%\.&=\*\#\$%]*)?
            (\#[\S]*)?)
        )
    """

    @classmethod
    def find(cls, data):
        urls = []
        _re = re.compile(cls.regex, re.VERBOSE)
        for i in re.finditer(_re, data):
            url = i.group('search')
            if url.find('/') != -1:
                urls.append(url)

        return urls
