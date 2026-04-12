# 🏋️‍♂️ Gym Management System

A web-based Gym Management System built using **Flask (Python)** to automate gym operations such as member management, trainer coordination, payments, and attendance tracking.

---

##Overview

The Gym Management System provides a centralized platform for managing gym activities efficiently. It replaces manual processes with a digital system that improves accuracy, security, and accessibility of records.

This project demonstrates practical skills in:

* Web application development (Flask)
* Database design and management
* Authentication and security
* CRUD operations

---

##Features

**Member Management**

  * Register, update, and delete members
  * Track membership details

**Trainer Management**

  * Add and manage trainers
  * Assign trainers to members

 **Payments & Subscriptions**

  * Record and monitor payments
  * Track subscription plans

 **Attendance Tracking**

  * Monitor member attendance

 **Authentication System**

  * Secure login/logout
  * Password hashing using Werkzeug

 **Reporting**

  * Basic system data insights

---

## Tech Stack

| Layer      | Technology            |
| ---------- | --------------------- |
| Backend    | Python (Flask)        |
| Frontend   | HTML, CSS, JavaScript |
| Database   | SQLite                |
| Security   | Werkzeug              |
| Versioning | Git & GitHub          |

---

## Project Structure

```bash
GYM-MANAGEMENT-SYSTEM/
│
├── app.py
├── database.py
├── templates/
├── static/
├── requirements.txt
└── README.md
```

---

## Installation & Setup

###  Clone the Repository

👉 https://github.com/simonmateli/GYM-MANAGEMENT-SYSTEM

```bash
git clone https://github.com/simonmateli/GYM-MANAGEMENT-SYSTEM.git
```

---

###  Navigate to the Project Folder

```bash
cd GYM-MANAGEMENT-SYSTEM
```

---

###  Install Dependencies

```bash
pip install -r requirements.txt
```

---

###  Run the Application

```bash
python app.py
```

---

###  Open in Browser

👉 http://127.0.0.1:5000/

---

## Authentication

The system uses **Werkzeug security utilities** for:

* Password hashing
* Secure login validation
* Session management

---

##  Testing

Testing includes:

* Functional testing of modules
* Form validation
* Authentication testing
* Database verification

---

##  Challenges

* Managing secure sessions in Flask
* Structuring SQLite database relationships
* Debugging routing and form handling

---

##  Solutions

* Implemented password hashing with Werkzeug
* Organized database operations in `database.py`
* Structured Flask routing and validation

---

##  Future Improvements

*  Mobile-friendly interface
*  M-Pesa / payment gateway integration
*  Advanced dashboard analytics
*  Cloud deployment (Render / Railway)
*  Notifications (Email/SMS)

---

##  References

* Flask Documentation → https://flask.palletsprojects.com/
* Python Documentation → https://docs.python.org/3/
* SQLite Documentation → https://www.sqlite.org/docs.html
* GitHub Documentation → https://docs.github.com/

---

##  Author

**Simon Mateli**

* GitHub Profile → https://github.com/simonmateli
* Project Repository → https://github.com/simonmateli/GYM-MANAGEMENT-SYSTEM

---

##  License

This project is licensed under the **MIT License**.

---

## Acknowledgements

* KCA University
* Lecturers and mentors
* Open-source community

---
