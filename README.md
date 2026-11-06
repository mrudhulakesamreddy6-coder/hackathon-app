# DISASTERSYNC AI
### AI-Powered Multi-Agent Disaster Response and Emergency Coordination System

> **HACKATHON PROJECT DOCUMENTATION & DEMONSTRATION SUITE**  
> **Event:** 24Hrs Hackathon on Generative AI | **Date:** 07/11/2026  
> **Project Code / ID:** AG-AI-01  
> **Category:** Agentic AI / Emergency Response & Disaster Management  
> **Institution:** Bapatla Women's Engineering College  
> **Prepared by Team DISASTERSYNC AI:**
> - K. Mrudhula Reddy
> - G. Kavya
> - T. Sneha Latha  
> **Mentor / Guide:** Narayana swamy sir  

---

## ⚠️ Important Hackathon Demonstration Notice
**Simulated Alerts Only:** This project is developed strictly for hackathon evaluation and demonstration. All emergency notifications, police dispatches, hospital alerts, and rescue team mobilizations are **simulated**. No real 911 / 112 / 100 emergency services are contacted, and no real-world teams are dispatched.

---

## 🌟 Executive Summary & Problem Brief
During catastrophic natural or man-made disasters (such as flash floods, structural fires, severe earthquakes, or multi-vehicle highway collisions), multiple public safety agencies (Police, Fire & Rescue, Emergency Medical Services, and Disaster Response battalions like NDRF) must act simultaneously. 

Current coordination suffers from:
- Divergent communication channels (phone, radio, disparate dispatch centers).
- Floods of duplicate or conflicting civilian emergency calls.
- Inability to dynamically prioritize critical life-threatening situations.
- Lack of centralized resource visibility (ambulances, rescue boats, ICU beds).

**DisasterSync AI** introduces an **Agentic AI Coordination Layer** that receives reports, normalizes incident data, detects duplicates using spatial Haversine distance, calculates transparent urgency ratings (0–100), and deploys specialized AI agents to generate structured action plans for each agency. **Final dispatch decisions remain under human authority (Human-in-the-Loop).**

---

## 🤖 Multi-Agent System Architecture

| Agent | Responsibility | Output / Deliverable |
| :--- | :--- | :--- |
| **Coordinator Agent** | Orchestrates agent pipeline, calculates explainable urgency scores (0–100), synthesizes overall action plan. | Unified Incident Response Plan & Priority Level |
| **Police Coordination Agent** | Plans public safety, 500m perimeters, evacuation routes, and traffic management. | Police Tactical Checklist & Road Blockage Guidance |
| **Monitoring & Duplicate Agent** | Evaluates spatial proximity (&lt;2.0 km) and description overlap to group duplicate reports into clusters. | Duplicate Cluster Tag & Parent Incident Link |
| **Fire & Rescue Agent** | Analyzes structural collapse, thermal fire spread, water depth, and specialized rescue gear. | Rescue Equipment Checklist (Boats, Ladders, Cutters) |
| **Medical Assistance Agent** | Evaluates casualties, determines Triage category (Red/Yellow/Green), reserves hospital ICU beds. | Trauma Alert & Ambulance Dispatch Recommendation |
| **Resource Management Agent** | Matches nearest available assets (vehicles, boats, beds) from inventory and flags asset shortages. | Resource Allocation Requisition & Shortage Warning |
| **Communication & Alert Agent** | Generates simulated dispatches across CAD terminals, APCO-25 Radio, and Pager systems. | Standardized CAD Payload & Public Safety Advisory |

---

## 🛠️ Technology Stack
- **Backend Application:** Python 3.10+ / Flask 3.x
- **Database Layer:** **MySQL** with PyMySQL + Seamless automatic SQLite fallback (`disastersync.db`) for immediate zero-config testing.
- **Frontend / UI:** Responsive HTML5, Modern CSS3 with Command-Center Glassmorphism, Vanilla ES6 JavaScript.
- **Geospatial Mapping:** Leaflet.js with OpenStreetMap (no paid API keys required).
- **Icons & Styling:** FontAwesome 6, custom CSS animations, pulsing SOS indicators.
- **Sound Effects:** In-browser Web Audio API alert frequency synthesizer (no external audio assets required).

