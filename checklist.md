# Checklist Kỹ Thuật - IDS Project (Chi Tiết)

## **PHASE 1: Setup & Chuẩn Bị** ✅ HOÀN THÀNH

### 1.1 Environment Setup
- [x] Cài Python 3.9+ 
- [x] Tạo virtual environment
- [x] Cài đặt dependencies cơ bản:
  - [x] FastAPI, Uvicorn
  - [x] XGBoost, scikit-learn, pandas, numpy
  - [x] Scapy (packet capture)
  - [x] SQLAlchemy (ORM)
  - [x] Jinja2 templates
  - [x] python-multipart (file upload)
  - [x] websockets

### 1.2 Dataset & Research
- [x] Download CICIDS2017 dataset (8 CSV files)
- [x] Tạo script explore dataset (`ml/explore_data.py`)
- [x] Chạy exploration:
  - [x] Phân tích 2.8M records, 79 features
  - [x] Hiểu 15 attack types
  - [x] Phân tích class imbalance (80% BENIGN)
  - [x] Phát hiện infinity values (4,376 values)
  - [x] Phát hiện missing values (0.05%)
- [x] Quyết định strategy:
  - [x] Chọn 4 classes: BENIGN, DoS Hulk, PortScan, DDoS (98.6% data)
  - [x] Giảm từ 79 → 36 features quan trọng
  - [x] Multi-class classification
- [x] Tạo script clean dataset (`ml/prepare_clean_data.py`)
- [x] Xử lý data quality:
  - [x] Filter 4 attack classes (2,791,127 records)
  - [x] Select 36 features
  - [x] Handle infinity values (replace with max finite)
  - [x] Handle missing values (fill with median)
- [x] Tạo clean dataset:
  - [x] File: `data/cleaned_data.csv` (473 MB)
  - [x] Verify: No missing, no infinity
  - [x] Save summary: `data/dataset_summary.txt`

### 1.3 Project Structure
- [x] Tạo cấu trúc thư mục đầy đủ
- [x] Tạo tất cả `__init__.py` files
- [x] Tạo `app/config.py` với configurations
- [x] Tạo `README.md` với project documentation
- [x] Tạo `.gitkeep` cho thư mục trống
- [x] Tạo `verify_structure.py` để kiểm tra
- [x] Verify: Chạy `verify_structure.py` - all ✓

---

## **PHASE 2: Machine Learning** ✅ HOÀN THÀNH

### 2.1 Data Preprocessing
- [x] Load cleaned_data.csv files
- [x] Xử lý missing values
- [x] Xử lý infinity values
- [x] Label encoding cho attack types (BENIGN=0, DoS Hulk=1, PortScan=2, DDoS=3)
- [x] Feature scaling/normalization (StandardScaler)
- [x] Train/val/test split (64/16/20%)
- [x] Xử lý class imbalance (Class weights: BENIGN=1.0, DoS Hulk=9.84, PortScan=14.31, DDoS=17.74)

### 2.2 Feature Engineering
- [x] Feature selection (25 features selected from 36)
- [x] Tạo mapping features từ raw packets → model input
- [x] Document 25 features quan trọng nhất
- [x] Save feature names và selected features

### 2.3 Model Training
- [x] Train XGBoost classifier với GPU acceleration
- [x] Hyperparameter tuning (GridSearchCV, 3-fold CV)
- [x] Best params: max_depth=10, learning_rate=0.1, n_estimators=152
- [x] Save best model (xgboost_model.pkl)
- [x] Save scaler (scaler.pkl)
- [x] Save encoder (label_encoder.pkl)
- [x] Save metadata (model_metadata.json, best_params.json)

### 2.4 Model Evaluation
- [x] Tính metrics: Accuracy=99.95%, Precision=99.95%, Recall=99.95%, F1-score=99.95%
- [x] Confusion matrix visualization
- [x] Per-class performance (all classes >99%)
- [x] Training history plots
- [x] Document kết quả (training_report.txt, training_metrics.json)

---

## **PHASE 3: Database Design** ✅ HOÀN THÀNH

