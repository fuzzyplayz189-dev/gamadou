# 🤖 Sumo Bot — Enterprise Discord Bot

Vollständiger Discord Bot mit Ultra-Premium Ticket-System und nativem AutoMod.  
**Kein MongoDB nötig** — läuft sofort mit lokalen JSON-Dateien.

---

## 🚀 Schnellstart (3 Schritte)

### Schritt 1 — Pakete installieren
```bash
pip install -r requirements.txt
```

### Schritt 2 — .env Datei einrichten
```bash
copy .env.example .env
```
Dann `.env` öffnen und BOT_TOKEN eintragen:
```
BOT_TOKEN=dein_token_hier
```

### Schritt 3 — Bot starten
```bash
python main.py
```

Das war's! Der Bot startet ohne MongoDB oder irgendeine andere Datenbank.

---

## 📁 Daten-Speicherung

Der Bot speichert alle Daten automatisch im `data/` Ordner als JSON-Dateien.  
Jeder Server bekommt eine eigene Datei: `data/SERVER_ID.json`

**Optional MongoDB:** Wenn du MongoDB nutzen möchtest, füge `MONGODB_URI` in `.env` ein  
und installiere: `pip install motor pymongo`

---

## 🎮 Nach dem Start: Server einrichten

```
/setup wizard         — Alle Setup-Optionen anzeigen
/setup logging        — Log-Kanäle konfigurieren
/ticket panel         — Ticket-Panel erstellen
/automod setup        — AutoMod einrichten
```

**Tipp für schnelle Command-Registrierung:**  
Trage deine Server-ID als `DEV_GUILD_ID` in `.env` ein — dann sind Commands sofort verfügbar.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎫 Ticket-System | Panels, Kategorien, Claim, Transcripts (HTML/JSON/TXT), Bewertungen |
| 🛡️ AutoMod | Keyword-Filter, Mention-Spam, Spam, Profanity — alles native Discord API |
| 🔨 Moderation | Ban, Kick, Timeout, Warn, Clear, Lock, Slowmode, Rolle, Nickname |
| 📋 Logging | Nachrichten, Mitglieder, Voice, Kanäle, Rollen, AutoMod-Aktionen |
| 💾 Datenbank | JSON-Dateien (Standard) oder MongoDB (optional) |

---

## 📋 Alle Slash-Commands

`/ticket panel` `/ticket close` `/ticket claim` `/ticket add` `/ticket remove`  
`/ticket rename` `/ticket priority` `/ticket transcript` `/ticket stats` `/ticket history` `/ticket config`

`/automod list` `/automod create-keyword` `/automod create-mention-spam`  
`/automod create-spam` `/automod create-profanity` `/automod delete` `/automod enable` `/automod disable` `/automod setup`

`/ban` `/unban` `/kick` `/timeout` `/untimeout` `/warn` `/warnings` `/clearwarnings`  
`/clear` `/lock` `/unlock` `/slowmode` `/role` `/nickname` `/modlogs`

`/status` `/setup wizard` `/setup logging` `/setup category` `/setup view`  
`/botstats` `/serverinfo` `/userinfo`

---

## 🐳 Docker

```bash
docker-compose up -d
```

## 📦 PM2 (VPS)

```bash
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save && pm2 startup
```
