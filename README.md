# CryptoTracker

A web application built with Flask to track cryptocurrency investment movements in real time.

## Features

- Record BUY, SELL and TRADE transactions between fiat and cryptocurrencies
- Real-time price conversion via the CoinMarketCap API
- Portfolio status with invested capital, recovered amount and gain/loss
- Multi-user support with login and registration

## Requirements

- Python 3.10+
- CoinMarketCap API key (free plan at https://coinmarketcap.com/api/)

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/Regenzel/Final_project_KeepCoding.git
cd Final_project_KeepCoding
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure the API key**

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Then open `.env` and set your CoinMarketCap API key (get one for free at https://coinmarketcap.com/api/):

```
CMC_API_KEY=your_api_key_here
```

## Running the app

```bash
python app.py
```

The database is created automatically on first run. Open your browser at **http://127.0.0.1:5000**.

## Project structure

```
├── app.py                  # App entry point
├── controllers/
│   ├── auth.py             # Login, register, logout routes
│   └── main.py             # Movements, purchase and status routes
├── models/
│   ├── user.py             # User model
│   └── movement.py         # Movement model
├── services/
│   └── crypto_api.py       # CoinMarketCap API wrapper
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── purchase.html
│   ├── status.html
│   ├── login.html
│   └── register.html
└── requirements.txt
```
