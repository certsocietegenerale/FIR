from fir_artifacts.artifacts import AbstractArtifact


class IP(AbstractArtifact):
	key = 'ip'
	display_name = 'IPS'
	regex = r"(?P<search>[\d+]{1,3}\.[\d+]{1,3}\.[\d+]{1,3}\.[\d+]{1,3})"
