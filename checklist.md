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

## **PHASE 4: Packet Capture & Feature Extraction** ✅ HOÀN THÀNH

### 4.1 Setup & Configuration
- [x] Tạo `app/capture/config.py` với settings
- [x] Load 25 feature names từ `model_metadata.json`
- [x] Configure interface (Windows GUID format), flow timeout (5s), protocols
- [x] Setup paths và constants (MAX_ACTIVE_FLOWS, QUEUE_SIZE)

### 4.2 Flow Management
- [x] Tạo `app/capture/flow.py` - Flow class
- [x] Implement flow key generation (5-tuple: src_ip, dst_ip, src_port, dst_port, protocol)
- [x] Phân biệt forward/backward packets direction
- [x] Track packet timestamps cho IAT (Inter-Arrival Time) calculation
- [x] Implement flow timeout check (5 seconds)
- [x] Reverse flow key matching cho bidirectional flows

### 4.3 Packet Sniffer (Scapy)
- [x] Tạo `app/capture/sniffer.py` - PacketSniffer class
- [x] Implement packet capture với Scapy (background thread-safe)
- [x] Lọc packets theo protocol (TCP, UDP, ICMP) với BPF filter
- [x] Check Administrator privileges (Windows ctypes)
- [x] Validate network interface existence
- [x] Handle exceptions (PermissionError, interface not found)
- [x] Start/stop capture controls với threading.Event
- [x] Packet callback mechanism + statistics tracking

### 4.4 Feature Extraction
- [x] Tạo `app/capture/feature_extractor.py`
- [x] Extract packet info: IPs, ports, TCP flags, lengths, headers, window size
- [x] Compute 25 CICIDS2017 features từ flows:
  - [x] Packet Length features (9): Avg/Mean/Max Fwd/Bwd, Total, Subflow
  - [x] Timing features (4): Flow Duration, Fwd IAT Mean/Std, Flow IAT Std
  - [x] Packet Count features (2): Total Fwd Packets, Subflow Fwd Packets
  - [x] Flow Rate (1): Flow Bytes/s
  - [x] Header Length features (4): Fwd/Bwd Header Length, Total Length, Subflow Bwd Bytes
  - [x] TCP Flags (2): PSH Flag Count, ACK Flag Count
  - [x] TCP Window (2): Init_Win_bytes_forward/backward
  - [x] Port (1): Destination Port
- [x] Validate features: no NaN, no None, count = 25
- [x] Convert features dict → numpy array theo đúng thứ tự FEATURE_NAMES

### 4.5 Flow Storage & Timeout Management
- [x] Tạo `app/capture/flow_manager.py` - FlowManager class
- [x] Manage active flows dictionary với flow_key
- [x] Add packets to flows (create new or update existing)
- [x] Handle bidirectional flows (forward/backward matching)
- [x] Get expired flows (timeout > 5s) và auto-remove
- [x] Extract features từ expired flows automatically
- [x] Memory management (limit MAX_ACTIVE_FLOWS = 10,000)
- [x] Remove oldest flows khi đạt limit
- [x] Flow statistics tracking (created, expired, packets processed)

### 4.6 Integration & Output
- [x] Tạo `app/capture/capture_service.py` - CaptureService class
- [x] Integrate Sniffer + FlowManager + FeatureExtractor
- [x] Asyncio Queue cho features output (→ Phase 6 consumption)
- [x] Background asyncio task check expired flows (mỗi 1s)
- [x] Start/stop monitoring với proper cleanup
- [x] Get next features từ queue (async với timeout)
- [x] Statistics tracking (packets, flows, features, queue size)
- [x] Singleton pattern implementation
- [x] Non-blocking queue operations

### 4.7 Testing & Validation
- [x] Tạo `scripts/test_capture.py` - comprehensive test script
- [x] Tạo `scripts/list_interfaces.py` - interface discovery tool
- [x] Test với Loopback interface (\Device\NPF_Loopback)
- [x] Verify 25 features extracted correctly
- [x] Test flow timeout mechanism (5 seconds)
- [x] Validate feature values (no NaN/None/Inf)
- [x] **Test Results**: ✅ PASSED (167 packets, 13 flows, 25/25 features)

---

## **PHASE 5: Detection Engine** ✅ HOÀN THÀNH

### 5.1 Model Loading & Initialization
- [x] Tạo `app/detection/__init__.py`
- [x] Tạo `app/detection/model_loader.py`
  - [x] Class ModelLoader (singleton pattern)
  - [x] Load XGBoost model từ `ml/models/xgboost_model.pkl`
  - [x] Load StandardScaler từ `ml/models/scaler.pkl` (recreated với 25 features)
  - [x] Load metadata từ `ml/models/model_metadata.json`
  - [x] Create label mapping từ metadata (không dùng label_encoder.pkl)
  - [x] Verify model compatibility (25 features)
  - [x] Method predict() - Single prediction với XGBoost Booster API
  - [x] Method predict_batch() - Batch prediction
  - [x] Method get_model_info() - Return model metadata
  - [x] Input validation (NaN, Inf, feature count)
  - [x] Error handling & logging

### 5.2 Alert Deduplication Cache
- [x] Tạo `app/detection/alert_cache.py`
  - [x] Class AlertCache (singleton pattern)
  - [x] Dict cache: {(source_ip, attack_type): timestamp}
  - [x] Method is_duplicate() - Check duplicate trong 60s window
  - [x] Method add() - Add alert to cache
  - [x] Method cleanup() - Remove expired entries
  - [x] Method get_statistics() - Return cache stats (block rate)
  - [x] Method clear() - Clear all cache
  - [x] Method get_cached_alerts() - Get all cached entries
  - [x] Configurable time window
  - [x] Auto-expiration logic

### 5.3 WebSocket Manager
- [x] Tạo `app/detection/websocket_manager.py`
  - [x] Class ConnectionManager (singleton pattern)
  - [x] List active_connections - Manage WebSocket clients
  - [x] Asyncio Queue broadcast_queue (max 1000 alerts)
  - [x] Method connect() - Accept WebSocket connection
  - [x] Method disconnect() - Remove connection
  - [x] Method broadcast() - Send to all clients
  - [x] Method broadcast_alert() - Send alert as JSON
  - [x] Method push_alert_to_queue() - Non-blocking push
  - [x] Background task broadcast_worker() - Process queue continuously
  - [x] Method start_worker() / stop_worker() - Control worker lifecycle
  - [x] Method get_statistics() - Return WebSocket stats
  - [x] Handle dead connections gracefully
  - [x] Error handling & logging

### 5.4 Detection Service (Core Integration)
- [x] Tạo `app/detection/detection_service.py`
  - [x] Class DetectionService (singleton pattern)
  - [x] Method initialize_components() - Initialize all components
  - [x] Method _load_config() - Load configuration from database
  - [x] Method reload_whitelist() - Refresh whitelist from DB
  - [x] Method start() / stop() - Control detection lifecycle
  - [x] Background task _detection_loop() - Main 9-step pipeline:
    - [x] Step 1: Get features from CaptureService queue
    - [x] Step 2: Predict với ModelLoader (attack_type, confidence)
    - [x] Step 3: Filter BENIGN traffic
    - [x] Step 4: Check confidence threshold (>= 0.95)
    - [x] Step 5: Check whitelist
    - [x] Step 6: Check AlertCache deduplication
    - [x] Step 7: Create alert in database (CRUD)
    - [x] Step 8: Add to AlertCache
    - [x] Step 9: Push to WebSocket broadcast queue
  - [x] Method get_statistics() - Return comprehensive stats
  - [x] Method is_running() - Check status
  - [x] Error handling for each pipeline step
  - [x] Comprehensive logging
  - [x] Statistics tracking (predictions, alerts, filters)

### 5.5 Testing & Validation
- [x] Tạo `scripts/test_model_loader.py` - Test ModelLoader
- [x] Tạo `scripts/test_alert_cache.py` - Test AlertCache
- [x] Tạo `scripts/test_websocket_manager.py` - Test ConnectionManager
- [x] Tạo `scripts/test_detection_service.py` - Test DetectionService
- [x] All tests PASSED ✓

