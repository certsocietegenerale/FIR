from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from fir_plugins.links import registry
from incidents.models import Incident, Comments


@python_2_unicode_compatible
class TemplateRelation(object):
    def __init__(self, relation, request, relation_type='target'):
        self.relation = relation
        self.relation_type = relation_type
        self.user = request.user
        if self.relation_type == 'target':
            self.object = relation.target
        else:
            self.object = relation.source
        self._check_permission()

    def _check_permission(self):
        self.can_view = False
        self.can_edit = False
        if hasattr(self.object, 'has_perm'):
            if self.object.has_perm(self.user, 'incidents.view_incidents'):
                self.can_view = True
            else:
                return
        if hasattr(self.relation.source, 'has_perm'):
            if self.relation.source.has_perm(self.user, 'incidents.handle_incidents'):
                self.can_edit = True


    @property
    def url(self):
        return registry.model_links.get(self.object._meta.label, ['', '', None])[1]

    @property
    def id(self):
        return self.object.id

    @property
    def id_text(self):
        template = registry.model_links.get(self.object._meta.label, ['', '', None])[2]
        if not template:
            template = "#{}"
        return template.format(self.object.id)

    @property
    def content_type_id(self):
        if self.relation_type == 'target':
            return self.relation.tgt_content_type_id
        else:
            return self.relation.src_content_type_id

    @property
    def object_type(self):
        if isinstance(self.object, Incident):
            if self.object.is_incident:
                return _('Incident')
            return _('Event')
        return self.object._meta.verbose_name

    def __str__(self):
        return unicode(self.object)


class RelationQuerySet(models.QuerySet):
    def update_relations(self, source_instance, data):
        relations = []
        src_ct = ContentType.objects.get_for_model(source_instance)
        for model, link in registry.model_links.items():
            parser, url, reverse = link
            tgt_ct = None
            for match in parser.finditer(data):
                if match:
                    if tgt_ct is None:
                        try:
                            tgt_ct = ContentType.objects.get_by_natural_key(*model.lower().split('.'))
                        except ContentType.DoesNotExist:
                            continue
                    relation, created = self.get_or_create(
                        src_content_type=src_ct,
                        src_object_id=source_instance.pk,
                        tgt_content_type=tgt_ct,
                        tgt_object_id=match.group(1)
                    )
                    relations.append(relation)
        return relations

    def as_template_objects(self, request, relation_type='target'):
        relations = []
        for relation in self:
            template_relation = TemplateRelation(relation, request, relation_type=relation_type)
            if template_relation.can_view:
                relations.append(template_relation)
        return relations


class Relation(models.Model):
    src_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    src_object_id = models.PositiveIntegerField()
    source = GenericForeignKey('src_content_type', 'src_object_id')
    tgt_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    tgt_object_id = models.PositiveIntegerField()
    target = GenericForeignKey('tgt_content_type', 'tgt_object_id')
    active = models.BooleanField(default=True)

    objects = RelationQuerySet.as_manager()


@receiver(post_save, sender=Incident)
def parse_incident(sender, instance, created, **kwargs):
    Relation.objects.update_relations(instance, instance.description)


@receiver(post_save, sender=Comments)
def parse_comment(sender, instance, created, **kwargs):
    Relation.objects.update_relations(instance.incident, instance.comment)
