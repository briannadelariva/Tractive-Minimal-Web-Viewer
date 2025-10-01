# Tractive Minimal Web Viewer

A minimal, production-ready web application that runs entirely in a Docker container. The app presents a login page for a Tractive account (email + password), authenticates via the unofficial Tractive API client, and displays available data from trackers.

## Screenshots

### Login Page
![Login Page](https://github.com/user-attachments/assets/5370e477-a801-45ff-8670-b8c0eebd4d62)

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/fea879f3-c7c4-4b62-90ca-444a190b0f0b)

## Quick Start

### Docker (Recommended)

```bash
# Build the image
docker build -t tractive-web .

# Run the container
docker run --rm -p 8080:8080 tractive-web

# Open in browser
open http://localhost:8080
```

### Development

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
- **Container**: Docker with multi-stage build

### File Structure
```
app/
├── main.py              # FastAPI application with routes
├── tractive_client.py   # Tractive API wrapper
├── templates/
│   ├── base.html       # Base template with header/footer
│   ├── login.html      # Login form
│   └── dashboard.html  # Main data display
└── static/
    └── styles.css      # Minimal CSS styling
Dockerfile              # Container definition
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
- Non-root user in Docker container

## Usage

1. Start the container: `docker run --rm -p 8080:8080 tractive-web`
2. Open http://localhost:8080
3. Enter your Tractive email and password
4. View your trackers and their data
5. Use dropdown to switch between trackers
6. Click "View JSON" links to inspect raw API responses
7. Use "Refresh Data" to reload information

## Limitations

- Uses unofficial Tractive API (may break if endpoints change)
- Limited to read-only operations (view data only)
- No map integration (coordinates only)
- No real-time updates (manual refresh required)
- Session restoration requires re-authentication
- Basic error handling for API failures

## Disclaimer

This application uses an unofficial Tractive API and may break if endpoints change. Use at your own risk. This is not affiliated with or endorsed by Tractive.