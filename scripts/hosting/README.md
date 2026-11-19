# MilesWeb Passenger deployment

Production application root: /home/dnatechy/book.kallah.in
Keep the existing cPanel-generated .htaccess and Python 3.10 Passenger venv.
Only reviewed changes are promoted from prePublish to Publish.
Hosting checkout must stay on Publish.

When deploying approved changes, run from hosting:

    cd /home/dnatechy/book.kallah.in
    git switch Publish
    git pull --ff-only origin Publish

Then install requirements in the existing Python virtualenv, if they changed, and
restart Passenger via the hosting panel or its configured restart mechanism.
Never store .env, user data, database dumps or credentials in this Git repository.
