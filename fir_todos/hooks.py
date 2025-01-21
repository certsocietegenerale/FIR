try:
    from fir_todos.api import TodoSerializer
except ModuleNotFoundError:
    incident_fields = {}
else:
    incident_fields = [
        (
            "todoitem_set",  #  name of the new field
            None,
            TodoSerializer(
                many=True, read_only=True
            ),  # Serializer corresponding to the new field
            None,
        ),
    ]

hooks = {
    "incident_fields": incident_fields,
}
