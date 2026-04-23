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

## 🚀 Deployment

This project is deployed on **Vercel** with automatic deployments on every push to `main`.

Webhook is set at:
```
https://importil-bot.vercel.app/webhook
```

---


*Private project — all rights reserved.*
