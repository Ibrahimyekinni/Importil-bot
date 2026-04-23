# 🤖 Importil — AI Customs Compliance Bot

> An AI-powered Telegram bot that acts as a Customs Compliance Officer for Israeli importers of wireless communication equipment.

[![Live Bot](https://img.shields.io/badge/Telegram-@Dekel__Importil__bot-blue?logo=telegram)](https://t.me/Dekel_Importil_bot)
[![Dashboard](https://img.shields.io/badge/Dashboard-importil--bot.vercel.app-black?logo=vercel)](https://importil-bot.vercel.app)
[![License](https://img.shields.io/badge/license-Private-red)]()

---

## 📌 What It Does

Users send a product to the bot — via photo, product name, AliExpress/Amazon link, or PDF/DOCX spec sheet — and get an instant professional compliance verdict on whether it can be imported into Israel.

The bot checks against:
- Israeli Ministry of Communications frequency regulations
- Banned frequency ranges (e.g. 5.8GHz hard stop)
- Whitelist/exemption categories
- Import track classification (private vs. commercial, quantity limits)

Verdicts: ✅ **ALLOWED** · ⚠️ **CONDITIONAL** · ❌ **PROHIBITED** · 🟢 **EXEMPT**

---

## ✨ Features

### Telegram Bot
- Subscription-based access with admin approval system
- Supports: photo, text, URL, PDF, DOCX inputs
- Track classification — private/company importer + quantity decision matrix
- Whitelist/exemption check with regulatory reference
- Frequency normalization (e.g. "WiFi" → 2400–2483.5 MHz, EN 300 328)
- 5.8GHz hard stop warning
- **Conversation memory** — after a verdict, users can ask follow-up questions and the bot answers in full context without restarting
- Long responses split into natural message chunks — never mid-sentence
- Typing indicator + clean processing state UX
- Bilingual — English 🇬🇧 and Hebrew 🇮🇱
- Commands: `/start` `/link` `/language` `/help` `/refresh` `/status`
- Admin gets Telegram notification on every new user registration

### Admin Dashboard (importil-bot.vercel.app)
- Premium dark fintech UI
- User management — approve/revoke with instant Telegram notification
- User notes with auto-save
- Full query history with color-coded verdict badges
- Search & filter by verdict, date, text
- CSV export
- Settings page

### AI Brain
- Groq AI — `llama-3.3-70b` for text, `llama-4-scout` for vision
- Google Drive document caching for knowledge base
- Dedicated follow-up query function — treats prior verdict as settled fact, answers conversationally
- Israeli frequency regulation rules hardcoded into system prompt
- Language-aware responses

---

## 🛠 Tech Stack

| Component      | Tool                                  |
|----------------|---------------------------------------|
| Bot Framework  | python-telegram-bot                   |
| AI Model       | Groq (llama-3.3-70b + llama-4-scout)  |
| URL Scraping   | Firecrawl API                         |
| Knowledge Base | Google Drive API                      |
| Database       | Neon DB (PostgreSQL)                  |
| Dashboard      | Flask (Python)                        |
| Hosting        | Vercel (serverless)                   |
| Version Control| GitHub                                |

---

## 🗄️ Database Schema

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  telegram_username VARCHAR(255),
  email VARCHAR(255),
  approved BOOLEAN DEFAULT FALSE,
  language VARCHAR(5) DEFAULT 'en',
  linked_at TIMESTAMP DEFAULT NOW(),
  approved_at TIMESTAMP,
  conv_state VARCHAR(50) DEFAULT NULL,
  conv_data TEXT DEFAULT NULL,
  notes TEXT DEFAULT NULL
);

CREATE TABLE queries (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL,
  query_type VARCHAR(10) NOT NULL,
  query_content TEXT,
  verdict VARCHAR(20),
  full_response TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## ⚙️ Environment Variables

```env
TELEGRAM_BOT_TOKEN=
GROQ_API_KEY=
FIRECRAWL_API_KEY=
GOOGLE_DRIVE_FOLDER_ID=
GOOGLE_SERVICE_ACCOUNT_JSON=
DATABASE_URL=
ADMIN_TELEGRAM_ID=
DASHBOARD_PASSWORD=
```

---

## 🚀 Deployment

This project is deployed on **Vercel** with automatic deployments on every push to `main`.

Webhook is set at:
```
https://importil-bot.vercel.app/webhook
```

> ⚠️ **Vercel Serverless Gotcha:** Telegram files cannot be re-downloaded after the initial request. All files (photos, PDFs) must be downloaded and stored as base64 immediately when they arrive. Never attempt to re-download by file_id in a later handler.

---

## 🧠 Architecture Notes

- **Single `get_user()` DB call per message** — never split into multiple DB calls per message (Neon cold-start latency will drop connections)
- **State routing is strict `if/elif/else`** — never separate `if` blocks. `AWAITING_FOLLOWUP` is always checked first
- **`conv_data` is a TEXT column** — always JSON serialize/deserialize
- **Follow-up responses** use `analyze_followup_query()` — NOT `analyze_text_query()`. This skips compliance re-analysis and answers conversationally
- **`split_message()`** helper in `track.py` — splits long responses at natural boundaries (paragraph → sentence). Use for any long response

---

## 📋 Pending Features

- [ ] Blacklist check — requires `rejected_items.csv` from client
- [ ] Golden Path — affidavit auto-fill after ALLOWED/CONDITIONAL verdict
- [ ] Gov.il form automation — conversational field collector

---

## 📁 Project Structure

```
/
├── bot/
│   ├── handlers/
│   │   ├── track.py          # Main message handler + state machine
│   │   ├── check.py          # Text/URL/photo compliance checks
│   │   ├── document_check.py # PDF/DOCX handler
│   │   └── refresh.py        # /refresh command
│   ├── services/
│   │   └── ai_service.py     # Groq AI calls + prompt logic
│   ├── messages.py           # Bilingual message strings
│   └── db.py                 # Neon DB helpers
├── dashboard/                # Flask admin dashboard
├── api/
│   └── webhook.py            # Vercel serverless entry point
└── vercel.json
```

---

---

*Private project — all rights reserved.*
