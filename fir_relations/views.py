from json import dumps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from fir_relations.models import Relation
from incidents.views import is_incident_handler


@login_required
@user_passes_test(is_incident_handler)
def relations(request, content_type, object_id):
    references = Relation.objects.filter(src_content_type=content_type,
                                         src_object_id=object_id,
                                         active=True).as_template_objects(relation_type='target')
    referenced_by = Relation.objects.filter(tgt_content_type=content_type,
                                            tgt_object_id=object_id,
                                            active=True).as_template_objects(relation_type='source')
    return render(request, "fir_relations/relations_sidebar.html",
                  {'references': references, 'referenced_by': referenced_by})


@login_required
@user_passes_test(is_incident_handler)
def remove_relation(request, relation_id):
    if request.method == "POST":
        relation = get_object_or_404(Relation, pk=relation_id)
        relation.active = False
        relation.save()
        return HttpResponse(dumps({'status': 'success'}), content_type="application/json")
