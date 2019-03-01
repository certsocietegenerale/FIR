from django.contrib import admin

from fir_artifacts.models import ArtifactBlacklistItem, File, Artifact

admin.site.register(ArtifactBlacklistItem)
admin.site.register(Artifact)
admin.site.register(File)
