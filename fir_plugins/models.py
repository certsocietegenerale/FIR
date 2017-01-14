from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from fir_plugins.managers import LinkableManager


def get_plural(model):
    if issubclass(model, models.base.Model):
        model = model.__name__
    return model.lower() + 's'


def get_singular(model):
    if issubclass(model, models.base.Model):
        model = model.__name__
    return model.lower()


class LinkedModelDoesNotExist(Exception):
        pass


class OneLinkableModel(models.Model):

    LinkedModelDoesNotExist = LinkedModelDoesNotExist

    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def get_related(self):
        return self.content_object

    def set_related(self, related):
        self.content_object = related

    class Meta:
        abstract = True


class ManyLinkableModel(models.Model):
    """
    Abstract base model to handle links to other models
    """

    LinkedModelDoesNotExist = LinkedModelDoesNotExist

    @property
    def relations(self):
        if hasattr(self, "_relation_manager") \
                and self._relation_manager is not None:
            return self._relation_manager
        self._relation_manager = LinkableManager(self)
        return self._relation_manager

    def relations_for_user(self, user):
        if user is None:
            return self.relations
        return LinkableManager(self, user=user)

    @classmethod
    def link_to(cls, linked_model, link_name=None, verbose_name=None, verbose_name_plural=None):
        return create_link(cls, linked_model)

    class Meta:
        abstract = True


def create_link(linkable_model, linked_model, linkable_link_name=None, verbose_name=None, verbose_name_plural=None):

    class LinkedModel(object):
        def __init__(self, model, link_name=None, verbose_name=None, verbose_name_plural=None, reverse_link_name=None):
            self.model = model
            self.link_name = link_name
            self.reverse_link_name = reverse_link_name
            self.verbose_name = verbose_name
            self.verbose_name_plural = verbose_name_plural

    if issubclass(linkable_model, ManyLinkableModel):
        get_link_name = get_plural
    elif issubclass(linkable_model, OneLinkableModel):
        get_link_name = get_singular

    if linkable_link_name is None:
        linkable_link_name = get_link_name(linked_model)
    if verbose_name is None:
        verbose_name = linked_model._meta.verbose_name
    if verbose_name_plural is None:
        verbose_name_plural = linked_model._meta.verbose_name_plural
    linked_link_name = get_plural(linkable_model)

    if issubclass(linkable_model, ManyLinkableModel):
        field = models.ManyToManyField(linkable_model, related_name=linkable_link_name)
        setattr(linked_model, linked_link_name, field)
        field.contribute_to_class(linked_model, linked_link_name)

    elif issubclass(linkable_model, OneLinkableModel):
        linked_link_name = get_singular(linkable_model)+"_set"
        field = GenericRelation(linkable_model, related_query_name=linkable_link_name)
        setattr(linked_model, linked_link_name, field)
        field.contribute_to_class(linked_model, linked_link_name)
        setattr(linkable_model, linkable_link_name, property(
            fget=lambda x: linkable_model.get_related(x),
            fset=lambda x, y: linkable_model.set_related(x, y)))

    if not hasattr(linkable_model, "_LINKS") or linkable_model._LINKS is None:
        setattr(linkable_model, "_LINKS", dict())
    linkable_model._LINKS[linkable_link_name] = LinkedModel(
                                linked_model, link_name=linkable_link_name,
                                verbose_name=verbose_name,
                                verbose_name_plural=verbose_name_plural,
                                reverse_link_name=linked_link_name)
    return linkable_model


def link_to(linkable_model, link_name=None, verbose_name=None, verbose_name_plural=None):
    def model_linker(cls):
        create_link(linkable_model, cls)
        return cls
    return model_linker
