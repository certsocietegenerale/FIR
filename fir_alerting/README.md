## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

You should also make sure to configure your FIR instance so that it is able to send emails (see `EMAIL_HOST`, `EMAIL_PORT` and `REPLY_TO` in the configuration file).

## Usage

This plugin adds two buttons in the action bar, on the incident details page:

* Alert
* Takedown

Both buttons, when clicked, open a modal form that you can use to send emails directly from the interface.

The email form is pre-filled with templates, which you can define from the FIR admin panel:

* **Recipient templates:** this defines all the upper part of the email form: the `from`, `to`, `cc` and `bcc`. You can link it to a business line if you want. When trying to find a template, FIR will look for the most specific template. The `type` field can have two values: `alerting` or `takedown`, in order to be linked with either of these two buttons.
* **Category templates:** this defines the email subject and body for a specific incident category. The field `type` is identical to the one used on Recipient templates. You can use django templating language to create your templates, and use any custom template tag. The following variables are available by default in the context:
  * `subject`: name of the incident
  * `bl`: name of concerned business line
  * `artifacts`: dictionary of artifacts

You should define your recipient and category templates by connecting to FIR admin and adding objects to the "Recipient templates" and "Category templates" tables.
