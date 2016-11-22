import mimetypes
import os
import zipfile
from io import BytesIO

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper

from fir_artifacts import Hash
from fir_artifacts.models import File, Artifact


def do_upload_file(request, content_type, object_id):

    if request.method == 'POST':
        object_type = ContentType.objects.get(pk=content_type)
        obj = get_object_or_404(object_type.model_class(), pk=object_id)
        if not request.user.has_perm('incidents.handle_incidents', obj=obj):
            raise PermissionDenied()
        descriptions = request.POST.getlist('description')
        files = request.FILES.getlist('file')
        if len(descriptions) == len(files):  # consider this as a valid upload form?
            for i, file in enumerate(files):
                handle_uploaded_file(file, descriptions[i], obj)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def handle_uploaded_file(file, description, obj):

    f = File()
    f.description = description
    f.file = file
    f.content_object = obj
    f.save()

    hashes = f.get_hashes()
    for h in hashes:
        try:
            a = Artifact.objects.get(value=hashes[h])
            a.save()
        except Exception:
            a = Artifact()
            a.type = Hash.key
            a.value = hashes[h]
            a.save()

        a.relations.add(obj)
        f.hashes.add(a)
    f.save()

    return f


def do_download(request, file_id):
    f = get_object_or_404(File, pk=file_id)
    if not request.user.has_perm('incidents.view_incidents', obj=f.get_related()):
        raise PermissionDenied()
    wrapper = FileWrapper(f.file)
    content_type = mimetypes.guess_type(f.file.name)
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % (f.getfilename())
    response['Content-Length'] = os.path.getsize(str(f.file.file))

    return response


def do_download_archive(request, content_type, object_id):
    object_type = ContentType.objects.get(pk=content_type)
    obj = get_object_or_404(object_type.model_class(), pk=object_id)
    if not request.user.has_perm('incidents.view_incidents', obj=obj):
        raise PermissionDenied()
    if obj.file_set.count() == 0:
        raise Http404
    temp = BytesIO()
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
        media_root = settings.MEDIA_ROOT
        for file in obj.file_set.all():
            path = os.path.join(media_root, file.file.path)
            archive.write(path, os.path.basename(path))
    file_size = temp.tell()
    temp.seek(0)
    wrapper = FileWrapper(temp)

    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=archive_%s_%s.zip' % (object_type.model, object_id)
    response['Content-Length'] = file_size
    return response


def do_remove_file(request, file_id):
    if request.method == "POST":
        f = get_object_or_404(File, pk=file_id)
        if not request.user.has_perm('incidents.handle_incidents', obj=f.get_related()):
            raise PermissionDenied()
        f.file.delete()
        f.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
