## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).
Make sur the following line is included in the `urlpatterns` variable in `fir/urls.py`:

```
url(r'^todos/', include('fir_todos.urls', namespace='todos')),
```

The line should already be there if you've copied the `fir/urls.py.sample` to `fir/urls.py`.


## Usage

Using the `fir_todos` plugin is pretty straightforward.

* To **create** a task, open an incident and click `Add`, then `Todo`. Specify an action to be done, and an accountable party (you may select the "CERT" business line for tasks atrributed to you). To save the changes, click on the `+` sign at the end of the line.

* **Remove** a task by clicking on the cross sign on the corresponding line.

* **Mark a task as done** by clicking on the tick icon next to the action name.

**Warning:** Tasks cannot be edited.

Todo lists will show up in two places: on the incident page, and on the *Dashboard* page, under the *Tasks* tab. Todos appearing on the dashboard are those attributed to the `CERT` business line.


## Development

Everything you need to tweak the plugin is in the `fir_todos` directory: static files (JavaScript & CSS), templates, and actions (in `views.py`) Creating a function in `views.py` for editing tasks would be interesting. :wink: :wink:





