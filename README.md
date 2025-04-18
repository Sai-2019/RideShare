# 🚗 RideShare Platform

A web-based community ride-sharing application that connects drivers offering rides with passengers seeking transportation. Built using Django and PostgreSQL, the platform supports timezone-aware scheduling, real-time booking, and role-based functionalities.

Deployed on **Heroku**, the app enables cost-effective, eco-friendly commuting in local networks such as colleges or workspaces.

---

## 🔧 Features

- User Management
- Ride creation and booking
- Timezone-aware ride scheduling
- Secure user authentication
- Real-time booking management
- PostgreSQL database integration
- Deployed on Heroku
- Stripe-ready for future payments

---

## 🚀 Live Deployment

🌐 Visit: [https://share-ride-59508d741b28.herokuapp.com/](https://share-ride-59508d741b28.herokuapp.com/)

---

## 🛠️ Installation Guide

### Prerequisites

- Python 3.8+
- PostgreSQL
- Git
- Virtualenv (optional but recommended)

### Steps

1. **Clone the Repository**

   ```bash
    git clone https://github.com/yourusername/rideshare-platform.git
    ```
2. **Installtion & Setup Guide**
    ### Env Setup
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate
    ```
    ### Install libraries
    ```bash
    pip install -r requirements.txt
    ```

    ## Apply migrations
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

    ### Create a stripe account and add details in `Sai-2019/RideShare/carpool/settings.py`

    ### Run the aplication
    ```bash
    python manage.py runserver
    ```
    