### 3.1 Database Setup
- [x] Tạo database.py (SQLite connection, session factory)
- [x] Setup SessionLocal và Base class
- [x] Implement get_db() dependency cho FastAPI
- [x] Enable foreign key constraints
- [x] Helper functions: init_database(), reset_database(), get_database_info()
- [x] Update app/config.py với database configs

### 3.2 Database Schema
- [x] **Alerts table**: 
  - [x] 8 columns: id, timestamp, source_ip, dest_ip, attack_type, confidence, severity, created_at
  - [x] 6 indexes cho real-time performance (timestamp, source_ip, attack_type + 3 composite)
  - [x] Severity: low/critical (based on confidence >= 0.95)
  - [x] Attack types: DoS Hulk, PortScan, DDoS
- [x] **TrainingLogs table**: 
  - [x] 6 columns: id, model_version, accuracy, f1_score, trained_at, notes
  - [x] Index trên trained_at
- [x] **Whitelist table**: 
  - [x] 4 columns: id, ip_address (unique), description, added_at
  - [x] Index + unique constraint trên ip_address
- [x] **Blacklist table**: 
  - [x] 4 columns: id, ip_address (unique), description, added_at
  - [x] Index + unique constraint trên ip_address
- [x] **SystemConfig table**: 
  - [x] 4 columns: id, key (unique), value, updated_at
  - [x] Index + unique constraint trên key

### 3.3 SQLAlchemy Models
- [x] Tạo Alert model (app/models/alert.py)
- [x] Tạo TrainingLog model (app/models/training_log.py)
- [x] Tạo Whitelist model (app/models/whitelist.py)
- [x] Tạo Blacklist model (app/models/blacklist.py)
- [x] Tạo SystemConfig model (app/models/system_config.py)
- [x] Tất cả models có to_dict() methods
- [x] Tạo app/models/__init__.py để export models

### 3.4 CRUD Operations (25 functions)
- [x] **Alert CRUD** (10 functions):
  - [x] create_alert() - Tạo alert mới
  - [x] get_alert_by_id() - Lấy alert theo ID
  - [x] get_alerts() - Pagination + filters (attack_type, severity, source_ip, date range)
  - [x] get_recent_alerts() - N alerts gần nhất
  - [x] get_alerts_by_ip() - Tất cả alerts từ IP
  - [x] delete_alert() - Xóa alert
  - [x] count_alerts() - Đếm alerts với filters
  - [x] get_alert_statistics() - Thống kê theo thời gian
- [x] **Whitelist CRUD** (4 functions):
  - [x] add_to_whitelist(), remove_from_whitelist()
  - [x] is_whitelisted(), get_all_whitelist()
- [x] **Blacklist CRUD** (4 functions):
  - [x] add_to_blacklist(), remove_from_blacklist()
  - [x] is_blacklisted(), get_all_blacklist()
- [x] **TrainingLog CRUD** (3 functions):
  - [x] create_training_log(), get_latest_training_log()
  - [x] get_all_training_logs()
- [x] **SystemConfig CRUD** (4 functions):
  - [x] set_config(), get_config()
  - [x] get_all_configs(), delete_config()

### 3.5 Database Initialization
- [x] Tạo init_db.py script
- [x] Create all tables automatically
- [x] Insert 15 default system configurations:
  - [x] Monitoring settings (monitoring_enabled, monitoring_interface)
  - [x] Alert settings (alert_threshold=0.95, max_alerts_per_page=50, retention)
  - [x] Model settings (model_version, model_path)
  - [x] Performance settings (batch_prediction_size, prediction_timeout)
  - [x] WebSocket settings (websocket_enabled, max_connections)
  - [x] Security settings (auto_block settings)
  - [x] System settings (system_name, version, admin_email)
- [x] Verify table creation
- [x] Display database info

### 3.6 Database Testing
- [x] test_database_setup.py - Test connection & session
- [x] test_models.py - Test models & table creation
- [x] test_crud.py - Test all 25 CRUD operations
- [x] seed_db.py - Insert sample data (optional, for development)
- [x] All tests PASSED ✓

---

## **PHASE 4: Packet Capture & Feature Extraction**

