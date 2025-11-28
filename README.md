# 📊 Dynamic Pricing for Yerevan Cafés & Restaurants  
### **DS223 — Marketing Analytics (Milestone 3)**  
### American University of Armenia

This repository contains **Milestone 3** of the team project *Dynamic Pricing in Yerevan*, developed for **DS223 – Marketing Analytics**, under the supervision of **Instructor Karen Hovhannisyan**.

The project implements a complete **service-based architecture** for predicting and forecasting menu item prices for Yerevan restaurants, including a CatBoost ML model, ETL pipelines, API services, and an interactive Streamlit UI.

---

# 🚀 Milestone 3 Summary

Milestone 3 connects all components of the system and delivers a fully working end-to-end pipeline across **Database**, **ETL**, **Data Science**, **Backend**, and **Frontend** services.

##  Data Science (DS)
- Built the **final CatBoost regression model** for price prediction  
- Implemented forecasting for menu items (short-term projections)  
- Exported clean model outputs for backend consumption  
- Delivered final DS work to the `ds` branch  

##  Backend (FastAPI)
- Implemented all API endpoints defined by PM specifications  
- Added **Pydantic request/response models**  
- Connected the CatBoost model outputs to `/predict-price` and `/forecast-price`  
- Added docstrings and internal documentation  
- Delivered backend work to the `backend` branch  

##  Database (DB)
- Finalized the ERD and updated the database schema  
- Added complete table definitions and descriptions  
- Enabled clean ingestion of restaurant/menu datasets  
- Delivered DB work to the `db` branch  

##  Frontend (Streamlit)
- Updated the full UI based on PM requirements  
- Added **prediction + forecasting pages** with redesigned layouts  
- Integrated API responses into user-friendly UI components  
- Applied consistent **dark green theme** across the application  
- Delivered final UI work to the `front` branch  

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