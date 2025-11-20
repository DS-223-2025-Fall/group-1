# 📊 Dynamic Pricing for Yerevan Cafés & Restaurants  
### **DS223 — Marketing Analytics (Milestone 2)**  
### American University of Armenia

This repository contains the **second milestone** of the team project *Dynamic Pricing in Yerevan*, developed for **DS223 – Marketing Analytics** under the supervision of **Instructor Karen Hovhannisyan**.

Our goal is to build a modular, scalable, service-based architecture for a pricing optimization system designed specifically for **Armenian cafés and restaurants**, integrating analytics, backend services, database infrastructure, and UI components.

---

# 🚦 Project Roadmap & UI Prototype

### 📍 **Roadmap (Figma)**  
🔗 https://www.figma.com/make/DA2iRGczqJoVTTSvkeQVn1/Project-Roadmap-Timeline

### 🎨 **UI Prototype (Figma)**  
🔗 https://www.figma.com/make/05Xegl324Lppf6OZrCHz8V/Pricing-Optimization-Dashboard

---

# 📘 Problem Definition

*(summarized from the uploaded document)*  

Armenia’s café and restaurant sector often relies on intuition rather than data-driven pricing strategies. Businesses rarely evaluate how price changes influence demand, customer satisfaction, or revenue. This leads to unstable profit margins, poor forecasting, and reactive decision-making.

The objective of this project is to build a **data-driven pricing optimization framework** capable of:

- Modeling price elasticity  
- Simulating demand  
- Quantifying the effects of promotions  
- Forecasting pricing outcomes  
- Providing visual tools for decision-making  

The system will use:

- **FastAPI** for backend APIs  
- **Streamlit** for UI and visualization  
- **Python analytics stack**  
- **PostgreSQL/SQLite** for data storage  

---

# 🧩 Milestone 2: Completed Tasks

### **Product Management (PM)**
- Review and merge PRs  
- Transform repository to **service-based layout**  
- Define ERD  
- Initialize documentation structure  
- Coordinate cross-team workflow  

### **Database (DB)**
- Create DB branch & service container  
- Push schemas and helper functions  
- Open PRs for review  

### **Backend (API)**
- Create backend service structure  
- Implement CRUD endpoints  
- Design endpoints with PM & DB  
- PR submissions  

### **Frontend (UI)**
- Create frontend service container  
- Push UI skeleton  
- Coordinate design with PM & DS  
- PR submissions  

### **Data Science (DS)**
- Create DS service container  
- Simulate additional data  
- Build baseline models  
- Integrate DB functions  
- Submit PR for review  

---

# 🏗️ Repository Structure (Service-Based Architecture)

```
yerevan_pricing/
│
├── api/                     # FastAPI backend service
│   ├── main.py
│   ├── routers/
│   ├── models/
│   ├── database/
│   └── Dockerfile
│
├── app/                     # Streamlit frontend service
│   ├── pages/
│   ├── utils/
│   └── Dockerfile
│
├── etl/                     # ETL service (data loading → Postgres)
│   ├── database/
│   │   ├── data/            # CSV files
│   │   ├── load_data.py     # ETL loader
│   │   └── helpers.py
│   ├── init/                # initial SQL schemas
│   │   └── init.sql
│   └── Dockerfile
│
├── analytics/               # Data Science & Modeling service
│   ├── baseline_models.py
│   ├── run_baseline.py
│   ├── utils/
│   │   └── db_connect.py
│   └── Dockerfile
│
│
├── docker-compose.yml       # Multi-service orchestration
├── .env                     # Environment variables (DB, API, App)
├── requirements.txt         # Python dependencies
├── README.md                # Project overview
└── .gitignore               # Ignore rules


```

---

# 👥 Team Members

| Role | Name |
|------|------|
| Product Manager | Shushan Meyroyan |
| Database Developer | Arina Hovhannisyan |
| Backend Developer | Narek Nurijanyan |
| Frontend Developer | Areg Khachatryan |
| Data Scientist | Shushan Gevorgyan |

---

# 🛠️ Technologies Used

- **Python** (Pandas, NumPy, scikit-learn)  
- **FastAPI**  
- **Streamlit**  
- **PostgreSQL / SQLite**  
- **Docker & docker-compose**  
- **GitHub PR workflow**  
- **Figma** (roadmap & UI prototype)