# Light Tower - WIP!

A Python/Flask approach to batch multiple http links for lighthouse reports.

Thanks to adamcupial for the great [Lighthouse implementation in Python](https://github.com/adamcupial/lighthouse-python).

**Notice:** This is a work in progress done fast in some hours, so the code is ugly as hell!

## Starting

To run Lighthouse here, you will need npm installed and also npm lighthouse package installed:

```bash
$ npm install -g lighthouse
```

To install the server, run the install script. (If needed, change the file to `chmod 777`.)

```bash
$ ./install.sh
```

And after everything installed, run the server with the run script

```bash
$ ./run.sh
```

## Using

With the server up, access http://localhost:5000 to see the form.
Fill the form and click submit. The report is done async, so there is a progress in the console, but the user will have to refresh the results page (http://localhost:5000/results) to see if the process is done or not.