---

## 📁 Repository Structure
```
├── app.py                     # Main Flask Application & REST API Endpoints
├── config.py                  # Environment & App Configuration
├── database.py                # Dual MySQL / SQLite Database Connector
├── database.sql               # MySQL Schema & Initial Seed Data Script
├── requirements.txt           # Python Dependencies (Flask, PyMySQL, flask-cors)
├── run.bat                    # 1-Click Startup Script for Windows
├── run.ps1                    # 1-Click PowerShell Runner
├── README.md                  # Complete Documentation & Hackathon Manual
├── agents/                    # Multi-Agent Coordination Engine
│   ├── __init__.py
│   ├── coordinator_agent.py   # Master Triage & Prioritization Coordinator
│   ├── duplicate_agent.py     # Haversine Distance & Semantic Duplicate Detection
│   ├── police_agent.py        # Public Safety & Traffic Cordon Agent
│   ├── fire_rescue_agent.py   # Fire, Watercraft & Structural Search Agent
│   ├── medical_agent.py       # Casualty Triage & Hospital Bed Agent
│   ├── resource_agent.py      # Resource Inventory & Proximity Matching Agent
│   └── comms_agent.py         # Simulated Dispatch & Alert Broadcasting Agent
├── static/
│   ├── css/
│   │   └── style.css          # Modern command-center styling & responsive layout
│   └── js/
│       ├── app.js             # Core utilities, toast notifications, demo scenario loader
│       ├── report.js          # Intake validation, GPS geolocation, Leaflet picker
│       ├── dashboard.js       # Live incident feed, filters, inline status updates
│       └── map.js             # Leaflet geospatial map with color-coded pulsing pins
└── templates/
    ├── base.html              # Layout with Hackathon disclaimer banner & navbar
    ├── index.html             # Landing portal with Big 1-Click SOS Panic Button
    ├── report.html            # Public emergency intake form with interactive map
    ├── dashboard.html         # Admin Command Center with live map & filters
    ├── incident_detail.html   # Master Multi-Agent coordination analysis view
    ├── resources.html         # Agency resource inventory & capacity board
    ├── alerts.html            # Simulated emergency broadcast terminal & audit log
    └── docs.html              # In-app hackathon documentation & test matrix
```

---

## 🚀 Quick Start & Installation

### Option 1: 1-Click Startup (Windows)
Double click `run.bat` or run in PowerShell:
```powershell
.\run.ps1
```

### Option 2: Manual Terminal Startup
1. Open PowerShell or Command Prompt in the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🗄️ Database Setup (MySQL)
The application includes a dual-engine architecture:
1. **Using MySQL (Recommended for Production / Evaluation):**
   - Import `database.sql` into your MySQL server (via MySQL CLI, phpMyAdmin, or MySQL Workbench):
     ```bash
     mysql -u root -p < database.sql
     ```
   - Update credentials in `config.py` if your MySQL user/password differs from default:
     ```python
     MYSQL_HOST = 'localhost'
     MYSQL_USER = 'root'
     MYSQL_PASSWORD = ''
     MYSQL_DB = 'disastersync_db'
     ```
2. **Zero-Configuration Fallback (SQLite):**
   - If MySQL is not running or credentials are not yet configured, DisasterSync AI automatically switches to high-speed local SQLite (`disastersync.db`) with zero downtime!

---

## 🎯 Hackathon Demonstration Walkthrough (For Judges)