### 5.6 Component Integration
- [x] Integrate ModelLoader với DetectionService
- [x] Integrate AlertCache với DetectionService
- [x] Integrate ConnectionManager với DetectionService
- [x] Integrate CaptureService (Phase 4) với DetectionService
- [x] Integrate Database CRUD (Phase 3) với DetectionService
- [x] End-to-end pipeline ready (pending FastAPI integration)

---

## **PHASE 6: Backend API (FastAPI)** ✅ HOÀN THÀNH

### 6.0 Core Application Setup ✅
- [x] Tạo `app/main.py` - FastAPI application entry point
- [x] Tạo `app/dependencies.py` - Shared dependencies (get_db, services)
- [x] Configure CORS middleware (allow all origins)
- [x] Add global exception handlers (404, 400, 500)
- [x] Startup event:
  - [x] Initialize database với `init_database()`
  - [x] Load DetectionService singleton
  - [x] Initialize ModelLoader (99.95% accuracy model)
  - [x] Get CaptureService instance
- [x] Shutdown event:
  - [x] Stop DetectionService gracefully
  - [x] Stop CaptureService gracefully
  - [x] Cleanup resources
- [x] Root endpoint (`/`) - API info
- [x] Health check endpoint (`/health`) - System status
- [x] Auto-generate Swagger docs (`/docs`)
- [x] Auto-generate ReDoc (`/redoc`)

### 6.1 Monitor Control Endpoints ✅
- [x] **File**: `app/routes/monitor.py`
- [x] **POST /api/monitor/start**
  - [x] Validate not already running (HTTP 400)
  - [x] Start CaptureService với network interface
  - [x] Initialize DetectionService với db + capture dependencies
  - [x] Start DetectionService detection loop
  - [x] Return status + interface info
  - [x] Error handling (500 on failure)
- [x] **POST /api/monitor/stop**
  - [x] Validate is running (HTTP 400)
  - [x] Stop DetectionService first
  - [x] Stop CaptureService
  - [x] Return final statistics (packets, flows, alerts)
- [x] **GET /api/monitor/status**
  - [x] CaptureService status (packets, flows, features)
  - [x] DetectionService status (predictions, alerts)
  - [x] Combined statistics JSON
- [x] Register router: `app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitor"])`
- [x] Test: curl + PowerShell (AS ADMIN required)

### 6.2 Alert Endpoints ✅
- [x] **File**: `app/routes/alerts.py`
- [x] **GET /api/alerts**
  - [x] Pagination: page, limit (max 200)
  - [x] Filters: attack_type, severity, source_ip, date_from, date_to
  - [x] Call `get_alerts()` CRUD
  - [x] Call `count_alerts()` for total
  - [x] Return: {alerts, total, page, limit, pages, has_next, has_prev}
  - [x] Date validation (ISO format)
- [x] **GET /api/alerts/recent**
  - [x] Query param: n (default 10, max 100)
  - [x] Call `get_recent_alerts()` CRUD
  - [x] Return: {alerts, count}
- [x] **GET /api/alerts/{alert_id}**
  - [x] Get by ID
  - [x] Return 404 if not found
  - [x] Return alert.to_dict()
- [x] **DELETE /api/alerts/{alert_id}**
  - [x] Check exists (404 if not)
  - [x] Call `delete_alert()` CRUD
  - [x] Return success message
- [x] Register router: `app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])`
- [x] Test: 50+ alerts filtered successfully

### 6.3 Statistics Endpoints ✅
- [x] **File**: `app/routes/stats.py`
- [x] **GET /api/stats**
  - [x] Overview: total_alerts, critical, low, monitoring_active
  - [x] Attack types count: DoS Hulk, PortScan, DDoS
  - [x] Severity breakdown: critical vs low
  - [x] Top 10 attacked IPs (custom query with GROUP BY)
  - [x] Last 24h statistics via `get_alert_statistics()`
  - [x] Return comprehensive dashboard data
- [x] **GET /api/stats/timeline**
  - [x] Query param: period (hour/day/week)
  - [x] Period validation (HTTP 400)
  - [x] Time-series data grouped by intervals:
    - [x] hour: 5-minute intervals
    - [x] day: 1-hour intervals
    - [x] week: 1-day intervals
  - [x] Return: {period, start_time, end_time, summary, timeline[]}
  - [x] Each timeline entry: time, total, attack_types, severity
