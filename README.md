# ANJUMANEFAIZANERABBANI — Website

**Anjuman-e-Faizan-e-Rabbani · انجمنِ فیضانِ ربانی · Chennai**

This is the official website for the ANJUMANEFAIZANERABBANI YouTube channel. Videos play right on the site
through embedded YouTube players. You add new videos yourself in a private admin panel: paste a YouTube
link and click **Save**. You don't need to change any code or redeploy.

It works on phones, tablets, laptops and desktop computers, and it has a dark mode.

---

## Contents

1. [What's inside](#1-whats-inside)
2. [Run it on your computer (step by step)](#2-run-it-on-your-computer)
3. [Using the admin panel](#3-using-the-admin-panel)
4. [Importing videos automatically from the channel](#4-importing-videos-from-the-channel)
5. [Deploying to the internet](#5-deploying-to-the-internet)
6. [Custom domain and HTTPS](#6-custom-domain-and-https)
7. [Project structure](#7-project-structure)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. What's inside

| Page | URL |
|---|---|
| Home: hero slider, weekly schedule, category chips and video rows | `/` |
| Categories / single category | `/categories/`, `/category/<slug>/` |
| Video page with the player | `/video/<category>/<video>/` |
| All videos (filter by type) | `/videos/?type=short` |
| Popular | `/popular/` |
| Playlists | `/playlists/` |
| Events | `/events/` |
| Audio player | `/audio/` |
| Photo gallery | `/gallery/` |
| Search, plus live suggestions | `/search/?q=` |
| About | `/about/` |
| Contact | `/contact/` |
| **Admin panel (private)** | **`/manage/`** |
| Sitemap / robots | `/sitemap.xml`, `/robots.txt` |

Tech: Python 3.11+, Django 5.2, plain HTML/CSS/vanilla JavaScript, SQLite locally, PostgreSQL in
production, WhiteNoise for static files and optional Cloudinary for uploaded media.

---

## 2. Run it on your computer

You need **Python 3.11 or newer**. Download it from <https://www.python.org/downloads/>. On Windows, tick
"Add Python to PATH" during setup.

Open a terminal (Windows: *PowerShell*) inside the project folder, then follow these steps.

### Step 1: Create a virtual environment

```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\activate
```
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```
Once it's active, your prompt starts with `(.venv)`.

### Step 2: Install the requirements

```bash
pip install -r requirements.txt
```

### Step 3: Configure `.env`

Copy the example file:

```powershell
copy .env.example .env        # Windows
```
```bash
cp .env.example .env          # macOS / Linux
```

Open `.env` in a text editor and set `SECRET_KEY` to a long random value. You can generate one like this:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

For local development, keep `DEBUG=True` and leave `DATABASE_URL` empty so the site uses SQLite.

### Step 4: Create the database tables

```bash
python manage.py migrate
```

### Step 5: Create your admin account

```bash
python manage.py createsuperuser
```

Choose a username and a **strong password** (at least 10 characters).

### Step 6: Load the demo content

```bash
python manage.py seed_demo
```

This creates:

- 6 categories (Naat Sharif, Hamd, Bayan, Tasawwuf, Kids Special, Quran o Hadees)
- 12 real videos from the channel
- 3 hero banners, made from the photos in `asserts/home page images`
- 2 events and 5 playlist links
- the site settings (committee phone numbers, email, WhatsApp, About text)
- every photo in `asserts/gallery`, resized automatically

Add `--no-gallery` to skip the photos. You can run the command more than once; it never creates duplicates.

> The weekly schedule, About/Mission/Vision text and the category assigned to each demo video are
> **examples**. Change them under **/manage/ → Site settings** and **Videos**.

### Step 7: Start the server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

**Test it on your phone:** connect the phone to the same Wi-Fi, then run
`python manage.py runserver 0.0.0.0:8000`. Add your computer's IP address (for example `192.168.1.5`) to
`ALLOWED_HOSTS` in `.env`, and open `http://192.168.1.5:8000` on the phone.

### Step 8: Run the automated tests (optional)

```bash
python manage.py test
```

---

## 3. Using the admin panel

Open **<http://127.0.0.1:8000/manage/>** and log in with the account from Step 5.
The usual `/admin/` address is switched off on purpose.

### Add your first category

1. Go to **Videos → Categories → Add**.
2. Type a **Name** (for example "Manqabat") and, if you like, a **Name (Urdu)**.
3. Leave **Slug** empty; it's created for you.
4. Click **Save**.

To change the order categories appear in, edit the **Sort order** numbers in the list (lower numbers come
first) and click **Save**.

### Add a video (takes about 10 seconds)

1. Go to **Videos → Videos → Add video**.
2. Paste the YouTube link into **YouTube link**. All of these formats work:
   - `https://www.youtube.com/watch?v=XXXXXXXXXXX`
   - `https://youtu.be/XXXXXXXXXXX`
   - `https://www.youtube.com/shorts/XXXXXXXXXXX` (automatically set as a vertical *Short*)
   - `https://www.youtube.com/live/XXXXXXXXXXX`
   - an embed link, or just the 11-character ID

   A thumbnail and player preview appear straight away.
3. Choose a **Category**.
4. Click **Save**. If you left the title empty, it's fetched from YouTube for you.

The video appears on the home page, in its category, in search and in the sitemap **immediately**.

- A link that isn't a YouTube link is rejected with a clear message.
- A video you've already added is also rejected, and the message tells you which existing video it matches.
- Tick **Live** while you're streaming. A red "LIVE NOW" strip then appears on the home page. Untick it
  when the stream ends.
- Tick **Featured** to put a video at the top of the Popular page.
- Untick **Published** to hide a video while you prepare it.

### Bulk import (many videos at once)

1. Go to **Videos → Videos → Bulk import links** (button at the top right).
2. Paste one YouTube link per line.
3. Choose a category and type, then click **Import videos**.
4. The result page lists what was created, which lines were duplicates and which lines weren't valid.

### Bulk actions

In the video list, tick some videos and choose **Publish**, **Unpublish** or **Mark as featured** from the
*Action* menu.

### Other screens

| Screen | What it controls |
|---|---|
| Website settings → **Hero banners** | Home page slider: image, title, label, link, order, on/off |
| Website settings → **Playlists & channel links** | Cards on `/playlists/` |
| Website settings → **Announcements** | Landscape posters (ideally 1600 × 900) above the category chips on the home page. Optional link and "show until" date; the section is hidden when there are none |
| Website settings → **Partner YouTube channels** | Extra "Also subscribe to…" banners on the home page (e.g. Ahmed Raza Rabbani) |
| Website settings → **Site settings** | Phones, email, WhatsApp, social links, address, map, weekly schedule, About/Mission/Vision |
| Events → **Events** | Upcoming and past events, posters, "Watch Live" link |
| Gallery & Audio → **Gallery images** | Photos on `/gallery/` |
| Gallery & Audio → **Audio tracks** | MP3/M4A files for the `/audio/` player |
| Contact messages | Messages sent from the contact form. Opening a message marks it as read. |

---

## 4. Importing videos from the channel

The channel ID is already in `.env.example`: `YOUTUBE_CHANNEL_ID=UCXCmmzfyuAPh9OAzAVbIrVg`.

```bash
python manage.py import_channel
```

This reads the channel's public RSS feed, which lists the 15 most recent uploads. Any upload that isn't on
the site yet is added as an **unpublished draft**. Afterwards, go to **/manage/ → Videos**, filter by
*Published: No*, check each video's category, then use **Publish selected videos**.

It also reads your channel's **Shorts** playlist. Shorts are saved with the type *Short* in a
"Shorts" category and appear in the home page **YouTube Shorts** row, played in a vertical 9:16 player.

Options:

```bash
python manage.py import_channel --category bayan    # put new videos in the "bayan" category
python manage.py import_channel --publish           # publish immediately (skip review)
python manage.py import_channel --only-shorts --publish   # just bring in the latest Shorts
python manage.py import_channel --no-shorts         # skip Shorts
```

You can run it automatically once a day (see "Scheduled task" in the PythonAnywhere section below).

---

## 5. Deploying to the internet

### Checklist for production `.env`

```ini
SECRET_KEY=<a new long random value>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SITE_URL=https://yourdomain.com
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
EMAIL_HOST_USER=anjumanefaizanerabbani@gmail.com
EMAIL_HOST_PASSWORD=<Gmail app password>
DEFAULT_FROM_EMAIL=anjumanefaizanerabbani@gmail.com
CONTACT_NOTIFY_EMAIL=anjumanefaizanerabbani@gmail.com
YOUTUBE_CHANNEL_ID=UCXCmmzfyuAPh9OAzAVbIrVg
```

When `DEBUG=False`, the site automatically turns on:

- the HTTPS redirect
- HSTS (1 year)
- secure, HttpOnly cookies
- nosniff headers
- clickjacking protection

**Cloudinary (recommended for uploaded images and audio):** create a free account at
<https://cloudinary.com>. Copy the **API environment variable** (`cloudinary://...`) from the dashboard into
`CLOUDINARY_URL`. Banners, gallery photos, posters and audio files are then stored on Cloudinary and survive
redeploys.

**Gmail notifications:** turn on 2-Step Verification, then go to Google Account → Security → *App passwords*,
create one, and paste it into `EMAIL_HOST_PASSWORD`.

Every deployment runs the same commands:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser      # first time only
python manage.py seed_demo --no-gallery   # optional, first time only
```

### Option A: PythonAnywhere

1. Create an account at <https://www.pythonanywhere.com>. A paid plan is needed for custom domains and
   PostgreSQL. The free plan works with SQLite on `yourname.pythonanywhere.com`.
2. Open a **Bash console** and upload the code, either with `git clone <your repo>` or by uploading a zip
   under *Files*.
3. Set up a virtual environment:
   ```bash
   cd ~/anjumanefaizanerabbani
   python3.11 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env && nano .env      # fill in the production values
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
4. **Web** tab → *Add a new web app* → *Manual configuration* → Python 3.11.
   - **Virtualenv:** `/home/<you>/anjumanefaizanerabbani/.venv`
   - **WSGI file:** replace its contents with:
     ```python
     import os, sys
     path = "/home/<you>/anjumanefaizanerabbani"
     if path not in sys.path:
         sys.path.insert(0, path)
     os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```
   - **Static files:** URL `/static/` → directory `/home/<you>/anjumanefaizanerabbani/staticfiles`
   - **Media files** (only if you're not using Cloudinary): URL `/media/` → directory
     `/home/<you>/anjumanefaizanerabbani/media`
   - Turn on **Force HTTPS**.
5. **PostgreSQL:** on the *Databases* tab, create a Postgres server and put its details into `DATABASE_URL`.
6. Click **Reload**.
7. **Scheduled task** (optional): on the *Tasks* tab, add a daily task:
   `/home/<you>/anjumanefaizanerabbani/.venv/bin/python /home/<you>/anjumanefaizanerabbani/manage.py import_channel`

### Option B: Render

1. Push the code to GitHub.
2. On <https://render.com>, create a **PostgreSQL** database and copy its *Internal Database URL*.
3. Create a **Web Service** from your repo:
   - **Build command:**
     `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start command:** `gunicorn config.wsgi:application`
   - **Environment:** add every variable from the checklist above. Set `DATABASE_URL` to the database URL.
     Add `yourapp.onrender.com` to `ALLOWED_HOSTS` and `https://yourapp.onrender.com` to
     `CSRF_TRUSTED_ORIGINS`.
4. Render's disk is temporary, so **use Cloudinary** for media.
5. Open the **Shell** tab once and run `python manage.py createsuperuser`.
6. **Cron** (optional): add a Cron Job that runs `python manage.py import_channel`.

### Option C: Railway

1. On <https://railway.app>, create a new project from your GitHub repo and add the **PostgreSQL** plugin.
2. In the service **Variables**, add the checklist variables. Railway provides `DATABASE_URL`; you can
   reference it as `${{Postgres.DATABASE_URL}}`.
3. **Custom start command:**
   `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
4. Use Cloudinary for media, and run `createsuperuser` from the service shell.

---

## 6. Custom domain and HTTPS

1. Buy a domain, for example from GoDaddy, Namecheap, Hostinger or Google Domains resellers.
2. On your host:
   - **PythonAnywhere:** *Web* tab → add a web app for `www.yourdomain.com`. Note the CNAME value it shows
     (`webapp-XXXX.pythonanywhere.com`).
   - **Render / Railway:** *Settings → Custom Domains* → add `yourdomain.com` and `www.yourdomain.com`. Note
     the DNS records they give you.
3. At your domain registrar's **DNS** settings:
   - `CNAME` record: `www` → the value from step 2
   - For the bare domain (`yourdomain.com`), use the `A`/`ALIAS` record your host gives you, or set up a
     redirect from `yourdomain.com` to `www.yourdomain.com`.
4. Wait for DNS to update. This usually takes minutes, but can take up to 24 hours.
5. Turn on HTTPS:
   - **PythonAnywhere:** *Web* tab → *HTTPS certificate* → **Auto-renewing Let's Encrypt**, then turn on
     **Force HTTPS**.
   - **Render / Railway:** certificates are issued automatically.
6. Update `.env`:
   - `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
   - `CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`
   - `SITE_URL=https://www.yourdomain.com`

   Then reload or redeploy.
7. Submit `https://www.yourdomain.com/sitemap.xml` in Google Search Console.

---

## 7. Project structure

```
config/          settings.py (reads .env), urls.py (/manage/ admin, sitemap, robots), wsgi/asgi
core/            SiteSetting, Banner, PlaylistLink · home/about/playlists · seed_demo · sitemaps · cache signals
videos/          Category, Video · YouTube helpers · views · admin (preview, bulk import) · import_channel
events/          Event model and page
gallery/         GalleryImage, AudioTrack · gallery and audio pages
contact/         ContactMessage · form with honeypot, rate limit and email notification
templates/       base.html, partials (_card, _pager, _hero_slider, _video_row…), pages, 404/500, admin overrides
static/css/      style.css (responsive, dark mode, RTL-safe)
static/js/       main.js, player.js, slider.js, audio.js, lightbox.js, search.js, admin_video.js
static/img/      logo.png, logo-sm.png, favicon.png, apple-touch-icon.png, og-default.jpg
asserts/         your original photos and logo (used by seed_demo)
```

**Replacing the logo:** overwrite `static/img/logo.png` (512×512) and `static/img/logo-sm.png` (160×160)
with square PNGs, then run `collectstatic` again in production.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `SECRET_KEY must be set` | Create `.env` (Step 3) and set `SECRET_KEY`. |
| "Bad Request (400)" in production | Add your domain to `ALLOWED_HOSTS`. |
| "CSRF verification failed" when logging in | Add `https://yourdomain.com` to `CSRF_TRUSTED_ORIGINS`. |
| Page has no styling in production | Run `python manage.py collectstatic --noinput` and reload. |
| Video shows "Error 153" | Keep `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"` in settings. YouTube needs it. |
| Title shows "Video XXXXXXXXXXX" | YouTube couldn't be reached while saving. Type the title by hand. |
| Uploaded images disappear after a redeploy | Set `CLOUDINARY_URL` (Render and Railway disks are temporary). |
| Contact emails are not arriving | Check `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` (use a Gmail *app password*) and `CONTACT_NOTIFY_EMAIL`. Messages are always saved in the admin, even if email fails. |

---

© ANJUMANEFAIZANERABBANI — Anjuman-e-Faizan-e-Rabbani. All videos, audio and images belong to the channel.
