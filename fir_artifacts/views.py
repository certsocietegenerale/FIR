from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from fir_artifacts.files import do_download_archive, do_download, do_upload_file, do_remove_file

from incidents.views import is_incident_viewer

from fir_artifacts.models import Artifact


@login_required
@user_passes_test(is_incident_viewer)
def artifacts_correlations(request, artifact_id):
    a = get_object_or_404(Artifact, pk=artifact_id)
    correlations = a.relations_for_user(request.user).group()
    if all([not link_type.objects.exists() for link_type in correlations.values()]):
        raise PermissionDenied
    return render(request, 'fir_artifacts/correlation_list.html', {'correlations': correlations,
                                                                   'artifact': a,
                                                                   'incident_show_id': settings.INCIDENT_SHOW_ID})


@login_required
def detach_artifact(request, artifact_id, relation_name, relation_id):
    a = get_object_or_404(Artifact, pk=artifact_id)
    relation = getattr(a, relation_name, None)
    if relation is None:
        raise Http404("Unknown relation")
    try:
        related = relation.get(pk=relation_id)
    except:
        raise Http404("Unknown related object")
    if not request.user.has_perm('incidents.handle_incidents', obj=related):
        raise PermissionDenied()
    a.relations.remove(related)
    if a.relations.count() == 0:
        a.delete()
    return redirect('%s:details' % relation_name, relation_id)


@login_required
def download_archive(request, content_type, object_id):
    return do_download_archive(request, content_type, object_id)


@login_required
def download(request, file_id):
    return do_download(request, file_id)


@login_required
def upload_file(request, content_type, object_id):
    return do_upload_file(request, content_type, object_id)


@login_required
def remove_file(request, file_id):
    return do_remove_file(request, file_id)
