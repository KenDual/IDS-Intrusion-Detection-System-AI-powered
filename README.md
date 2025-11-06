# AI-Powered Intrusion Detection System (IDS)

Real-time network intrusion detection system using XGBoost machine learning model.

## Features

- ✅ Real-time packet capture and analysis
- ✅ Multi-class attack detection (DoS Hulk, DDoS, PortScan)
- ✅ Web-based dashboard with live alerts
- ✅ SQLite database for alert storage
- ✅ RESTful API with FastAPI
- ✅ 36 network flow features
- ✅ 98%+ detection accuracy

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **ML Model**: XGBoost
- **Database**: SQLite
- **Packet Capture**: Scapy
- **Frontend**: Jinja2, HTML/CSS/JS
- **Dataset**: CICIDS2017

## Project Structure
```
ids-project/
├── app/           # FastAPI backend
├── ml/            # Machine learning code
├── scripts/       # Attack simulation
├── data/          # Datasets
└── logs/          # Application logs
```

## Installation
```bash
# 1. Clone repo
git clone <repo-url>
cd ids-project

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your settings
```

## Dataset Preparation
```bash
# Download CICIDS2017 dataset
# Place CSV files in data/ folder

# Create cleaned dataset
python ml/prepare_clean_data.py
```

## Training Model
```bash
python ml/train.py
```

## Running Application
```bash
# Start FastAPI server
python app/main.py

# Access dashboard
http://localhost:8000
```

## Attack Simulation
```bash
# Port scan
python scripts/port_scan.py --target 192.168.1.100

# DoS attack
python scripts/dos_sim.py --target 192.168.1.100

# Normal traffic
python scripts/normal_traffic.py
```

## API Endpoints

- `GET /` - Dashboard
- `POST /api/predict` - Predict from CSV/PCAP
- `GET /api/alerts` - List alerts
- `POST /api/monitor/start` - Start monitoring
- `POST /api/monitor/stop` - Stop monitoring
- `WS /ws/alerts` - WebSocket for real-time alerts

## Model Performance

- **Accuracy**: 98.5%
- **Precision**: 97.8%
- **Recall**: 96.9%
- **F1-Score**: 97.3%
- **False Positive Rate**: 1.2%

## Dataset Statistics

- **Total Records**: 2,791,127
- **Classes**: 4 (BENIGN, DoS Hulk, PortScan, DDoS)
- **Features**: 36 network flow features
- **Class Distribution**:
  - BENIGN: 81.44%
  - DoS Hulk: 8.28%
  - PortScan: 5.69%
  - DDoS: 4.59%

## License

MIT License

## Author

KenDual