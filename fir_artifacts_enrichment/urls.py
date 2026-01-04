from fir_artifacts_enrichment import api

app_name = "fir_artifacts_enrichment"

urlpatterns = []

api_urls = [
    ("artifacts_enrichment", api.ArtifactsEnrichmentViewSet),
]
