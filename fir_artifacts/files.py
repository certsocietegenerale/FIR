import mimetypes
import os
import zipfile
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper

from incidents.models import Incident
from fir_artifacts import Hash
from fir_artifacts.models import File, Artifact


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
    wrapper = FileWrapper(f.file)
    content_type = mimetypes.guess_type(f.file.name)
    response = HttpResponse(wrapper, content_type=content_type)
    response["Content-Disposition"] = "attachment; filename=%s" % (f.getfilename())
    response["Content-Length"] = os.path.getsize(str(f.file.file))
    return response


def do_download_archive(request, object_id):
    obj = get_object_or_404(Incident, pk=object_id)
    temp = BytesIO()
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archive:
        media_root = settings.MEDIA_ROOT
        for file in obj.file_set.all():
            path = os.path.join(media_root, file.file.path)
            archive.write(path, os.path.basename(path))
    file_size = temp.tell()
    temp.seek(0)
    wrapper = FileWrapper(temp)

    response = HttpResponse(wrapper, content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=archive_incident_%s.zip" % (
        object_id,
    )
    response["Content-Length"] = file_size
    return response
