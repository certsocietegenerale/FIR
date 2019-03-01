from fir_artifacts.artifacts import AbstractArtifact


class IP(AbstractArtifact):
    key = 'ip'
    display_name = 'IPS'
    regex = r'(([^\d])|^)(?P<search>(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9])))(([^\d]|$))'
