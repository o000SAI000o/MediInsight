
## 📁 Project Structure

```
MediInsight/
│
├── 📁 models/
│   ├── tumor_model.pkl
│   └── diabetes_model.pkl
│
├── 📁 static/
│   └── (optional: CSS, JS, images)
│
├── 📁 templates/
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── tumor_form.html
│   ├── tumor_result.html
│   ├── diabetes_form.html
│   ├── diabetes_result.html
│   └── admin_dashboard.html
│
├── 📁 streamlit/
│   └── dashboard.py  ← Your Streamlit app here
│
├── 📄 app.py          ← Your main Flask backend
├── 📄 users.db        ← SQLite database
├── 📄 requirements.txt
└── 📄 README.md       ← Project explanation
```

---

## 📄 Sample `README.md`

````markdown
# 🧠 MediInsight: Medical Prediction Web App

MediInsight is a secure medical prediction system that allows users to:
- Predict Tumor and Diabetes conditions
- Generate, view, and export reports
- Visualize predictions on dashboards (via Streamlit)
- Administer user and report management

---

## 🔧 Tech Stack

| Layer     | Tool / Library         |
|-----------|------------------------|
| Backend   | Flask + SQLAlchemy     |
| Frontend  | Jinja2 (Flask)         |
| Dashboard | Streamlit              |
| Database  | SQLite (users.db)      |
| Models    | Scikit-learn (Pkl files) |
| Security  | bcrypt for passwords   |
| Charts    | matplotlib / seaborn   |

---

## 🏗️ Project Structure

- `app.py`: Flask backend (auth, models, predictions)
- `streamlit/dashboard.py`: Interactive analytics dashboard
- `models/`: ML models in pickle format
- `templates/`: HTML pages for Flask
- `users.db`: SQLite DB for users and reports

---

## 🚀 Setup Instructions

1. **Clone Repo**
   ```bash
   git clone https://github.com/yourusername/MediInsight.git
   cd MediInsight
````

2. **Create Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run Flask App**

   ```bash
   python app.py
   ```

   Visit: [http://localhost:5050](http://localhost:5050)

5. **Run Streamlit Dashboard**

   ```bash
   streamlit run streamlit/dashboard.py
   ```

   Visit: [http://localhost:8501](http://localhost:8501)

---

## 🔒 Admin Credentials (Default)

| Username | Password |
| -------- | -------- |
| admin    | admin123 |

> Change these in `app.py` after first use for security.

---

## ✅ Features

* 🔐 Signup/Login with password hashing
* 📂 Report generation and export (PDF/CSV)
* 📈 Visual analytics with Streamlit
* 👨‍⚕️ Admin portal to manage users/reports
* 📧 Password reset via OTP (demo setup)

---

## 🧪 Future Improvements

* Add REST API for prediction via Flask
* Deploy to Heroku/Render/Streamlit Cloud
* Integrate email using SMTP or SendGrid
* Add more ML models (e.g. heart disease, etc.)

---

## 📜 License

This project is open-source and free to use under the MIT license.

````

---

## 📄 Sample `requirements.txt`

```txt
flask
flask_sqlalchemy
flask_bcrypt
joblib
matplotlib
seaborn
streamlit
pandas
fpdf
bcrypt
````

---

Would you like me to generate the `README.md` and `requirements.txt` files and place them in a ZIP format or show them as downloadable text?


### streamlit and flask role - 

Great question — let’s clarify the **roles of Flask vs Streamlit** in your current project and how login/navigation flow can be handled:

---

### 🔁 **Current Structure Overview**

| Technology    | Role                                                                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Flask**     | Main backend: handles user **authentication**, **prediction forms**, **report saving**, and **PDF/chart generation**.                    |
| **Streamlit** | Acts as a **visual, analytical dashboard**: allows users to **view reports**, **filter by type/result**, and see **interactive charts**. |

---

### 🎯 What Happens After Flask Login?

Right now in Flask:

* After login, users land on `/dashboard`, which renders `dashboard.html` with past reports.

---

### 🧠 How Streamlit Can Be Better Integrated

If you want **Streamlit to act as the dashboard**, here’s what we can do:

#### ✅ **Option 1: Show Dashboard Button (Recommended)**

* After login, users still land on Flask's `/dashboard`
* Add a **"View Interactive Dashboard"** button that redirects them to the Streamlit app (e.g., `http://localhost:8501`)

#### ✅ **Option 2: Redirect to Streamlit After Login**

* Instead of rendering `dashboard.html`, use:

  ```python
  return redirect("http://localhost:8501")
  ```
* This opens the Streamlit dashboard directly.

---

### 🔒 Note on Auth Integration

Flask handles login securely. Streamlit doesn’t natively support sessions like Flask, so:

* We **don’t rely on Streamlit for authentication**
* You pass the logged-in username from Flask to Streamlit via **query params** or **environment/session files**
  Example URL:
  `http://localhost:8501?user=Vishwajeet`

We already configured this in the `streamlit_dashboard.py` using query parameters.

---

### ✅ Summary

* **Flask**: Core engine, handles login, form submission, ML predictions
* **Streamlit**: Visual dashboard for logged-in users to explore results
* **Navigation Flow**: Login via Flask → Optionally redirect or open Streamlit dashboard

---
