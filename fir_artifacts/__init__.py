from fir_artifacts import artifacts
from fir_artifacts.ip import IP
from fir_artifacts.url import URL
from fir_artifacts.hostname import Hostname
from fir_artifacts.hash import Hash
from fir_artifacts.email import Email

artifacts.install(IP)
artifacts.install(URL)
artifacts.install(Hostname)
artifacts.install(Hash)
artifacts.install(Email)