### 4.1 Packet Sniffer
- [ ] Implement packet capture với Scapy
- [ ] Lọc packets theo protocol (TCP, UDP, ICMP)
- [ ] Extract raw features: IPs, ports, flags, packet size, time
- [ ] Handle exceptions (permission, interface not found)

### 4.2 Flow Generator
- [ ] Tạo flow từ packets (group by 5-tuple: src_ip, dst_ip, src_port, dst_port, protocol)
- [ ] Tính flow statistics: duration, packets/sec, bytes/sec
- [ ] Tính forward/backward packets ratio
- [ ] Tính flags count (SYN, ACK, FIN, RST, PSH, URG)
- [ ] Feature window (VD: 5 giây)

### 4.3 Feature Mapping
- [ ] Map raw packet features → 25 selected CICIDS2017 features
- [ ] Normalize features (dùng scaler.pkl đã save)
- [ ] Validate feature shape trước khi predict

---

## **PHASE 5: Backend API (FastAPI)**

### 5.1 Core APIs
- [ ] **POST /predict**: Upload file CSV/PCAP → predict
- [ ] **GET /alerts**: Lấy danh sách alerts (pagination)
- [ ] **GET /alerts/{id}**: Chi tiết 1 alert
- [ ] **GET /stats**: Thống kê tổng quan
- [ ] **POST /whitelist**: Add IP vào whitelist
- [ ] **DELETE /whitelist/{id}**: Remove IP
- [ ] **GET /model/info**: Thông tin model hiện tại

### 5.2 Real-time Monitoring
- [ ] **POST /monitor/start**: Bật packet capture
- [ ] **POST /monitor/stop**: Tắt monitoring
- [ ] **GET /monitor/status**: Check trạng thái
- [ ] WebSocket endpoint: **/ws/alerts** (push real-time)

### 5.3 Model Management
- [ ] **POST /model/retrain**: Trigger retrain với new data
- [ ] **GET /model/metrics**: Xem performance metrics
- [ ] Load model khi startup
- [ ] Model versioning

### 5.4 Middleware & Security
- [ ] CORS middleware
- [ ] Rate limiting
- [ ] Basic authentication (optional)
- [ ] Error handling global

---

## **PHASE 6: Detection Engine**

### 6.1 Real-time Detection Service
- [ ] Background task sniff packets liên tục
- [ ] Queue packets để xử lý (asyncio.Queue)
- [ ] Extract features từ packets
- [ ] Predict với XGBoost model
- [ ] Check whitelist trước khi alert

### 6.2 Alert System
- [ ] Tạo alert object khi detect attack
- [ ] Lưu alert vào database
- [ ] Push alert qua WebSocket
- [ ] Gán severity level (low/critical based on confidence)
- [ ] Deduplicate alerts (tránh spam cùng 1 IP)

### 6.3 Performance Optimization
- [ ] Batch prediction (nhiều flows cùng lúc)
- [ ] Cache predictions gần đây
- [ ] Limit queue size (avoid memory leak)
- [ ] Monitor latency (< 100ms)

---

## **PHASE 7: Frontend (Jinja2 Templates)**

### 7.1 Layout & Templates
- [ ] **base.html**: Layout chung (navbar, footer)
- [ ] **dashboard.html**: Trang chủ - overview stats
- [ ] **alerts.html**: Danh sách alerts + filter
- [ ] **alert_detail.html**: Chi tiết 1 alert
- [ ] **monitor.html**: Real-time monitoring page
- [ ] **settings.html**: Whitelist/Blacklist management
- [ ] **model.html**: Model info & retrain

### 7.2 Static Assets
- [ ] CSS: Bootstrap hoặc Tailwind
- [ ] JavaScript: 
  - [ ] WebSocket client (connect /ws/alerts)
  - [ ] Chart.js (visualize attack types, timeline)
  - [ ] Real-time notifications
  - [ ] Auto-refresh tables

### 7.3 Dashboard Components
- [ ] Total alerts counter
- [ ] Attack types pie chart
- [ ] Timeline chart (attacks over time)
- [ ] Top attacked IPs table
- [ ] Recent alerts feed
- [ ] System status indicator

### 7.4 Real-time Features
- [ ] WebSocket connection status
- [ ] Live alert notifications (toast/modal)
- [ ] Auto-update alert count
- [ ] Sound/desktop notification (optional)

