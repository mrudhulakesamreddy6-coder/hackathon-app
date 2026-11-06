# 📧 DisasterSync AI — Email Notification Setup Guide

> **Language:** Telugu + English Mixed (మీ సౌకర్యం కోసం రెండు భాషల్లో రాశాం)

---

## ✅ Email Notifications Work Avvanikossam — Step-by-Step Guide

DisasterSync AI real Gmail email send cheyyataniki **Gmail App Password** required.
Ee guide follow chesthe email notifications complete ga work avtayi.

---

## 🔐 Step 1 — 2-Step Verification Enable చేయండి

**Mandatory:** App Passwords use cheyyataniki 2-Step Verification enable cheyyali.

1. Mee Gmail account open cheyyandi: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. **"2-Step Verification"** option click cheyyandi
3. **"Get started"** click chesi steps follow cheyyandi
4. Mee phone number verify cheyyandi
5. 2-Step Verification **ON** ayye varaku complete cheyyandi

> ⚠️ **2-Step Verification OFF unte App Passwords option appear avvaadu.**

---

## 🔑 Step 2 — App Passwords Open చేయండి

1. ee link open cheyyandi: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Mee Gmail password enter chesi login cheyyandi
3. **App Passwords** page ki redirect avtundi

---

## ⚙️ Step 3 — App Password Generate చేయండి

1. **"Select app"** dropdown lo → **"Mail"** select cheyyandi
2. **"Select device"** dropdown lo → **"Windows Computer"** (or mee device) select cheyyandi
3. **"Generate"** button click cheyyandi
4. Google **16-character password** generate chesi show chestundi
5. Aa password **copy** cheyyandi (oka sari matrame show avutundi — save cheyyandi!)

```
Example format: abcd efgh ijkl mnop
(16 characters, spaces tho chupistundi — spaces tho include cheyyandi)
```

---

## 📁 Step 4 — .env File Lo Securely Store చేయండి

Project root lo `.env` file open cheyyandi (already create chesaru).
Below values fill cheyyandi:

```env
# Mee Gmail address
GMAIL_USER=yourgmail@gmail.com

# Google generate chesina 16-character App Password
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```

**Example only** — actual mee values fill cheyyandi.

---

## 🔒 Security Rules — Mandatory గా Follow చేయండి

| ❌ Cheyyakandi | ✅ Cheyyandi |
|---|---|
| Real password ni GitHub lo push cheyyakandi | `.env` file ni `.gitignore` lo add cheyyandi |
| Password ni chat/email lo share cheyyakandi | App Password matrame use cheyyandi (login password kaadu) |
| `.env` file ni public repository lo commit cheyyakandi | `.env.example` file matrame commit cheyyandi |
| Personal Gmail password use cheyyakandi | Google generate chesina App Password use cheyyandi |

---

## 📋 Complete .env File Example

```env
# Email Notifications
EMAIL_NOTIFICATIONS_ENABLED=true

# Gmail SMTP Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# Gmail Credentials (Primary - fill these)
GMAIL_USER=yourgmail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# Emergency Response Officer Email Addresses
OFFICER_EMAILS=your-officer@gmail.com
```

> ⚠️ **Actual password ni ikkada share cheyyakandi!**

---

## 🧪 Step 5 — Test Email Send చేయండి

1. DisasterSync AI Admin Dashboard open cheyyandi: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)
2. Header lo **"Test Email"** button click cheyyandi
3. Mee email address enter cheyyandi
4. **"Send Test Email"** button click cheyyandi
5. Result check cheyyandi:
   - ✅ **EMAIL SENT** — Configuration correct, emails work avutunnayi
   - ❌ **EMAIL FAILED** — `.env` file credentials check cheyyandi

---

## ❓ Troubleshooting (Problems Vasthe)

### "Authentication failed" error vasthe:
- 2-Step Verification enable chesaaro check cheyyandi
- App Password correct ga copy chesaaro verify cheyyandi
- `.env` file lo `GMAIL_USER` and `GMAIL_APP_PASSWORD` correct ga set chesaaro confirm cheyyandi
- Flask server restart cheyyandi: `python app.py`

### "Less secure app access" error vasthe:
- Ee option use cheyyakandi — App Password use cheyyandi (more secure)
- App Password already generate chesaro check cheyyandi

### App Passwords option show avvakapothe:
- 2-Step Verification enable chesaaro verify cheyyandi
- Google Workspace account use chestunnara? — Admin allow cheyyali

---

## 🚀 Quick Reference

```bash
# 1. .env file edit cheyyandi
notepad .env

# 2. Flask server restart cheyyandi
python app.py

# 3. Admin Dashboard open cheyyandi
# http://127.0.0.1:5000/dashboard

# 4. "Test Email" button click cheyyandi
```

---

*DisasterSync AI — AI-Powered Multi-Agent Disaster Response and Emergency Coordination System*  
*Email setup guide version 1.0*

