from fir_artifacts.artifacts import AbstractArtifact


class Hash(AbstractArtifact):
    key = 'hash'
    display_name = 'Hashes'
    regex = r"(?P<search>[a-fA-F0-9]{32,64})"
