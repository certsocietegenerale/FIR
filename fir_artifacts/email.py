from fir_artifacts.artifacts import AbstractArtifact


class Email(AbstractArtifact):
    key = 'email'
    display_name = 'Emails'
    regex = r"(?P<search>[\w\-\.\_]+@(([\w\-]+\.)+)([a-zA-Z]{2,6}))\.?"
