$ErrorActionPreference = "Stop"
python -m pip install -r requirements-dev.txt
$env:BOOK_SITE_URL = "http://127.0.0.1:5000"
python -m flask --app "app:create_app" run --debug
