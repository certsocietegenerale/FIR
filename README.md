[![Build Status](https://travis-ci.org/certsocietegenerale/FIR.svg?branch=master)](https://travis-ci.org/certsocietegenerale/FIR)

# What is FIR? Who is it for?

FIR (Fast Incident Response) is an cybersecurity incident management platform designed with agility and speed in mind. It allows for easy creation, tracking, and reporting of cybersecurity incidents.

FIR is for anyone needing to track cybersecurity incidents (CSIRTs, CERTs, SOCs, etc.). It's was tailored to suit our needs and our team's habits, but we put a great deal of effort into making it as generic as possible before releasing it so that other teams around the world may also use it and customize it as they see fit.

![dashboard](https://github.com/certsocietegenerale/FIR/wiki/screenshots/dashboard.png)
![incident details](https://github.com/certsocietegenerale/FIR/wiki/screenshots/incident_details.png)

See the wiki for the [user manual](https://github.com/certsocietegenerale/FIR/wiki/User-Manual) and more screenshots !

# Installation

There are two ways to install FIR. If you want to take it for a test-drive, just follow the instructions for [setting up a development environment](https://github.com/certsocietegenerale/FIR/wiki/Setting-up-a-development-environment) in the Wiki.

If you like it and want to set it up for production, [here's how to do it](https://github.com/certsocietegenerale/FIR/wiki/Installation-on-a-production-environment).

A dockerfile for running a dev-quality FIR setup is also available in [docker/Dockerfile](docker/Dockerfile).

Deploy to [Heroku](https://heroku.com) via fir/heroku_settings.py

# Community

A dedicated users mailing list is available https://groups.google.com/d/forum/fir-users

# Technical specs

FIR is written in Python (but you probably already knew that), using Django 1.9. It uses Bootstrap 3 and some Ajax and d3js to make it pretty. We use it with a MySQL back-end, but feel free to use any other DB adaptor you might want - as long as it's compatible with Django, you shouldn't run into any major issues.

FIR is not greedy performance-wise. It will run smoothly on a Ubuntu 14.04 virtual machine with 1 core, a 40 GB disk and 1 GB RAM.

# Roadmap

* Nested Todos
* REST API
* Mailman
* You name it :)
