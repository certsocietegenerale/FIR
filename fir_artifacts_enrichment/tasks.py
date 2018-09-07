from abuse_finder import domain_abuse, ip_abuse, email_abuse, url_abuse

from fir_artifacts.models import Artifact
from fir_celery.celeryconf import celery_app


ENRICHMENT_FUNCTIONS = {
    'hostname': domain_abuse,
    'ip': ip_abuse,
    'email': email_abuse,
    'url': url_abuse
}


@celery_app.task
def enrich_artifact(artifact_id):
    artifact = Artifact.objects.get(pk=artifact_id)
    print "Enrichment for {}".format(artifact.value)

    if artifact.type in ENRICHMENT_FUNCTIONS:
        results = ENRICHMENT_FUNCTIONS[artifact.type](artifact.value)

    enrichment = ArtifactEnrichment(
        artifact=artifact,
        name='\n'.join(results['names']),
        email='; '.join(results['abuse']),
        raw=results['raw']
    )
    enrichment.save()


from fir_artifacts_enrichment.models import ArtifactEnrichment