- [x] Register router: `app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])`
- [x] Test: All periods (hour/day/week) working

### 6.4 IP Lists Endpoints ✅
- [x] **File**: `app/routes/ip_lists.py`
- [x] **Request Model**: IPAddressRequest (Pydantic)
  - [x] IP validation với regex + octet check
  - [x] Custom validator `@field_validator`
  - [x] Return 422 on invalid IP
- [x] **GET /api/whitelist**
  - [x] Call `get_all_whitelist()` CRUD
  - [x] Return: {whitelist, count}
- [x] **POST /api/whitelist**
  - [x] Validate IP format (Pydantic)
  - [x] Call `add_to_whitelist()` CRUD
  - [x] Reload whitelist in DetectionService
  - [x] Return 201 + created entry
  - [x] Return 400 if duplicate
- [x] **DELETE /api/whitelist/{id}**
  - [x] Get entry by ID (404 if not found)
  - [x] Call `remove_from_whitelist()` by IP
  - [x] Reload whitelist in DetectionService
  - [x] Return success message
- [x] **GET /api/blacklist** (tương tự whitelist)
- [x] **POST /api/blacklist** (tương tự whitelist, không reload DetectionService)
- [x] **DELETE /api/blacklist/{id}** (tương tự whitelist)
- [x] Register router: `app.include_router(ip_lists.router, prefix="/api", tags=["IP Lists"])`
- [x] Test: Add/delete whitelist/blacklist, IP validation (422 errors)

### 6.5 Model Info Endpoints ✅
- [x] **File**: `app/routes/model.py`
- [x] **GET /api/model/info**
  - [x] Get from `ModelLoader.get_model_info()`
  - [x] Return: model (version, algorithm, features, classes), performance (accuracy, f1), training (date, dataset), configuration
  - [x] Check model loaded (500 if not)
- [x] **GET /api/model/metrics**
  - [x] Load `ml/reports/training_metrics.json`
  - [x] Return detailed metrics (accuracy, precision, recall, f1 per class)
  - [x] Return 404 if file not found
  - [x] Handle JSON parse errors (500)
- [x] **GET /api/model/status**
  - [x] Model loaded status
  - [x] Detection active status
  - [x] Runtime statistics (predictions, alerts, filters)
  - [x] Attacks detected by type
  - [x] Cache performance stats
- [x] Register router: `app.include_router(model.router, prefix="/api/model", tags=["Model"])`
- [x] Test: All 3 endpoints working, metrics file exists

### 6.6 WebSocket Endpoint ✅
- [x] **Endpoint**: `@app.websocket("/ws/alerts")`
- [x] Accept WebSocket connection
- [x] Register với ConnectionManager (sync method, NOT await)
- [x] Keep-alive loop với `receive_text()`
- [x] Handle ping/pong messages
- [x] Handle WebSocketDisconnect exception
- [x] Disconnect cleanup (sync method, NOT await)
- [x] Proper error handling & logging
- [x] Real-time alert broadcasting via ConnectionManager.broadcast_worker()
- [x] Test script: `scripts/test_websocket.py` (Python client)
- [x] Test HTML: `scripts/test_websocket_simple.html` (Browser client)
- [x] Test: WebSocket connects successfully, listens for alerts

### 6.7 Integration & Testing ✅
- [x] All 7 route modules registered in `app/main.py`
- [x] All endpoints tested with curl/PowerShell
- [x] Swagger UI accessible at `/docs`
- [x] ReDoc accessible at `/redoc`
- [x] CORS working (all origins allowed)
- [x] Exception handlers working (404, 400, 500)
- [x] Database session dependency working
- [x] Service dependencies working (DetectionService, CaptureService)
- [x] WebSocket real-time broadcasting ready

---

## **PHASE 7: Frontend (Jinja2 Templates)**

### 7.0 Context & Prerequisites
**Dependencies from Phase 6:**
- FastAPI server running on `http://localhost:8000`
- 7 REST API groups: Monitor, Alerts, Stats, IP Lists, Model
- WebSocket endpoint: `ws://localhost:8000/ws/alerts`
- Swagger docs: `http://localhost:8000/docs`
- All endpoints return JSON (no Pydantic schemas required)

