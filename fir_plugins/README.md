## Install

This is a mandatory plugin, shipped with FIR. Therefore, it is installed by default.

## Usage

This plugin does not direclty offer any user interraction and is only useful for FIR developpers.

## Development

This plugins provides the `plugin_point` template tag that allows developers to specify a point in the main jinja2 templates where plugins can add content to an existing HTML page.

This is how you define a `plugin_point`:

```
{% plugin_point "dashboard_tab" %}
```

`dashboard_tab` is the name defined for this specific plugin point. For each plugin point defined in the codebase, any plugin can insert a specific template by creating a file matching that name in its directory.

Let's illustrate this with our previous example. The plugin point `dashboard_tab` allows any plugin to add a tab on the dashboard. This is used by the `fir_todos` plugin, with the file `fir_todos/template/fir_todos/plugins/dashboard_tab.html`.

When writing your plugin templates, you can use any variable that is available in the context of the plugin point.
