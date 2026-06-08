# Smart City Parking System - Admin Features

## ✅ Features Added

### 1. **Admin Login Page** (`/admin`)
- Modern login interface at `http://localhost:8000/admin`
- Demo credentials:
  - **Username:** `admin`
  - **Password:** `admin123`
- JWT token-based authentication
- "Remember me" functionality
- Responsive design with dark theme

### 2. **Admin Dashboard** (`/admin-dashboard`)
- Accessible only after login at `http://localhost:8000/admin-dashboard`
- Full pagination support for parking events
- Configurable items per page (10, 20, 50, 100)
- Smart pagination buttons with navigation
- Real-time event management

### 3. **Pagination for Recent Parking Events**
- **Public Dashboard:** Shows 10 events per page with pagination controls
- **Admin Dashboard:** Shows configurable events per page
- API endpoint updated: `/api/events?page=1&per_page=10`
- Response includes:
  - `items`: Array of parking events
  - `total`: Total number of events
  - `page`: Current page number
  - `per_page`: Items per page
  - `total_pages`: Total number of pages

### 4. **Authentication Endpoint**
- **POST** `/api/auth/login`
- Request body:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- Returns JWT token for authenticated access

### 5. **Admin Button in Header**
- Added "🔐 Admin" button to main dashboard
- Quick access to admin login page

## 🚀 How to Use

### Access Admin Login
1. Click the "🔐 Admin" button in the header of the main dashboard
2. Or navigate directly to `http://localhost:8000/admin`

### Login
- Username: `admin`
- Password: `admin123`
- Optionally check "Remember me" to save username

### Admin Dashboard
- View all parking events with pagination
- Change items per page (10, 20, 50, 100)
- Navigate between pages using:
  - Previous/Next buttons
  - Direct page number buttons
  - First/Last page shortcuts

### Public Dashboard Pagination
- Recent Parking Events table now shows 10 events per page
- Use pagination controls at the bottom of the table to navigate
- Shows "Showing X-Y of Z events" indicator

## 📋 Event Details Displayed
Each event row shows:
- **Vehicle Number:** License plate (e.g., KA-86-ID-3918)
- **Parking Lot:** Which lot the vehicle is parked in
- **Space Number:** Specific parking space (e.g., A1, F10)
- **Entry Time:** Date and time of arrival
- **Exit Time:** Date and time of departure (or "Still Parked")
- **Duration:** Total parking hours (with ⚠️ if overstay)
- **Allowed Duration:** Maximum allowed hours (Admin only)

## 🔐 Security Notes
- Default credentials are for demo purposes
- Change `SECRET_KEY` in `main.py` for production
- Update `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `main.py`
- Use environment variables for sensitive credentials

## 📦 New Dependencies
- **PyJWT:** JWT token generation and verification

## 🗂️ Files Created/Modified
- ✅ `static/admin.html` - Admin login page
- ✅ `static/admin-dashboard.html` - Admin dashboard with pagination
- ✅ `main.py` - Added auth endpoints and pagination logic
- ✅ `static/script.js` - Updated event loading with pagination
- ✅ `static/index.html` - Added admin button
- ✅ `requirements.txt` - Added PyJWT

## 🧪 Testing
1. Start the server: `py main.py`
2. Open `http://localhost:8000` - Main dashboard
3. Click "🔐 Admin" button or go to `/admin`
4. Login with demo credentials
5. Browse events with pagination in admin dashboard
6. Return to main dashboard to see pagination in public view
