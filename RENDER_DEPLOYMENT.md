# Deploying Planted to Render.com - Quick Start Guide

## Prerequisites

- GitHub account
- Render.com account (free tier available)

## Step-by-Step Deployment

### 1. Generate a Secure Secret Key

On your **local machine**, run:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Copy the output** - it will be a long random string like:
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

⚠️ **Keep this secret!** Don't share it or commit it to Git.

### 2. Deploy to Render

1. **Sign in** to [render.com](https://render.com)

2. **Create New Web Service**:
   - Click "New +" → "Blueprint"
   - Connect your GitHub account
   - Select the Planted repository
   - Render will detect the `render.yaml` file

3. **Set Environment Variables** (CRITICAL):
   - In the service creation page or Dashboard
   - Go to "Environment" tab
   - Click "Add Environment Variable"
   - Set:
     - **Key**: `FLASK_SECRET_KEY`
     - **Value**: Paste the secret you generated in step 1
   - Click "Save Changes"

4. **Deploy**:
   - Click "Create Web Service" or "Manual Deploy"
   - Wait for build to complete (~2-3 minutes)
   - Your app will be live at `https://your-app-name.onrender.com`

### 3. Optional: Add Weather API Key

For real weather data (otherwise mock data is used):

1. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
2. In Render Dashboard → Environment → Add Environment Variable:
   - **Key**: `OPENWEATHERMAP_API_KEY`
   - **Value**: Your API key
3. Redeploy the service

## Troubleshooting

### Error: "FLASK_SECRET_KEY is set to a weak placeholder value"

**Solution**: You need to set the `FLASK_SECRET_KEY` environment variable in Render Dashboard.

1. Generate a secure key: `python3 -c "import secrets; print(secrets.token_hex(32))"`
2. Go to Render Dashboard → Your Service → Environment
3. Add or edit `FLASK_SECRET_KEY` with the generated value
4. Click "Manual Deploy" → "Clear build cache & deploy"

### Error: "FLASK_SECRET_KEY is not set"

**Solution**: Same as above - add the environment variable.

### Error: "FLASK_SECRET_KEY must be at least 32 characters"

**Solution**: Your key is too short. Generate a new one with the command above (it creates a 64-character key).

### App is slow to wake up

This is normal for Render's free tier. The service "sleeps" after 15 minutes of inactivity and takes ~30 seconds to wake up on the first request.

### Database resets on each deploy

This is expected behavior on Render's free tier. For persistent data, upgrade to a paid plan with a persistent disk or external database.

## Important Notes

- **Security**: Never commit your `.env` file or share your secret key
- **Free Tier**: Services sleep after 15 minutes of inactivity
- **Automatic Deploys**: Pushes to main branch trigger automatic redeployment
- **Database**: SQLite database is ephemeral on free tier (resets with each deploy)

## Need More Help?

- Full deployment guide: [docs/deployment.md](docs/deployment.md)
- GitHub Issues: [github.com/zamays/Planted/issues](https://github.com/zamays/Planted/issues)
- Render Docs: [render.com/docs](https://render.com/docs)

---

**Happy Gardening! 🌱**
