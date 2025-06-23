# Jamnesia Deployment Guide

## Quick Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Git

### Single Command Deployment

```bash
# Clone and deploy
git clone <repository-url>
cd jamnesia
docker-compose up -d
```

Visit `http://localhost:8000` to access the application.

## Production Deployment

### Environment Variables

Create a `.env` file:

```bash
SECRET_KEY=your-very-secure-secret-key-here
DATABASE_URL=sqlite:///data/jamnesia.db
FLASK_ENV=production
```

### Docker Build and Run

```bash
# Build the image
docker build -t jamnesia .

# Run with volume for persistent data
docker run -d \
  --name jamnesia \
  -p 8000:8000 \
  -v jamnesia_data:/app/data \
  -e SECRET_KEY=your-secret-key \
  jamnesia
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update and restart
git pull
docker-compose build
docker-compose up -d
```

## Cloud Platform Deployment

### Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use the following settings:
   - **Build Command**: `pip install -r requirements.txt && pip install gunicorn`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 app:app`
   - **Environment Variables**:
     - `SECRET_KEY`: Your secure secret key
     - `DATABASE_URL`: `sqlite:///data/jamnesia.db`

### Railway

1. Connect your GitHub repository
2. Deploy from the repository
3. Add environment variables:
   - `SECRET_KEY`: Your secure secret key
   - `DATABASE_URL`: `sqlite:///data/jamnesia.db`

### Heroku

```bash
# Create app
heroku create your-jamnesia-app

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key

# For PostgreSQL (recommended on Heroku)
heroku addons:create heroku-postgresql:mini
# This automatically sets DATABASE_URL

# Deploy
git push heroku master
```

## Future PostgreSQL Migration

When ready to scale, uncomment the PostgreSQL section in `docker-compose.yml`:

1. **Stop current services**:
   ```bash
   docker-compose down
   ```

2. **Export current SQLite data** (if needed):
   ```bash
   # Export sample commands - adjust based on your needs
   docker run --rm -v jamnesia_data:/data alpine \
     cp /data/jamnesia.db /data/backup.db
   ```

3. **Update configuration**:
   - Uncomment PostgreSQL service in `docker-compose.yml`
   - Update Dockerfile workers: `--workers 2`
   - Set `DATABASE_URL` to PostgreSQL connection string

4. **Start with PostgreSQL**:
   ```bash
   docker-compose up -d postgres
   docker-compose up -d jamnesia
   ```

## Monitoring and Maintenance

### Health Checks

The application includes built-in health checks:
- Docker health check: `curl -f http://localhost:8000/`
- Manual check: `docker-compose ps`

### Logs

```bash
# View application logs
docker-compose logs jamnesia

# Follow logs in real-time
docker-compose logs -f jamnesia
```

### Database Backup (SQLite)

```bash
# Backup current database
docker run --rm -v jamnesia_data:/data -v $(pwd):/backup alpine \
  cp /data/jamnesia.db /backup/jamnesia-backup-$(date +%Y%m%d).db
```

### Updates

```bash
# Update application
git pull
docker-compose build jamnesia
docker-compose up -d jamnesia
```

## Security Considerations

1. **Change the SECRET_KEY** in production
2. **Use HTTPS** in production (configure reverse proxy)
3. **Regular backups** of the database
4. **Monitor logs** for suspicious activity
5. **Update dependencies** regularly

## Performance Tuning

Current configuration is optimized for small to medium usage:
- Single worker process (SQLite compatible)
- 120-second timeout for long replay generations
- Built-in health checks

For high-traffic scenarios, migrate to PostgreSQL and increase workers.

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure Docker has access to mount volumes
2. **Port conflicts**: Change port mapping in docker-compose.yml
3. **Database errors**: Check volume mounts and permissions
4. **Memory issues**: Monitor container memory usage

### Getting Help

1. Check application logs: `docker-compose logs jamnesia`
2. Verify health status: `docker-compose ps`
3. Test database connection: Access `/api/hands` endpoint
4. Manual testing: `docker exec -it jamnesia_jamnesia_1 python -c "from app import app, db; app.app_context().push(); print('DB OK')"`