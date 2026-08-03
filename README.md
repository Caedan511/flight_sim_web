## Backend Initialization

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure database and admin credentials in `.env`:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=flight_sim_web
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=change-this-password
JWT_SECRET_KEY=change-this-secret
```

Initialize a new database:

```bash
python deploy.py
```

Start the backend:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

