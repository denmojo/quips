# smash
a bash.org clone built with Flask
This version was forked by denmojo. It is run locally using SQLite.

## Technologies
- python3
- Flask
- SQLite3
- SQLAlchemy

## Functionalities
- Quote database
- Tags for grouping and classifying quotes
- Moderation queue, admin approval required for adding new quotes
- Pagination
- Ratings

## How to run
This program is designed to be easy to deploy via Heroku. It can also run locally.

First, you have to edit the config file (`config.json`). `APPNAME` is the name that will be displayed in the title bar in the browser, while `APPBRAND` is the name that will be displayed in the navbar on every page.

`SECRETKEY` will be used to encrypt and sign session cookies, so it needs to be a cryptographically-secure random string. `ADMINSECRET` will be used to elevate privileges to allow approving and deleting new quotes. There are no user accounts since there are no user-specific functionalities.

`MOTD` will be displayed on the index page.

`APPNAME` and `APPBRAND` will be loaded from the environment if they're left empty in the config.

Smash uses SQLite. Before you start, you need to set `DATABASE_URL` environment variable to a valid URL leading to your database. If you install the Heroku plugin, it will be done automatically for you - you only need to do this manually if you want to run Smash locally. The `DATABASE_URL` will take the form: `sqlite:////path/to/dbfile.db`.

After basic config is done, run this to start the development server:

```
python run.py
```

The program looks for `HEROKU` in the environment; if that variable is equal to 1, it interprets this as a sign that it's running in a production environment and starts in the externally visible mode with debug turned off. It also needs the `PORT` environment variable to have some sensible value; this is configured automatically when deploying on heroku.

The first time it's started it will create the local database and all required tables, as specified by models. After that it's ready to be used.

All logging is done by printing to stdout - heroku adds that to the app logs visible in the dashboard.

## Running under gunicorn
To productionalize this app, set up nginx or other upstream proxy route to this app under gunicorn wsgi. To run using gunicorn, simply do: 

`gunicorn --bind 0.0.0.0:5000 wsgi:app`

## Screenshots
![index](http://i.imgur.com/VA4NGw4.png)

![quotes](http://i.imgur.com/rlyz1Wa.png)

![tags](http://i.imgur.com/1tMgKkF.png)

![adding a new quote](http://i.imgur.com/BRMsBrU.png)