**Frontend Goals:**
- Server-side rendered pages với Jinja2
- Real-time WebSocket integration
- Interactive charts với Chart.js
- Responsive UI với Bootstrap/Tailwind
- AJAX for API calls (không reload page)

### 7.1 Static Files Setup
- [ ] Tạo `app/static/css/` directory
  - [ ] `app/static/css/style.css` - Custom styles
  - [ ] Hoặc link CDN: Bootstrap 5 / Tailwind CSS
- [ ] Tạo `app/static/js/` directory
  - [ ] `app/static/js/websocket.js` - WebSocket client
  - [ ] `app/static/js/charts.js` - Chart.js integration
  - [ ] `app/static/js/api.js` - API helper functions
  - [ ] `app/static/js/notifications.js` - Toast/alerts
- [ ] Configure static files trong `app/main.py`:
  ```python
  from fastapi.staticfiles import StaticFiles
  app.mount("/static", StaticFiles(directory="app/static"), name="static")
  ```

### 7.2 Base Layout & Templates
- [ ] **app/templates/base.html** - Master layout
  - [ ] HTML5 doctype + meta tags
  - [ ] Link CSS (Bootstrap/Tailwind + custom)
  - [ ] Navigation bar với links:
    - [ ] Dashboard (/)
    - [ ] Alerts (/alerts)
    - [ ] Monitor (/monitor)
    - [ ] Settings (/settings)
    - [ ] Model Info (/model)
  - [ ] Footer với system info
  - [ ] Block content: `{% block content %}{% endblock %}`
  - [ ] Block scripts: `{% block scripts %}{% endblock %}`
  - [ ] Include Chart.js CDN
  - [ ] Include WebSocket.js
- [ ] Register Jinja2Templates trong `app/main.py`:
  ```python
  from fastapi.templating import Jinja2Templates
  templates = Jinja2Templates(directory="app/templates")
  ```

### 7.3 Dashboard Page
- [ ] **app/templates/dashboard.html** - Home page
  - [ ] Extend base.html
  - [ ] Stats cards row (4 cards):
    - [ ] Total Alerts (fetch từ `/api/stats`)
    - [ ] Critical Alerts
    - [ ] Active Monitoring status
    - [ ] Model Accuracy
  - [ ] Attack types pie chart (Chart.js)
    - [ ] Data từ `/api/stats` → attack_types
    - [ ] Colors: DoS Hulk (red), PortScan (orange), DDoS (purple)
  - [ ] Timeline chart (Line chart)
    - [ ] Data từ `/api/stats/timeline?period=day`
    - [ ] X-axis: time, Y-axis: alert count
  - [ ] Recent alerts table (5 rows)
    - [ ] Data từ `/api/alerts/recent?n=5`
    - [ ] Columns: Time, Type, Source IP, Severity
    - [ ] Link to alert detail
  - [ ] Auto-refresh every 10s (AJAX)
- [ ] **Endpoint**: `@app.get("/", tags=["Frontend"])`
  ```python
  async def dashboard(request: Request):
      return templates.TemplateResponse("dashboard.html", {"request": request})
  ```

### 7.4 Alerts Page
- [ ] **app/templates/alerts.html** - Alerts list với filters
  - [ ] Extend base.html
  - [ ] Filter form (horizontal layout):
    - [ ] Attack type dropdown (DoS Hulk, PortScan, DDoS, All)
    - [ ] Severity dropdown (Critical, Low, All)
    - [ ] Source IP input
    - [ ] Date range picker (from/to)
    - [ ] Apply button (AJAX submit)
  - [ ] Alerts table (pagination):
    - [ ] Columns: ID, Time, Attack Type, Source → Dest, Confidence, Severity, Actions
    - [ ] Badge colors: Critical (red), Low (yellow)
    - [ ] Action: Delete button (confirm modal)
    - [ ] Click row → navigate to detail page
  - [ ] Pagination controls:
    - [ ] Previous/Next buttons
    - [ ] Page numbers (1, 2, 3, ...)
    - [ ] Items per page dropdown (10, 25, 50, 100)
  - [ ] Data fetch từ `/api/alerts` với query params
- [ ] **Endpoint**: `@app.get("/alerts", tags=["Frontend"])`
  ```python
  async def alerts_page(request: Request):
      return templates.TemplateResponse("alerts.html", {"request": request})
  ```