### Step 1: Quick 1-Click Demo Scenario
On the homepage or Command Center, click the yellow **"Load Hackathon Demo Scenario"** button.
This instantly loads the fictional flood disaster from **Section 13.1 of the Hackathon Documentation**:
1. **Neighborhood A (Flood Inundation):** East Colony canal breach, 4 trapped on roof, Urgency Score: 80 (CRITICAL).
2. **Neighborhood A (Duplicate Report):** Second resident reports the exact same flood 200m away. **AI Duplicate Agent automatically flags it as a duplicate and links it to Incident #1!**
3. **Neighborhood B (Critical SOS Beacon):** Submerged transformer explosion causing fire. Urgency Score: 100 (CRITICAL SOS).
4. **Neighborhood C (Evacuation Route Collision):** Highway bus collision with 6 casualties requiring ALS ambulances and police traffic diversions.

### Step 2: Test the 1-Click Urgent SOS Panic Button
1. Click the large red **"SOS"** button on the homepage or navigation bar.
2. The browser automatically locks onto device GPS coordinates.
3. Click **"TRANSMIT SOS NOW"**.
4. The system triggers an emergency chime, calculates an Urgency Score of 100/100, and immediately generates simulated CAD alerts for Police, Fire, and Ambulance units!

### Step 3: Interactive Geospatial Map
Navigate to the **Command Center** (`/dashboard`):
- Zoom in and inspect the pins on the interactive map.
- Red markers pulse for Critical/SOS incidents.
- Click any marker to view the incident popup and navigate straight to its multi-agent intelligence plan.

### Step 4: Inspect Multi-Agent AI Analysis
Click **"AI Agents Plan"** on any incident to view the **Incident Detail View** (`/incident/<id>`):
- Read the **Urgency Score Breakdown** (+40 SOS, +30 Trapped, +25 Casualties).
- Review each agent card:
  - **Police Agent:** 500m cordon and traffic clearance.
  - **Fire & Rescue Agent:** Inflatable motorized rescue boats.
  - **Medical Agent:** Triage Red, ALS Ambulances, Hospital ICU bed reservations.
  - **Resource Agent:** Proximity matching of nearest units.
- **Human-in-the-Loop Authorization:** Click **"Authorize Dispatch"** or **"Transmit Radio / CAD"** to approve simulated alerts.
- Change the Incident Status (`Reported` ➔ `Verified` ➔ `Dispatched` ➔ `In Progress` ➔ `Resolved`).
- Check the **Audit Trail** at the bottom, verifying who approved what and when.

---

## 🧪 Verification Matrix (Section 14 Test Results)
| Test ID | Test Scenario | Result | Status |
| :--- | :--- | :--- | :--- |
| **T-01** | Submit complete incident report | Incident recorded with GPS coordinates and timestamp | **PASSED** |
| **T-02** | Submit report with missing location | Auto-assigned default municipal area or GPS acquired | **PASSED** |
| **T-03** | Submit 2 similar reports within 2km | Flagged as duplicate &amp; linked to parent incident | **PASSED** |
| **T-04** | Urgent 1-Click SOS Distress Button | Urgency Score set to 100/100 with immediate broadcast | **PASSED** |
| **T-05** | Multi-Agent Coordination Synthesis | Structured outputs produced by all 5 specialized agents | **PASSED** |
| **T-06** | Human Officer Approval Workflow | Alerts remain PENDING until human officer authorizes | **PASSED** |
| **T-07** | Proximity Resource Matching | Nearest available boats and ambulances allocated | **PASSED** |
| **T-08** | Audit Trail & Governance Logging | All submissions, triage events, and updates logged | **PASSED** |

---

## 🏆 Hackathon Credits & Affiliation
- **Project Name:** DisasterSync AI
- **Project Code:** AG-AI-01
- **College:** Bapatla Women's Engineering College
- **Team Members:**
  1. K. Mrudhula Reddy
  2. G. Kavya
  3. T. Sneha Latha
- **Mentor:** Narayana swamy sir
- **Hackathon:** 24Hrs Hackathon on Generative AI (07/11/2026)

