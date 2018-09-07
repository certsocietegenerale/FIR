## Install
Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

| FIR plugin requirements   |                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------- |
| fir_celery                | [[link]](https://github.com/certsocietegenerale/FIR/tree/master/fir_celery)               |
| fir_artifacts_enrichement | [[link]](https://github.com/certsocietegenerale/FIR/tree/master/fir_artifacts_enrichment) |

You should also make sure to configure your FIR instance so that it is able to send emails (see `EMAIL_HOST`, `EMAIL_PORT` and `REPLY_TO` in the configuration file).


## Usage

The `fir_abuse` plugin adds a **context menu** to be displayed when you right click on an artifact link on the incident details page.

Thanks to a **visual indicator** this context menu offers a feedback on the **enrichement task** fired in the background upon **each artifact creation** (provided by the two required plugins).

The enrichement task consists mainly in a **search** for an **abuse contact**. [[more info]](https://github.com/certsocietegenerale/FIR/tree/master/fir_artifacts_enrichment)

Clicking on **Send Abuse** in the context menu, opens a _Send Email Abuse_ modal form.

The form comes pre-filled with data from templates and contact info, which you can define from the FIR admin panel:

* __Abuse Templates__: `name`, `type`, `body`, `subject` and `incident_category` are the five attributes that define an abuse template. The abuse email's _subject_ and _body_ for a specific incident category are filled thanks to these templates. When trying to find a template, FIR will look for the most specific one. The following variables are available by default in the context:
  * subject: name of the incident
  * bls: name of concerned business line
  * artifacts: dictionary of artifacts
  * incident_id: incident id
  * incident_category: category's name
  * artifact: artifact value
  * enrichment: enrichment raw content
  
* __Abuse Contact__: is a **_qualified contact information_** that helps define the upper part of the email form: `to`, `cc` and `bcc`. Each contact can be specific to an `incident_category` and/or a `type` of artifact. FIR will choose the most specific abuse contact for the `name` determined by the **enrichment task**.

If an __Abuse Contact__ exists it's always used to fill the upper part of the form. In this case, the `to` field will be green. Otherwise it's the __Email__ found through the enrichment process (and the field will be red).

> The form also contain an __Enrichment tab__ providing the `raw` result of the enrichment task.

You should define your __Abuse Templates__ and qualified __Abuse Contact__ by connecting to FIR admin and adding objects to the "Abuse templates" and "Abuse contact" tables.

### TODO
Add the possibility to save the abuse email found through the enrichment task to the Abuse contact base
