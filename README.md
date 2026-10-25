# Telegram Broadcast Bot

বটকে প্রাইভেটে যা পাঠাবেন (লেখা, PDF, গাইডলাইন, ছবি, ভিডিও, অ্যালবাম) তা নির্দিষ্ট সব গ্রুপ ও চ্যানেলে একসাথে পোস্ট হয়ে যাবে। ফরম্যাটিং ও ক্যাপশন অক্ষত থাকে, "Forwarded from" লেখা আসে না।

## সেটআপ
1. [@BotFather](https://t.me/BotFather) এ `/newbot` দিয়ে বট বানিয়ে টোকেন নিন।
2. [@userinfobot](https://t.me/userinfobot) থেকে নিজের User ID জানুন।
3. চালান:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env   # এরপর .env এ BOT_TOKEN ও ADMIN_IDS বসান
   python bot.py
   ```

## গ্রুপ/চ্যানেল যুক্ত করা
- **গ্রুপ:** বটকে গ্রুপে অ্যাড করে অ্যাডমিন করুন, তারপর গ্রুপে `/add` লিখুন।
- **চ্যানেল:** বটকে চ্যানেলের অ্যাডমিন করুন (Post Messages অনুমতি সহ), তারপর বটের প্রাইভেট চ্যাটে `/add @channelusername` বা `/add -100xxxxxxxxxx`।

## কমান্ড
| কমান্ড | কাজ |
|---|---|
| `/list` | যুক্ত সব গ্রুপ/চ্যানেল |
| `/remove <chat_id>` | তালিকা থেকে বাদ |
| `/myid` | নিজের ও চ্যাটের ID |

শুধু `ADMIN_IDS`-এ থাকা ব্যক্তিরাই পোস্ট বা তালিকা পরিবর্তন করতে পারবেন। প্রতিটি পোস্টের পর কতগুলো জায়গায় সফল হলো তার রিপোর্ট পাবেন।

বট সবসময় চালু রাখতে কোনো VPS, Railway, Render বা PythonAnywhere-এ `python bot.py` চালান।
