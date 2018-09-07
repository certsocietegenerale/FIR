from django.db.models.manager import BaseManager
from fir_plugins.querysets import QuerySetSequence


class LinkableManager(BaseManager):
    def __init__(self, instance, user=None, permission='incidents.view_incidents'):
        self.linkable = instance
        self.user = user
        self.permission = permission

    def get_querysets(self, linked_type=None):
        qss = list()
        if not linked_type:
            for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
                if hasattr(self.linkable, link_name):
                    if hasattr(linked_model.model, 'authorization') and self.user is not None:
                        qss.append(
                            linked_model.model.authorization.for_user(self.user, self.permission).filter(
                                **{linked_model.reverse_link_name: self.linkable.pk}))
                    else:
                        qss.append(getattr(self.linkable, link_name).all())
        else:
            if not isinstance(linked_type, (list, tuple)):
                linked_type = [linked_type,]
            for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
                if linked_type.count(linked_model.model) > 0:
                    if hasattr(linked_model.model, 'authorization') and self.user is not None:
                        qss.append(
                            linked_model.model.authorization.for_user(self.user, self.permission).filter(
                                **{linked_model.reverse_link_name: self.linkable.pk}))
                    else:
                        qss.append(getattr(self.linkable, link_name).all())
        return QuerySetSequence(*qss)

    def all(self, linked_type=None):
        return self.get_querysets(linked_type=linked_type)

    def group(self):
        result = dict()

        class Group(object):
            def __init__(self, linked, objects):
                self.model = linked
                self.objects = objects

        for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
            if hasattr(self.linkable, link_name):
                if hasattr(linked_model.model, 'authorization') and self.user is not None:
                    objects = linked_model.model.authorization.for_user(self.user, self.permission).filter(
                        **{linked_model.reverse_link_name: self.linkable.pk})
                else:
                    objects = getattr(self.linkable, link_name).all()
                result[link_name] = Group(linked_model, objects)
        return result

    def count(self, linked_type=None):
        return self.get_querysets(linked_type=linked_type).count()

    def order_by(self, *field_names, **kwargs):
        linked_type = kwargs.pop('linked_type', None)
        return self.get_querysets(linked_type=linked_type).order_by(*field_names)

    def filter(self, *args, **kwargs):
        linked_type = kwargs.pop('linked_type', None)
        return self.get_querysets(linked_type=linked_type).filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        linked_type = kwargs.pop('linked_type', None)
        return self.get_querysets(linked_type=linked_type).exclude(*args, **kwargs)

    def exists(self):
        return self.get_querysets().exists()

    def add(self, *objs):
        objs = list(objs)

        for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
            for instance in objs:
                if isinstance(instance, linked_model.model):
                    getattr(self.linkable, link_name).add(instance)
                    objs.remove(instance)
                    if len(objs) == 0:
                        return self.linkable
        if len(objs) > 0:
            raise self.linkable.LinkedModelDoesNotExist()
        return self.linkable

    def remove(self, *objs, **kwargs):
        objs = list(objs)

        for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
            for instance in objs:
                if isinstance(instance, linked_model.model):
                    getattr(self.linkable, link_name).remove(instance, **kwargs)
                    objs.remove(instance)
                    if len(objs) == 0:
                        return self.linkable
        if len(objs) > 0:
            raise self.linkable.LinkedModelDoesNotExist()
        return self.linkable

    def clear(self, **kwargs):
        for link_name in getattr(self.linkable, "_LINKS", dict()).keys():
            getattr(self.linkable, link_name).clear(**kwargs)
        return self.linkable

    def get_or_create(self, **kwargs):
        linked_type = kwargs.pop("linked_type", None)
        assert linked_type, 'get_or_create() must be passed the linked model type'
        assert len(kwargs), 'get_or_create() must be passed at least one keyword argument'
        for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
            if linked_model.model == linked_type:
                return getattr(self.linkable, link_name).get_or_create(**kwargs)
        raise self.linkable.LinkedModelDoesNotExist()

    def update_or_create(self, **kwargs):
        linked_type = kwargs.pop("linked_type", None)
        assert linked_type, 'get_or_create() must be passed the linked model type'
        assert len(kwargs), 'get_or_create() must be passed at least one keyword argument'
        for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
            if linked_model.model == linked_type:
                return getattr(self.linkable, link_name).update_or_create(**kwargs)
        raise self.linkable.LinkedModelDoesNotExist()

    def create(self, **kwargs):
        linked_type = kwargs.pop("linked_type", None)
        assert linked_type, 'get_or_create() must be passed the linked model type'
        assert len(kwargs), 'get_or_create() must be passed at least one keyword argument'
        for link_name, linked_model in getattr(self.linkable, "_LINKS", dict()).items():
            if linked_model.model == linked_type:
                return getattr(self.linkable, link_name).create(**kwargs)
        raise self.linkable.LinkedModelDoesNotExist()
