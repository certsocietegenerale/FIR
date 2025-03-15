from fir_todos.api import TodoSerializer


hooks = {
    "incident_fields": [
        (
            "todoitem_set",  #  name of the new field
            None,
            TodoSerializer(
                many=True, read_only=True
            ),  # Serializer corresponding to the new field
            None,
        ),
    ],
}