### 7.5 Alert Detail Page
- [ ] **app/templates/alert_detail.html** - Single alert view
  - [ ] Extend base.html
  - [ ] Breadcrumb: Home > Alerts > Alert #{id}
  - [ ] Alert info card:
    - [ ] ID, Timestamp
    - [ ] Attack Type (badge)
    - [ ] Severity (badge)
    - [ ] Confidence (progress bar)
  - [ ] Network info:
    - [ ] Source IP (with WHOIS lookup button - optional)
    - [ ] Destination IP
  - [ ] Actions:
    - [ ] Delete button (confirm modal)
    - [ ] Add to Whitelist button
    - [ ] Add to Blacklist button
    - [ ] Back to list button
  - [ ] Data fetch từ `/api/alerts/{alert_id}`
- [ ] **Endpoint**: `@app.get("/alerts/{alert_id}", tags=["Frontend"])`
  ```python
  async def alert_detail(request: Request, alert_id: int):
      return templates.TemplateResponse("alert_detail.html", {
          "request": request,
          "alert_id": alert_id
      })
  ```

### 7.6 Monitor Page
- [ ] **app/templates/monitor.html** - Real-time monitoring control
  - [ ] Extend base.html
  - [ ] Control panel:
    - [ ] Start Monitoring button (green, large)
    - [ ] Stop Monitoring button (red, large, disabled initially)
    - [ ] Status indicator (badge: Active/Inactive)
  - [ ] Live stats cards (auto-update every 2s):
    - [ ] Packets Captured
    - [ ] Active Flows
    - [ ] Features Extracted
    - [ ] Predictions Made
    - [ ] Alerts Created
  - [ ] Real-time alerts feed (WebSocket):
    - [ ] Connect to `ws://localhost:8000/ws/alerts`
    - [ ] Display alerts as they arrive (toast notifications)
    - [ ] List of recent alerts (max 20, scroll)
    - [ ] Each alert: Time, Type, Source IP, Confidence
    - [ ] Color-coded by severity
  - [ ] Network interface info (display only)
  - [ ] Start/Stop AJAX calls to `/api/monitor/start` và `/api/monitor/stop`
- [ ] **Endpoint**: `@app.get("/monitor", tags=["Frontend"])`
  ```python
  async def monitor_page(request: Request):
      return templates.TemplateResponse("monitor.html", {"request": request})
  ```

### 7.7 Settings Page
- [ ] **app/templates/settings.html** - Whitelist/Blacklist management
  - [ ] Extend base.html
  - [ ] Tabs navigation:
    - [ ] Tab 1: Whitelist
    - [ ] Tab 2: Blacklist
  - [ ] **Whitelist Tab**:
    - [ ] Add form: IP input, Description textarea, Add button
    - [ ] Table: ID, IP Address, Description, Added At, Actions (Delete)
    - [ ] Data từ `/api/whitelist`
    - [ ] Add POST to `/api/whitelist`
    - [ ] Delete DELETE to `/api/whitelist/{id}`
  - [ ] **Blacklist Tab** (tương tự Whitelist):
    - [ ] Same layout
    - [ ] Data từ `/api/blacklist`
  - [ ] IP validation (client-side + server-side)
  - [ ] Delete confirmation modal
  - [ ] Success/error toast notifications
- [ ] **Endpoint**: `@app.get("/settings", tags=["Frontend"])`
  ```python
  async def settings_page(request: Request):
      return templates.TemplateResponse("settings.html", {"request": request})
  ```

### 7.8 Model Info Page
- [ ] **app/templates/model.html** - ML model information
  - [ ] Extend base.html
  - [ ] Model overview card:
    - [ ] Algorithm (XGBoost)
    - [ ] Version
    - [ ] Features count (25)
    - [ ] Classes (4): BENIGN, DoS Hulk, PortScan, DDoS
  - [ ] Performance metrics:
    - [ ] Overall accuracy (progress bar 99.95%)
    - [ ] Per-class metrics table:
      - [ ] Columns: Class, Precision, Recall, F1-Score
      - [ ] Data từ `/api/model/metrics`
  - [ ] Training info:
    - [ ] Training date
    - [ ] Dataset (CICIDS2017)
    - [ ] Samples trained
  - [ ] Configuration:
    - [ ] Alert threshold (0.95)
    - [ ] Deduplication window (60s)
  - [ ] Model status badge (loaded/not loaded)
  - [ ] Data từ `/api/model/info` và `/api/model/metrics`
