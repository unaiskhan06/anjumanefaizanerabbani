# Deployment Guide — Render + Neon + Cloudinary + UptimeRobot

All four services have free tiers. Total cost: **$0/month**.

> [!IMPORTANT]
> Do the steps **in order**. Later steps depend on values from earlier ones.

---

## Prerequisites

### 1. Push to GitHub

Make sure your code is in a GitHub repo (private is fine).  
Confirm [.gitignore](file:///e:/UNAIS%20KHAN/PROGRAMS/anjumanefaizanerabbani/.gitignore) already excludes `.env`, `db.sqlite3`, and `/media/` — it does ✅.

### 2. Check requirements

[requirements.txt](file:///e:/UNAIS%20KHAN/PROGRAMS/anjumanefaizanerabbani/requirements.txt) already has everything needed ✅:
- `gunicorn` — production WSGI server
- `whitenoise` — serves static files
- `psycopg[binary]` — Postgres driver
- `dj-database-url` — parses `DATABASE_URL`
- `cloudinary` + `django-cloudinary-storage` — media on Cloudinary
- `python-dotenv` — loads `.env` locally

### 3. Generate a production SECRET_KEY

Run this in PowerShell (inside the project venv):

```powershell
.\.venv\Scripts\python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Copy the output — you'll paste it into Render later.

---

## Step 1 — Cloudinary (image & audio storage)

1. Go to [cloudinary.com](https://cloudinary.com) → **Sign Up Free**
2. On the dashboard, find **API environment variable**  
   It looks like: `cloudinary://123456789012345:abcDEFghiJKLmno@your-cloud-name`
3. **Copy this entire string** — this is your `CLOUDINARY_URL`

> [!NOTE]
> **Free tier:** 25 GB storage, 25 GB bandwidth/month — more than enough for banners, gallery photos, and audio.

---

## Step 2 — Neon (PostgreSQL database)

1. Go to [neon.tech](https://neon.tech) → **Sign Up Free**
2. Create a project:
   - **Name:** `anjumanefaizanerabbani`
   - **Region:** `Asia Pacific (Singapore)` — closest to India
   - **Postgres version:** latest (default is fine)
3. After creation, copy the **Connection string** from the dashboard  
   It looks like: `postgresql://user:password@ep-xyz-123.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`

> [!WARNING]
> If the string ends with `&channel_binding=require`, **delete that part**. Keep only `?sslmode=require`.

> [!NOTE]
> **Free tier limits:**
> - 0.5 GB storage, 190 hours active compute/month
> - Auto-suspends after 5 minutes of inactivity (first request after sleep adds ~1–2 seconds)
> - This is fine — UptimeRobot pings `/robots.txt` which doesn't touch the database, so Neon sleeps between real visits

---

## Step 3 — Seed the database from your computer

Render's free plan has no shell, so run the one-time setup commands locally, pointed at the production database and Cloudinary.

Open **PowerShell** in the project folder with your venv active:

```powershell
# Set temporary environment variables (only for this PowerShell session)
$env:DATABASE_URL = "postgresql://...your Neon string..."
$env:CLOUDINARY_URL = "cloudinary://...your Cloudinary string..."
$env:DEBUG = "False"

# Create the tables
.\.venv\Scripts\python manage.py migrate

# Create your admin account
.\.venv\Scripts\python manage.py createsuperuser

# Load demo content (photos upload to Cloudinary because CLOUDINARY_URL is set)
.\.venv\Scripts\python manage.py seed_demo

# Import videos from the YouTube channel
.\.venv\Scripts\python manage.py import_channel
```

> [!TIP]
> Close this PowerShell window when done, so the production variables don't stay in your environment and accidentally affect local development.

Verify everything uploaded correctly:
- Check your Cloudinary dashboard — you should see uploaded images
- The Neon dashboard → **Tables** should show your Django tables with data

---

## Step 4 — Deploy on Render

### 4a. Create the web service

1. Go to [render.com](https://render.com) → **Sign Up** → **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `anjumanefaizanerabbani` (becomes `anjumanefaizanerabbani.onrender.com`) |
| **Region** | Singapore (closest to India) |
| **Instance Type** | **Free** |
| **Runtime** | Python |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| **Start Command** | `gunicorn config.wsgi:application` |

### 4b. Add environment variables

Under **Environment → Environment Variables**, add each of these:

```
SECRET_KEY=<the value you generated in Prerequisites step 3>
DEBUG=False
ALLOWED_HOSTS=anjumanefaizanerabbani.onrender.com
CSRF_TRUSTED_ORIGINS=https://anjumanefaizanerabbani.onrender.com
SITE_URL=https://anjumanefaizanerabbani.onrender.com
DATABASE_URL=<your Neon connection string>
CLOUDINARY_URL=<your Cloudinary API environment variable>
EMAIL_HOST_USER=anjumanefaizanerabbani@gmail.com
EMAIL_HOST_PASSWORD=<your Gmail app password>
DEFAULT_FROM_EMAIL=anjumanefaizanerabbani@gmail.com
CONTACT_NOTIFY_EMAIL=anjumanefaizanerabbani@gmail.com
YOUTUBE_CHANNEL_ID=UCXCmmzfyuAPh9OAzAVbIrVg,UCWRR-TOgsbtwb2Dq4rCItNA
```

> [!IMPORTANT]
> Replace `anjumanefaizanerabbani` with whatever name you actually chose in Render if it's different.

### 4c. Deploy

Click **Create Web Service**. The first build takes 3–5 minutes.

### 4d. Verify

- Open `https://anjumanefaizanerabbani.onrender.com` — the site should load with styling and images
- Go to `https://anjumanefaizanerabbani.onrender.com/manage/` — log in with the superuser from Step 3

---

## Step 5 — UptimeRobot (keep-alive monitor)

Render's free web service sleeps after 15 minutes of no traffic. A monitor prevents this.

1. Go to [uptimerobot.com](https://uptimerobot.com) → **Sign Up Free**
2. **Add New Monitor:**
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** `Anjuman Website`
   - **URL:** `https://anjumanefaizanerabbani.onrender.com/robots.txt`
   - **Monitoring Interval:** 5 minutes
3. Click **Create Monitor**

> [!TIP]
> **Why `/robots.txt` and not `/`?**
>
> The [robots_txt view](file:///e:/UNAIS%20KHAN/PROGRAMS/anjumanefaizanerabbani/core/views.py#L70-L72) only renders a simple template — it doesn't query the database.
> This keeps Render awake **without** waking Neon's database, preserving your free compute hours.
> The home page `/` runs database queries, which would keep Neon awake 24/7 and burn through the 190-hour monthly limit.

---

## Day-to-Day Operations

### Adding content

| Task | How |
|------|-----|
| Add/edit videos, events, gallery, settings | Use `/manage/` — no redeploy needed |
| Upload gallery photos or audio | Upload via `/manage/` — they go to Cloudinary automatically |
| Change code | Push to GitHub → Render auto-redeploys |

### Importing new YouTube uploads

Render's cron jobs aren't free, so run this manually from your computer when needed:

```powershell
$env:DATABASE_URL = "postgresql://...your Neon string..."
$env:CLOUDINARY_URL = "cloudinary://...your Cloudinary string..."

.\.venv\Scripts\python manage.py import_channel
```

Or use the **Bulk Import** page in `/manage/` → Videos → Bulk import links.

### Adding a custom domain (later)

1. Render → Settings → Custom Domains → add your domain
2. Update three env vars in Render:
   ```
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,anjumanefaizanerabbani.onrender.com
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   SITE_URL=https://www.yourdomain.com
   ```
3. Set DNS records at your domain registrar as Render instructs
4. Update the UptimeRobot URL to your custom domain

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **Bad Request (400)** | `ALLOWED_HOSTS` doesn't match your Render address exactly |
| **CSRF error on login** | Add `https://yourname.onrender.com` to `CSRF_TRUSTED_ORIGINS` |
| **No styling** | Check build log — `collectstatic` must run; `whitenoise` must be installed |
| **Database connection error** | Re-copy the Neon string; keep `?sslmode=require`; remove `&channel_binding=require` |
| **First load very slow** | Normal — Render or Neon was sleeping. UptimeRobot keeps Render awake, but Neon still sleeps between visits |
| **Neon "compute suspended"** | You've used the monthly 190 compute hours. The database resumes next billing cycle. Reduce pings or upgrade |
| **Images/audio not loading** | Check `CLOUDINARY_URL` is set correctly in Render env vars |
| **YouTube Error 153** | Already handled — [settings.py](file:///e:/UNAIS%20KHAN/PROGRAMS/anjumanefaizanerabbani/config/settings.py#L200) has `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"` |

---

## Free Tier Limits Summary

| Service | Key Limits | Notes |
|---------|-----------|-------|
| **Render** | 750 hours/month, auto-sleep after 15 min idle | UptimeRobot keeps it awake |
| **Neon** | 0.5 GB storage, 190 compute-hours/month | Sleeps after 5 min idle — this is good for staying under limits |
| **Cloudinary** | 25 GB storage, 25 GB bandwidth/month | Plenty for a community channel site |
| **UptimeRobot** | 50 monitors, 5-min interval | One monitor is all you need |

---

> [!CAUTION]
> **Never commit your `.env` file or paste secrets into your code.** All secrets go into Render's environment variables dashboard only.
