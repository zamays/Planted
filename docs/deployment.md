# Deploying Planted to the Web

This guide will help you deploy Planted to a web server for public or private access.

## Prerequisites

- A server or cloud hosting account (e.g., DigitalOcean, AWS, Heroku, PythonAnywhere)
- Basic knowledge of Linux/Unix commands
- OpenWeatherMap API key (optional but recommended)

## Deployment Options

### Option 1: PythonAnywhere (Easiest)

PythonAnywhere is a Python-focused hosting platform with a free tier.

1. **Create Account**: Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Code**:
   ```bash
   # On PythonAnywhere console
   git clone https://github.com/zamays/Planted.git
   cd Planted
   ```

3. **Install Dependencies**:
   ```bash
   pip3 install --user -r requirements.txt
   ```

4. **Configure Web App**:
   - Go to Web tab
   - Add a new web app
   - Choose Flask
   - Set path to `/home/yourusername/Planted/app.py`

5. **Set Environment Variables**:
   - Edit your `.env` file with your API keys
   - Or use PythonAnywhere's environment variable settings

6. **Reload**: Click "Reload" on the Web tab

### Option 2: Heroku

Heroku is a cloud platform that supports Python applications.

1. **Install Heroku CLI**:
   ```bash
   # See: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**:
   ```bash
   heroku create planted-app
   ```

3. **Add Procfile**:
   Create a file named `Procfile` in the project root:
   ```
   web: gunicorn app:app
   ```

4. **Add Gunicorn**:
   Add to `requirements.txt`:
   ```
   gunicorn>=20.1.0
   ```

5. **Configure Environment**:
   ```bash
   heroku config:set OPENWEATHERMAP_API_KEY=your_key_here
   heroku config:set FLASK_SECRET_KEY=your_secret_key_here
   ```

6. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 3: DigitalOcean/AWS/Your Own Server

For more control, deploy on your own server.

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx -y
```

#### 2. Clone and Setup Application

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/zamays/Planted.git
cd Planted

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### 3. Configure Environment

```bash
# Create .env file
sudo nano .env

# Add your configuration:
OPENWEATHERMAP_API_KEY=your_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

#### 4. Create Systemd Service

Create `/etc/systemd/system/planted.service`:

```ini
[Unit]
Description=Planted Garden Management Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/Planted
Environment="PATH=/var/www/Planted/venv/bin"
ExecStart=/var/www/Planted/venv/bin/gunicorn --workers 3 --bind unix:planted.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable planted
sudo systemctl start planted
sudo systemctl status planted
```

#### 5. Configure Nginx

Create `/etc/nginx/sites-available/planted`:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/Planted/planted.sock;
    }

    location /static {
        alias /var/www/Planted/garden_manager/web/static;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/planted /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Setup SSL (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

## Production Configuration

### Security

1. **Change Secret Key**: Generate a secure secret key:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

2. **Disable Debug Mode**: Ensure `debug=False` in production

3. **Use HTTPS**: Always use SSL/TLS in production

4. **Restrict Database Access**: Set proper file permissions:
   ```bash
   chmod 600 garden.db
   ```

5. **Keep Dependencies Updated**: Regularly update packages:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

### Performance

1. **Use Production WSGI Server**: Never use Flask's built-in server
   - Gunicorn (recommended)
   - uWSGI
   - Waitress

2. **Configure Workers**:
   ```bash
   # Rule of thumb: 2-4 workers per CPU core
   gunicorn --workers 4 --threads 2 app:app
   ```

3. **Enable Caching**:
   - Cache weather data to reduce API calls
   - Use Flask-Caching for response caching

4. **Optimize Database**:
   - Add indexes for frequently queried fields
   - Use connection pooling for high traffic

### Monitoring

1. **Application Logs**:
   ```bash
   sudo journalctl -u planted -f
   ```

2. **Nginx Logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/access.log
   ```

3. **Health Checks**: Set up monitoring to check application uptime

### Backup

1. **Database Backup**:
   ```bash
   # Create backup script
   #!/bin/bash
   cp /var/www/Planted/garden.db /backups/garden_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Schedule with Cron**:
   ```bash
   # Backup daily at 2 AM
   0 2 * * * /path/to/backup_script.sh
   ```

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENWEATHERMAP_API_KEY` | Weather API key | No | `abc123...` |
| `FLASK_SECRET_KEY` | Flask session key | Yes (production) | `hex_string...` |
| `FLASK_ENV` | Environment | No | `production` |
| `DATABASE_PATH` | Database location | No | `/data/garden.db` |

## Multi-User Considerations

Currently, Planted is designed for single-user local use. For multi-user:

1. **Add Authentication**:
   - Flask-Login for user sessions
   - User registration and login

2. **Database Changes**:
   - Add user_id to all tables
   - Migrate to PostgreSQL or MySQL

3. **User Isolation**:
   - Filter all queries by user_id
   - Prevent data leakage between users

## Troubleshooting

### Application Won't Start

1. Check logs: `sudo journalctl -u planted -n 50`
2. Verify Python path in systemd service
3. Check file permissions
4. Verify all dependencies installed

### Database Errors

1. Check file permissions: `ls -l garden.db`
2. Verify database path in configuration
3. Check disk space: `df -h`

### Weather Data Not Loading

1. Verify API key in `.env`
2. Check network connectivity
3. Review weather service logs
4. Ensure API key is activated (can take a few minutes)

### Performance Issues

1. Check server resources: `htop`
2. Increase worker processes
3. Add caching
4. Optimize database queries

## Scaling Considerations

### Vertical Scaling
- Increase server resources (RAM, CPU)
- Optimize application code
- Add caching layers

### Horizontal Scaling
- Use a reverse proxy load balancer
- Share database across instances
- Use Redis for session storage
- Deploy static files to CDN

## Updating the Application

```bash
# On server
cd /var/www/Planted
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart planted
```

## Support

For deployment issues:
- Check [GitHub Issues](https://github.com/zamays/Planted/issues)
- Review Flask documentation
- Consult your hosting provider's docs

---

**Happy Deploying! 🚀🌱**
