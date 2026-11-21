# 🍜 NutriSnap – Real-Time Food Calorie & Macro AI

NutriSnap is an AI-powered nutrition assistant and PWA that classifies meals, predicts calories and macronutrients in real-time, and scales them to your portion size.

---

## ✨ Features

- **⚡ Live Camera Scanner:** Real-time camera viewfinder with continuous HUD frame analysis, optical reticle, and laser scan beam.
- **🧠 Dual MobileNetV2 Auto-Detection:** Automatically runs both the **Global (10 dishes)** and **Indian Cuisine (15 dishes)** models, compares raw logit scores, and selects the best prediction without requiring manual cuisine selection.
- **📊 Instant Nutrition & Macros:** Provides calories, protein, carbohydrates, and fat for 25 different dishes.
- **🍽️ Dynamic Portion Scaling:** Interactive `0.5×` (Half), `1.0×` (Regular), and `1.5×` (Large) portion multipliers that scale all macronutrients instantly in the UI.
- **📱 Mobile-First PWA:** Full Progressive Web App with offline caching, home-screen installation, notch/safe-area handling, and tactile haptic feedback.
- **🎨 Custom Design:** Dark obsidian glassmorphic UI with custom vector branding and zero external CSS/JS framework bloat.

---

## 🥗 Supported Dishes (25 Total)

- **Indian Cuisine (15):** Aloo Gobi, Aloo Matar, Biryani, Butter Chicken, Chana Masala, Chapati, Dal Makhani, Dal Tadka, Gulab Jamun, Jalebi, Naan, Palak Paneer, Paneer Butter Masala, Poha, Rasgulla.
- **Global & Fast Food (10):** Chicken Curry, Dumplings, French Fries, Fried Rice, Hamburger, Ice Cream, Omelette, Pizza, Ramen, Samosa.

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Lostshayan/NutriSnap.git
cd NutriSnap
```

### 2. Set up virtual environment & install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Run the application
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open your browser at [http://localhost:8000](http://localhost:8000).

---

## 📡 API Endpoints

- **`GET /`** – Serves the single-page PWA frontend.
- **`POST /predict`** – Accepts an image upload (`multipart/form-data` with `file`), runs dual-model inference, and returns top-3 predictions, confidence percentages, attached nutrition, and a low confidence flag.
