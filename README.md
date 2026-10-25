# 🤖 Personal AI Assistant (Claude)

WhatsApp, Telegram, Gmail, Messenger-এ আপনার হয়ে reply দেয়।

| অবস্থা | কী হয় |
|---|---|
| **Busy** | Claude নিজে reply পাঠিয়ে দেয়, আপনাকে Telegram "Saved Messages"-এ জানায় |
| **Free** | Reply draft হিসেবে Saved Messages-এ আসে → `/send 12`, `/edit 12 নতুন লেখা`, `/skip 12` |

- পুরো chat history (SQLite + প্রথমবার Telegram/Gmail থেকে পুরনো মেসেজ import) পড়ে context বুঝে reply দেয়।
- আপনি ফোন থেকে নিজে reply দিলে সেটাও history-তে যোগ হয়।
- Busy নির্ধারণ: `BUSY_HOURS` schedule, অথবা Saved Messages-এ `/busy`, `/free`, `/auto`, `/status`, `/drafts`।
- Model: `.env`-এ `CLAUDE_MODEL` = `claude-fable-5-1` / `claude-opus-5-5` / `claude-sonnet-5-5` (default, সাশ্রয়ী)।

## Setup
1. `cp .env.example .env` এবং মান বসান।
2. **Telegram**: my.telegram.org → API ID/Hash। প্রথমবার চালালে OTP চাইবে।
3. **Gmail**: Google Cloud Console → Gmail API enable → OAuth *Desktop* client → `credentials.json`। প্রথমবার browser-এ login (লোকালি চালিয়ে `data/gmail_token.json` তৈরি করে server-এ কপি করুন)।
4. **WhatsApp / Messenger**: Meta Developer app → webhook URL `https://<your-domain>/webhook`, verify token = `META_VERIFY_TOKEN`।
5. চালান:
   ```bash
   pip install -r requirements.txt && python -m assistant.main      # লোকাল
   docker compose up -d --build                                    # 24/7 (VPS-এ)
   ```
   24 ঘণ্টা চালাতে একটি VPS (DigitalOcean/Hetzner/AWS Lightsail ~$5/মাস) ব্যবহার করুন; `restart: always` crash/reboot-এ আবার চালু করে।

## ⚠️ গুরুত্বপূর্ণ সীমাবদ্ধতা
- **WhatsApp**: অফিসিয়াল Cloud API শুধু একটি *Business নম্বরে* কাজ করে (আলাদা নম্বর লাগবে), ব্যক্তিগত WhatsApp নয়। ব্যক্তিগত নম্বরের জন্য whatsapp-web.js / Baileys-এর মতো unofficial লাইব্রেরি আছে, কিন্তু তাতে নম্বর ban হওয়ার ঝুঁকি আছে। এছাড়া ২৪ ঘণ্টার বেশি পুরনো conversation-এ শুধু template message পাঠানো যায়, আর API দিয়ে পুরনো chat history পাওয়া যায় না (bot চালু হওয়ার পর থেকে জমা হয়)।
- **Messenger**: Meta শুধু *Facebook Page*-এর inbox-এর জন্য API দেয়; ব্যক্তিগত প্রোফাইলের Messenger automate করার কোনো অফিসিয়াল উপায় নেই।
- **Telegram**: আপনার নিজের account (userbot) ব্যবহার হয় — সবচেয়ে ভালোভাবে কাজ করে, পুরো history সহ।
- AI টাকা/মিটিং/OTP নিয়ে কোনো প্রতিশ্রুতি দেবে না, "পরে জানাবো" বলবে।