---

## **PHASE 8: Attack Simulation Scripts**

### 8.1 Port Scan Simulation
- [ ] Script nmap scan ports
- [ ] Configurable target IP/port range

### 8.2 DDoS Simulation
- [ ] Script gửi SYN flood (hping3)
- [ ] Hoặc simple UDP flood (Scapy)

### 8.3 DoS Hulk Simulation
- [ ] Script simulate DoS Hulk attack pattern
- [ ] High volume HTTP GET requests

### 8.4 Normal Traffic Generator
- [ ] Script tạo traffic bình thường (curl, ping)
- [ ] Để test false positive

---

## **PHASE 9: Testing**

### 9.1 Unit Tests
- [ ] Test feature extraction functions
- [ ] Test model prediction
- [ ] Test database CRUD
- [ ] Test API endpoints

### 9.2 Integration Tests
- [ ] Test end-to-end flow: packet → predict → alert → UI
- [ ] Test WebSocket connection
- [ ] Test với attack scripts

### 9.3 Performance Tests
- [ ] Test latency (packet → alert time)
- [ ] Test với high traffic volume
- [ ] Memory leak check
- [ ] False positive rate measurement

---

## **PHASE 10: Documentation & Demo**

### 10.1 Documentation
- [ ] README.md: Setup instructions
- [ ] API documentation (Swagger tự động)
- [ ] Model training guide
- [ ] Feature list document
- [ ] Architecture diagram

### 10.2 Demo Preparation
- [ ] Video demo script
- [ ] Test scenarios:
  - [ ] Scenario 1: Upload file predict
  - [ ] Scenario 2: Real-time port scan detection
  - [ ] Scenario 3: DDoS detection + alert
  - [ ] Scenario 4: Whitelist IP (no alert)
- [ ] Screenshots cho báo cáo

### 10.3 Deployment (Optional)
- [ ] Containerize với Docker
- [ ] Docker Compose setup
- [ ] Deploy lên VPS/cloud (optional)

---

## **PHASE 11: Final Polish**

- [ ] Code cleanup & refactoring
- [ ] Add logging (file + console)
- [ ] Error handling hoàn chỉnh
- [ ] UI/UX improvements
- [ ] Performance tuning
- [ ] Security review (input validation, SQL injection)

---

## **Progress Summary**

### Completed Phases: 3/11
- ✅ **PHASE 1**: Setup & Chuẩn Bị (100%)
- ✅ **PHASE 2**: Machine Learning (100%)
- ✅ **PHASE 3**: Database Design (100%)
- ⏳ **PHASE 4**: Packet Capture & Feature Extraction (0%)
- ⏳ **PHASE 5**: Backend API (0%)
- ⏳ **PHASE 6**: Detection Engine (0%)
- ⏳ **PHASE 7**: Frontend (0%)
- ⏳ **PHASE 8**: Attack Simulation (0%)
- ⏳ **PHASE 9**: Testing (0%)
- ⏳ **PHASE 10**: Documentation & Demo (0%)
- ⏳ **PHASE 11**: Final Polish (0%)

### Overall Progress: ~27% Complete

---

## **Current Status**
- **Database Layer**: ✅ Production-ready
  - 5 models, 25 CRUD functions
  - Real-time indexes
  - 15 default configs
  - Comprehensive testing
  
- **ML Model**: ✅ Trained & Evaluated
  - XGBoost with 99.95% accuracy
  - 25 selected features
  - GPU-accelerated training
  - Model artifacts saved

- **Next Phase**: 🚀 Phase 4 - Packet Capture & Feature Extraction
  - Implement Scapy packet sniffer
  - Build flow generator
  - Map packets to model features

---

## **Checklist Tools & Libraries**

```txt
# Core
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
python-multipart==0.0.6

# ML
xgboost==2.0.0
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.24.3
imbalanced-learn==0.11.0

# Database
sqlalchemy==2.0.23

# Packet Capture
scapy==2.5.0

# WebSocket
websockets==12.0

# Utilities
python-dotenv==1.0.0
pydantic==2.5.0
```

---