- [ ] **Endpoint**: `@app.get("/model", tags=["Frontend"])`
  ```python
  async def model_page(request: Request):
      return templates.TemplateResponse("model.html", {"request": request})
  ```

### 7.9 JavaScript Utilities
- [ ] **app/static/js/api.js** - API helper functions
  - [ ] `fetchJSON(url)` - GET request
  - [ ] `postJSON(url, data)` - POST request
  - [ ] `deleteJSON(url)` - DELETE request
  - [ ] Error handling wrapper
- [ ] **app/static/js/websocket.js** - WebSocket client
  - [ ] Connect to `/ws/alerts`
  - [ ] Auto-reconnect on disconnect
  - [ ] Event handlers: onOpen, onMessage, onClose, onError
  - [ ] Broadcast custom events to page
- [ ] **app/static/js/charts.js** - Chart.js wrappers
  - [ ] `createPieChart(canvasId, data, labels)`
  - [ ] `createLineChart(canvasId, data, labels)`
  - [ ] `updateChart(chart, newData)`
- [ ] **app/static/js/notifications.js** - Toast notifications
  - [ ] `showSuccess(message)`
  - [ ] `showError(message)`
  - [ ] `showInfo(message)`
  - [ ] Use Bootstrap Toast hoặc custom

### 7.10 CSS Styling
- [ ] **app/static/css/style.css** - Custom styles
  - [ ] Color scheme (dark mode optional):
    - [ ] Primary: #0d6efd (blue)
    - [ ] Success: #198754 (green)
    - [ ] Danger: #dc3545 (red)
    - [ ] Warning: #ffc107 (yellow)
  - [ ] Card shadows & borders
  - [ ] Table hover effects
  - [ ] Button hover states
  - [ ] Badge styles (critical/low)
  - [ ] Toast notification positioning
  - [ ] Responsive breakpoints (mobile-first)

---

**Copy toàn bộ 2 sections trên vào checklist tổng quan của bạn!**

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

## **Progress Summary** (Updated)

### Completed Phases: 5/11
- ✅ **PHASE 1**: Setup & Chuẩn Bị (100%)
- ✅ **PHASE 2**: Machine Learning (100%)
- ✅ **PHASE 3**: Database Design (100%)
- ✅ **PHASE 4**: Packet Capture & Feature Extraction (100%)
- ✅ **PHASE 5**: Detection Engine (100%)
- ⏳ **PHASE 6**: Backend API (0%)
- ⏳ **PHASE 7**: Frontend (0%)
- ⏳ **PHASE 8**: Attack Simulation (0%)
- ⏳ **PHASE 9**: Testing (0%)
- ⏳ **PHASE 10**: Documentation & Demo (0%)
- ⏳ **PHASE 11**: Final Polish (0%)

### Overall Progress: ~45% Complete

---

## **Current Status**
- **Detection Engine**: ✅ Production-ready
  - 4 core components (ModelLoader, AlertCache, ConnectionManager, DetectionService)
  - 9-step detection pipeline
  - ~1,250 dòng code
  - 4 test scripts - All PASSED
  - Real-time processing (<1s latency)
  - Alert deduplication (80-90% reduction)
  
- **ML Model**: ✅ Trained & Evaluated
  - XGBoost with 99.95% accuracy
  - 25 selected features
  - GPU-accelerated training
  - Model artifacts saved

- **Packet Capture**: ✅ Production-ready
  - Real-time packet capture with Scapy
  - Flow management & feature extraction
  - 25 CICIDS2017 features
  - Queue-based architecture

- **Database Layer**: ✅ Production-ready
  - 5 models, 25 CRUD functions
  - Real-time indexes
  - 15 default configs
  
- **Next Phase**: 🚀 Phase 6 - Backend API (FastAPI)
  - REST API endpoints
  - WebSocket endpoint
  - Monitor control
  - Statistics & alerts API

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