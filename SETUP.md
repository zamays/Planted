# Planted - Setup Guide

## Environment Configuration

This application uses environment variables to securely manage API keys and other sensitive configuration. **Never commit your `.env` file to git!**

### First-Time Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Get your OpenWeatherMap API key:**
   - Visit https://openweathermap.org/api
   - Sign up for a free account at https://home.openweathermap.org/users/sign_up
   - Go to your API keys section
   - Copy your API key

3. **Edit your `.env` file:**
   ```bash
   # Open .env in your favorite editor
   nano .env
   # or
   code .env
   ```

4. **Add your API key:**
   ```
   OPENWEATHERMAP_API_KEY=your_actual_api_key_here
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENWEATHERMAP_API_KEY` | Your OpenWeatherMap API key for real weather data | No | Falls back to mock data |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | No | Default development key |

### Running Without an API Key

If you don't provide an OpenWeatherMap API key, the application will automatically use **mock weather data** for development and testing. You'll see this message when starting:

```
⚠️  No OpenWeatherMap API key found. Using mock weather data.
   To use real weather data, add OPENWEATHERMAP_API_KEY to your .env file
```

### Security Best Practices

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Use different API keys for development and production**
3. **Rotate your API keys periodically**
4. **Don't share your `.env` file** - Share `.env.example` instead

### For Collaborators

If you're collaborating on this project:

1. Get your own OpenWeatherMap API key (it's free!)
2. Copy `.env.example` to `.env`
3. Add your own API key to `.env`
4. Never commit your `.env` file

### Troubleshooting

**"No module named 'dotenv'"**
```bash
pip install python-dotenv
```

**Weather data not loading:**
- Check that your `.env` file exists
- Verify your API key is correct
- Make sure there are no quotes around the API key in `.env`
- Check that your API key is activated (can take a few minutes after signup)

**Mock data being used when you have an API key:**
- Ensure `.env` is in the project root directory
- Check that the variable name is exactly `OPENWEATHERMAP_API_KEY`
- Restart the Flask application after adding the API key
