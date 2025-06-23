# Jamnesia Render Deployment Guide

## Quick Deploy to Render

### Step 1: Fork Repository
1. Fork this repository to your GitHub account
2. Clone your fork locally (optional)

### Step 2: Connect to Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select your forked `jamnesia` repository

### Step 3: Configure Service
Use these exact settings in Render:

**Basic Settings:**
- **Name**: `jamnesia` (or your preferred name)
- **Region**: Choose closest to your users
- **Branch**: `master`
- **Runtime**: `Python 3`

**Build & Deploy:**
- **Build Command**: 
  ```
  pip install -r requirements.txt && pip install gunicorn
  ```
- **Start Command**: 
  ```
  gunicorn --config gunicorn.conf.py app:app
  ```

**Advanced Settings:**
- **Auto-Deploy**: ✅ Yes (recommended)

### Step 4: Environment Variables
Add these environment variables in Render dashboard:

**Required:**
- `SECRET_KEY`: Generate a secure secret key
  ```bash
  # Generate a secure key (run locally):
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

**Optional:**
- `FLASK_ENV`: `production` (default)
- `DATABASE_URL`: `sqlite:///data/jamnesia.db` (default)

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait for build and deployment (3-5 minutes)
3. Visit your app at: `https://your-app-name.onrender.com`

## Alternative: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/jamnesia)

## Configuration Details

### Database
- Uses SQLite by default (perfect for small to medium apps)
- Data persists across deployments
- Automatic backups available with Render Pro

### Performance
- Single worker process (SQLite optimized)
- 120-second timeout for large replay generations
- Automatic health checks

### Security
- HTTPS enabled by default
- Secure secret key required
- No root access needed

## Post-Deployment

### Testing Your App
1. Visit your Render URL
2. Click "Create Sample Hand"
3. Test the replay functionality
4. Create custom hands via "Input Hand"

### Custom Domain (Optional)
1. Go to your service dashboard
2. Click "Settings" → "Custom Domains"
3. Add your domain and configure DNS

### Monitoring
- View logs in Render dashboard
- Set up health check notifications
- Monitor performance metrics

## Scaling Options

### Current Setup (Free/Starter)
- Single SQLite database
- One worker process
- Perfect for personal use and small teams

### Scaling Up (Paid Plans)
1. **Add PostgreSQL**:
   - Add PostgreSQL service in Render
   - Update `DATABASE_URL` environment variable
   - Increase workers in `gunicorn.conf.py`

2. **Add Redis** (future caching):
   - Add Redis service
   - Configure session storage
   - Enable background tasks

## Troubleshooting

### Common Issues

**Build Fails:**
- Check build logs in Render dashboard
- Verify `requirements.txt` is complete
- Ensure Python 3.11+ compatibility

**500 Error on Load:**
- Check if `SECRET_KEY` is set
- Verify database permissions
- Review application logs

**Slow Performance:**
- Consider upgrading to paid plan
- Add PostgreSQL for better concurrent access
- Optimize replay generation

### Getting Help
1. Check Render logs: Service → Logs
2. Test locally: `python app.py`
3. Verify config: Check environment variables

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | None | Flask secret key for sessions |
| `DATABASE_URL` | ❌ No | `sqlite:///data/jamnesia.db` | Database connection string |
| `FLASK_ENV` | ❌ No | `production` | Flask environment |
| `PORT` | ❌ No | Auto-set by Render | Application port |

## Cost Estimate

**Free Tier:**
- ✅ Perfect for testing and personal use
- ✅ HTTPS included
- ✅ Custom domains supported
- ⚠️ Spins down after 15 minutes of inactivity

**Starter Plan (~$7/month):**
- ✅ Always-on service
- ✅ No spin-down delays
- ✅ More CPU and memory
- ✅ Better for teams

## Next Steps

1. **Deploy your app** following the steps above
2. **Test thoroughly** with sample hands
3. **Share your URL** with teammates
4. **Consider PostgreSQL** when you need more concurrent users
5. **Set up monitoring** for production use

Happy deploying! 🚀