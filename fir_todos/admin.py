from django.contrib import admin

from fir_todos.models import TodoItem, TodoListTemplate

admin.site.register(TodoItem)
admin.site.register(TodoListTemplate)
