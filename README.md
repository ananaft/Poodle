# Poodle

## Pythonic Moodle e-assessment

Poodle is a tool for managing exams within the Moodle e-learning platform. Its
goals are to accelerate and streamline the creation and management of exams and
exam questions.

Instead of working inside Moodle's slow web-based UI, Poodle provides a database
which can be stored locally or on a server combined with its own graphical user
interface. It is aimed at those who frequently use Moodle for large exams with
partially changing question pools and power users who wish to potentially
automate aspects of exam creation and management. The current version only runs
under Ubuntu Linux.

Poodle's key features are as follows:

* Create, edit, and overview questions and exams within a fast GUI
* Create XML files for export of questions into Moodle
* Evaluate exams using Moodle results
* Import questions in bulk with JSON files

Poodle was created and is maintained by Lukas Hötttges. It was enriched by ideas
and suggestions from Marian Krawietz at University of Potsdam.

## How to install

* Install [MongoDB Community
Edition](https://www.mongodb.com/docs/manual/administration/install-on-linux/#std-label-install-mdb-community-edition-linux)
in accordance with your operating system. It is utilized as the backend for
Poodle's database.
* Download this repository and move it to your desired location.
* Make launch.sh executable with `chmod +x /PATH/TO/launch.sh` .
* OPTIONAL: Create a symbolic link for more convenience with `sudo ln -s
  /PATH/TO/launch.sh /usr/local/bin/poodle` .
* You can now execute `launch.sh` directly or with `poodle -l <DB NAME>` if you
  followed the previous step.

## Documentation

A full documentation of Poodle can be found
[here](https://ananaft.github.io/poodle-docs/).


## Known issues (Work in progress)


## Planned features (Work in progress)
