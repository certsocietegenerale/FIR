## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

## Usage

Using the `fir_todos` plugin is pretty straightforward.

* To **create** a task, open an incident and click `Add`, then `Todo`. Specify an action to be done, and an accountable party (you may select the "CERT" business line for tasks atrributed to you). To save the changes, click on the `+` sign at the end of the line.

* **Remove** a task by clicking on the cross sign on the corresponding line.

* **Mark a task as done** by clicking on the tick icon next to the action name.

**Warning:** Tasks cannot be edited.

Todo lists will show up in two places: on the incident page, and on the *Dashboard* page, under the *Tasks* tab. Todos appearing on the dashboard are those attributed to the `CERT` business line.

### Todo Templates

You can use Todo Templates in order to automatically create Todos when there is a new incident. You can create as many templates as you want in the *Admin* panel.

Each template can specify:

* A category
* A detection
* Concerned business lines

The template will be activated for each incident matching all the criteria **that are defined (not null)**.

Note that *Concerned business line* is a little bit special: you only need one business line in order to match the template, and parents are considered. This means that if you create a template with *Concerned business lines* set to *BL1* and *BL2*, the following will be true:

* An incident for *BL1* will match
* An incident for *BL2* will match
* An incident for *BL1* and *BL2* will match
* An incident for *BL1 > Sub BL1* will match

#### Todo Items for your templates

When creating Todo Items for your templates, be aware that the *business line* is optionnal. When this field is not specified, a todo item will be created for each incident *business line* that matched the template.

Example: if you have a template for *BL1* with a Todo item "Do Something" with no *business line* specified, and you create an incident for *BL1 > Sub BL1*, *BL1 > Sub BL2* and *BL2*, you will have the following todos created:

* Do Something (BL1 > Sub BL1)
* Do Something (BL1 > Sub BL2)

## Development

Everything you need to tweak the plugin is in the `fir_todos` directory: static files (JavaScript & CSS), templates, and actions (in `views.py`) Creating a function in `views.py` for editing tasks would be interesting. :wink: :wink:
