# Tractive Minimal Web Viewer

A minimal web application with a dev container setup for VS Code. The app presents a login page for a Tractive account (email + password), authenticates via the unofficial Tractive API client, and displays available data from trackers.

## Screenshots

### Login Page
![Login Page](https://github.com/user-attachments/assets/5370e477-a801-45ff-8670-b8c0eebd4d62)

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/fea879f3-c7c4-4b62-90ca-444a190b0f0b)

## Quick Start

### VS Code Dev Container (Recommended)

1. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Clone this repository
3. Open the repository in VS Code
4. When prompted, click "Reopen in Container" (or press F1 and select "Dev Containers: Reopen in Container")
5. Wait for the container to build and dependencies to install
6. Run the development server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```
7. Open http://localhost:8080 in your browser

### Local Development (Without Dev Container)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Open in browser
open http://localhost:8080
```

## Features

- **Simple Login**: Email and password authentication via Tractive API
- **Account Summary**: Masked email and last refresh time
- **Trackers List**: View all trackers with battery, charging status, and basic info
- **Hardware Info**: Battery level, firmware, model, capabilities for selected tracker
- **Latest Position**: Current location with coordinates, speed, accuracy, altitude
- **Position History**: Recent tracking history (last 2 hours, sample of 10 points)
- **Geofences**: List of configured geofences (circles and polygons)
- **Live Tracking**: Current state and toggle functionality
- **Raw Data**: JSON endpoints for all data types for inspection
- **Session Management**: Server-side sessions with 20-minute timeout
- **Security**: No password storage, redacted logs, CSRF protection

## Architecture

### Tech Stack
- **Backend**: Python 3.12 + FastAPI + uvicorn
- **Templates**: Jinja2 with semantic HTML
- **Styling**: Minimal CSS, no JavaScript frameworks
- **Authentication**: aiotractive client for Tractive API
- **Sessions**: Signed cookies with server-side storage
- **Development**: VS Code Dev Container

### File Structure
```
.devcontainer/
└── devcontainer.json    # VS Code dev container configuration
app/
├── main.py              # FastAPI application with routes
├── tractive_client.py   # Tractive API wrapper
├── templates/
│   ├── base.html       # Base template with header/footer
│   ├── login.html      # Login form
│   └── dashboard.html  # Main data display
└── static/
    └── styles.css      # Minimal CSS styling
requirements.txt        # Python dependencies
```

## API Endpoints

### Web Pages
- `GET /` - Redirect to login or dashboard based on auth status
- `GET /login` - Login form
- `POST /login` - Handle authentication
- `POST /logout` - Clear session and redirect
- `GET /dashboard` - Main data display page

### JSON APIs  
- `GET /data/json/trackers` - Raw tracker list
- `GET /data/json/hw_info?tracker_id=X` - Hardware information
- `GET /data/json/latest?tracker_id=X` - Latest position
- `GET /data/json/history?tracker_id=X` - Position history
- `GET /data/json/geofences?tracker_id=X` - Geofences list

### Utility
- `GET /healthz` - Health check endpoint
- `POST /toggle-live/{tracker_id}` - Toggle live tracking

## Configuration

### Environment Variables
- `SECRET_KEY` - Session encryption key (auto-generated if not set)
- `PORT` - Server port (default: 8080)
- `LOG_LEVEL` - Logging level (default: INFO)

### Security Features
- Server-side session storage with signed cookies
- 20-minute session timeout on inactivity
- Password never stored or logged
- Secrets redacted from logs
- Basic CSRF protection on forms

## Usage

1. Open the project in VS Code with the Dev Container
2. Start the development server: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`
3. Open http://localhost:8080
4. Enter your Tractive email and password
5. View your trackers and their data
6. Use dropdown to switch between trackers
7. Click "View JSON" links to inspect raw API responses
8. Use "Refresh Data" to reload information

## Limitations

- Uses unofficial Tractive API (may break if endpoints change)
- Limited to read-only operations (view data only)
- No map integration (coordinates only)
- No real-time updates (manual refresh required)
- Session restoration requires re-authentication
- Basic error handling for API failures

## Disclaimer

This application uses an unofficial Tractive API and may break if endpoints change. Use at your own risk. This is not affiliated with or endorsed by Tractive.