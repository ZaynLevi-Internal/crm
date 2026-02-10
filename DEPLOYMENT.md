# Deployment Guide - Render + Supabase (100% FREE)

## Step 1: Setup Supabase (PostgreSQL Database)

1. Go to https://supabase.com
2. Sign up (free, no card required)
3. Click "New Project"
   - Name: `ca-crm-db`
   - Database Password: Create a strong password (SAVE THIS!)
   - Region: Choose closest to you
4. Wait 2 minutes for database to be ready
5. Go to Project Settings → Database
6. Copy the "Connection String" (URI format)
   - It looks like: `postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres`
   - Replace `[PASSWORD]` with your actual password
7. **SAVE THIS CONNECTION STRING!**

## Step 2: Push Code to GitHub

1. Create a GitHub account (if you don't have one)
2. Create a new repository: `ca-crm`
3. In WSL terminal, run:

```bash
cd /mnt/c/Users/rf823/Projects/Chand/CRM
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ca-crm.git
git push -u origin main
```

## Step 3: Deploy on Render

1. Go to https://render.com
2. Sign up (free, no card required)
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select your `ca-crm` repository
6. Configure:
   - **Name**: `ca-crm`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`

7. Add Environment Variables:
   - Click "Advanced" → "Add Environment Variable"
   - Add these:
     ```
     DATABASE_URL = [Your Supabase connection string from Step 1]
     SECRET_KEY = [Generate random string like: mysecretkey12345]
     ```

8. Click "Create Web Service"
9. Wait 5-10 minutes for deployment

## Step 4: Access Your App

- Your app will be live at: `https://ca-crm.onrender.com`
- Login: `admin` / `admin123`

## Important Notes:

- **Free tier sleeps after 15 minutes of inactivity** (first request takes 30 seconds to wake up)
- Database stays active
- Change admin password after first login!

## Troubleshooting:

If deployment fails:
1. Check logs in Render dashboard
2. Verify DATABASE_URL is correct
3. Ensure all files are pushed to GitHub

## To Update Your App:

Just push changes to GitHub:
```bash
git add .
git commit -m "Update"
git push
```

Render auto-deploys in 2-3 minutes!
