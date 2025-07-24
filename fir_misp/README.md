# fir_misp

This plugin leverages the [MISP ](https://www.misp-project.org/) Threat Intelligence platform in order to enrich incidents. When opening an incident, a "MISP" tab will display all known observables and indicators matching your incident's artifacts, as well as related events.

You can also send your artifacts to MISP directly from FIR.

## Features

- Push FIR artifacts to MISP.
- Display data from MISP into FIR cases. (automatic search)

## Requirements

- Python 3.7+
- `pymisp` library (`pip install pymisp`)
- Access to a running MISP instance with a valid API key

## Install

First, follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

Then, each user needs to set his MISP API key and the location of the MISP instance in his profile page (by clicking on his username).
Alternatively, an administrator you can also set up the API key and location globally, by defining the settings `MISP_URL` and `MISP_APIKEY` in FIR config.

## User manual

At the bottom of the ticket details page, you can find a "MISP" tab. Here, you can find information about the ticket artifacts that are attached to a MISP event.

<img width="1911" height="456" alt="qqOCmLPfxo8k31dL-image" src="https://github.com/user-attachments/assets/95b5a7c5-1a69-451a-b6ae-9002fc89a38b" />

Here you can find the details about MISP related events (MISP event with fir-incident & fir-<incident_id> tags), and MISP observables, the tags attached & description. 

/!\ If an artifact is related to several misp event, only the most recent one is displayed.

On the MISP tab, if you see the message "No intelligence available for this incident. Please check your configuration settings", wait : it can be because the ticket has many artifacts attached and the MISP search is still running. If the message persists, ask a fir admin to configure a MISP api key for you :
<img width="982" height="159" alt="yCPGmMmGOYyRQmOs-image" src="https://github.com/user-attachments/assets/974bff73-c2e5-40e6-9c99-068da0fd1899" />

These buttons redirect you directly to the right MISP event :
<img width="1884" height="574" alt="tWXfBAiFqoQEQ2Bn-image" src="https://github.com/user-attachments/assets/e3d291e2-e11d-48ec-96e7-e03915d51b8b" />

The "unknown observable" list allows you to visualize the fir observable that are unknown in MISP : 
<img width="1777" height="258" alt="Os1ozJ9xxbtm4Dwo-image" src="https://github.com/user-attachments/assets/be374091-3486-44e3-acd2-bd82cba16f46" />

At the bottom of the list, you have a button to send new artifacts / add tags to MISP :

<img width="308" height="85" alt="image" src="https://github.com/user-attachments/assets/b153fc2e-4453-4936-b242-822d068a432d" />

When you hit this button, you see a first panel containing the misp events related to your fir case : 
<img width="1058" height="344" alt="bKjFmp9Pt1p2l6R3-image" src="https://github.com/user-attachments/assets/e6899ea2-11c7-44b4-9d31-283e56d535da" />

Here, you can check the misp event you want to link to the observables.
If no event is checked, it will create a new event, with the tags fir-incident, and fir-< your case id >

Under this panel, you have the observables panel, where you can select all the observables you want to add.
You can also attach tags to those observables, either if the observable is newly sent to misp or if it does already exist. (you can't remove tags that already exists on misp side, if the observable is already linked to the misp event)

To add a tag, click on "+" and type the tags you want to add, and type enter
<img width="1549" height="201" alt="9aVnrQJwSB0dxGgs-image" src="https://github.com/user-attachments/assets/43e90267-d725-4289-a3ec-7677f1a6be28" />

For example, here I will add the tag "test" when I will send the form : 
<img width="1324" height="140" alt="00ZYQnEXzeDFoYnP-image" src="https://github.com/user-attachments/assets/6fee448d-dcd9-48c8-b8db-8933b9c990ae" />

If you want to correct the tag you just typed, just hover the tag and click on the garbage can : 
<img width="1354" height="152" alt="NProOL7lt9qftWDk-image" src="https://github.com/user-attachments/assets/b3044b26-9233-4ceb-ad90-1ae2bd2f119e" />

This button shows you some tags suggestions : 
<img width="1336" height="169" alt="G9r4P2cZxOLGjKNF-image" src="https://github.com/user-attachments/assets/bb9da045-5dda-44bc-8f16-4636de4d1ec9" />

Just click on a suggestion to add it to the tags to attach to the observable : 
<img width="1409" height="180" alt="p0BA6uJ1f1huJHqN-image" src="https://github.com/user-attachments/assets/fecd6a48-2a7b-4028-b542-81dfb7a73861" />

At the end of the form, you have a field where you can add tags who will be added to all observables send to misp : 
<img width="1138" height="60" alt="aW3Ayq7okXgSXIAo-image" src="https://github.com/user-attachments/assets/a1f1a4c3-c243-46cf-8558-94fc96806ca1" />

When you are happy with the form content, you can sent it by clicking the "Send it!" button : 

<img width="190" height="144" alt="Q3NmjYtTy3rPNJap-image" src="https://github.com/user-attachments/assets/b279d1e2-f2d7-4b94-9f1d-6d1579d874cb" />

/!\ If no observable is checked, nothing will be done, you have to check at least one observable to send data to MISP

## License

This module inherits the FIR license (GNU GPLv3).

