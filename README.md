# Smart City Parking Management System

A comprehensive IoT-based parking management platform that monitors occupancy, tracks vehicle movements, and provides real-time analytics for city parking lots.

## 🎯 Features

- **Real-time Parking Monitoring**: Track parking lot occupancy with IoT sensors
- **Vehicle Tracking**: Record entry/exit events with timestamp logging
- **Smart Analytics**: Get weekly trends and occupancy summaries
- **Alert Management**: Automatic alerts for lot capacity and violations
- **RESTful API**: Complete FastAPI backend with CRUD operations
- **Web Dashboard**: Interactive frontend for visualization and management
- **Database Persistence**: SQLite database for data storage

## 📋 System Architecture

### Backend (FastAPI)
- **Parking Lots Management**: Create, read, update, and delete parking lots
- **Parking Spaces**: Manage individual parking spaces and availability
- **Sensor Events**: Process vehicle entry/exit events
- **Alert System**: Monitor and resolve parking violations
- **Analytics Engine**: Generate occupancy trends and weekly reports

### Database (SQLAlchemy + SQLite)
- **parking_lots**: City parking locations with capacity info
- **parking_spaces**: Individual spaces with status tracking
- **parking_events**: Timestamped vehicle entry/exit records
- **alerts**: System-generated alerts for violations

### Frontend (Static Web App)
- Interactive dashboard with real-time updates
- Parking lot visualization
- Analytics charts and reports
- Alert management interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/parking-management-system.git
   cd parking-management-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

   The application will start at `http://localhost:8000`

### Access Points
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)
- **Web Dashboard**: http://localhost:8000/

## 📦 Dependencies

- **fastapi**: Modern Python web framework for building APIs
- **uvicorn**: ASGI server for FastAPI
- **sqlalchemy**: SQL toolkit and ORM for database management
- **pandas**: Data analysis and manipulation library for analytics

See `requirements.txt` for complete list.

## 🔌 API Endpoints

### Parking Lots
- `POST /lots` - Create a new parking lot
- `GET /lots` - List all parking lots
- `GET /lots/{id}` - Get parking lot details
- `PUT /lots/{id}` - Update parking lot
- `DELETE /lots/{id}` - Delete parking lot

### Parking Spaces
- `GET /spaces` - List spaces with filters

### Vehicle Events
- `POST /events/entry` - Record vehicle entry
- `POST /events/exit` - Record vehicle exit
- `GET /events` - View all parking events

### Alerts
- `POST /alerts` - Create alert
- `GET /alerts` - View all alerts
- `PUT /alerts/{id}/resolve` - Resolve alert

### Analytics
- `GET /analytics/summary` - Dashboard summary
- `GET /analytics/weekly` - Weekly analytics and trends

## 📁 Project Structure

```
parking-management-system/
├── main.py              # FastAPI application and routes
├── database.py          # SQLAlchemy models and setup
├── schemas.py           # Pydantic data validation schemas
├── simulator.py         # Test data generator
├── analytics.py         # Analytics calculations
├── requirements.txt     # Python dependencies
├── static/              # Frontend files
│   ├── index.html       # Dashboard HTML
│   ├── script.js        # Frontend JavaScript
│   └── style.css        # Dashboard styling
└── parking.db          # SQLite database (generated at runtime)
```

## 🔄 Data Flow

1. **IoT Sensors** → Detect vehicle entry/exit
2. **API Endpoints** → Process and store events
3. **Database** → Persist parking lot and event data
4. **Analytics Engine** → Calculate occupancy trends
5. **Web Dashboard** → Display real-time information

## 💾 Database Models

### ParkingLot
- Lot ID, Name, Location
- Total capacity and current occupancy
- Hourly rates

### ParkingSpace
- Space ID, Lot ID
- Occupancy status
- Vehicle type support

### ParkingEvent
- Event ID, Space ID
- Entry/Exit timestamp
- Duration of parking

### Alert
- Alert ID, Type
- Status (Active/Resolved)
- Associated parking lot

## 📊 Analytics Capabilities

- **Occupancy Rates**: Track usage patterns over time
- **Peak Hours**: Identify busiest periods
- **Weekly Trends**: Monitor week-over-week changes
- **Capacity Analysis**: Monitor lot capacity utilization
- **Revenue Potential**: Estimate income based on duration

## 🧪 Testing

The system includes a data simulator that generates 1 week of realistic parking data on startup:

```python
from simulator import seed_data
seed_data()  # Generates test data
```

## 🛠️ Development

### Add New Feature
1. Update database models in `database.py`
2. Create Pydantic schemas in `schemas.py`
3. Add API routes in `main.py`
4. Update frontend in `static/`

### Database Queries
```python
from database import SessionLocal, ParkingLot
db = SessionLocal()
lots = db.query(ParkingLot).all()
```

## 📝 Configuration

Edit `database.py` to change database location:
```python
DATABASE_URL = "sqlite:///parking.db"  # SQLite file path
```

## 🐛 Troubleshooting

**Port 8000 already in use?**
```bash
uvicorn main:app --port 8001
```

**Database corruption?**
Delete `parking.db` and restart the application to regenerate.

**Dependencies not installing?**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 📧 Contact & Support

For questions or issues, please open an issue on GitHub.

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/)
- [RESTful API Best Practices](https://restfulapi.net/)

---

**Happy Parking! 🚗**
