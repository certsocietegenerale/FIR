# -*- coding: utf-8 -*-
import os
import argparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fir.settings")

import django
django.setup()

# your imports, e.g. Django models
from fir_todos.models import TodoItem, TodoListTemplate


def import_file(filename):
    ''' create a todolistemplate from a file '''
    todos = []
    template = TodoListTemplate(name=filename.split('.')[0])
    template.save()
    for line in open(filename).read().split('\n'):
        todos.append(create_item(line))

    template.todolist = todos
    template.save()
    print "[*] import terminé"


def create_item(line):
    ''' create a todo item '''
    item = TodoItem(description=line)
    item.save()
    return item


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('fichier', help="fichier à importer")
    args = parser.parse_args()

    if os.path.exists(args.fichier) and os.path.isfile(args.fichier):
        import_file(args.fichier)
    else:
        print "le fichier n'existe pas"
