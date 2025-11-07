# Weather Data Caching

## Overview

Weather data caching has been implemented to reduce API calls and improve application performance. The caching system uses a 15-minute time-to-live (TTL) for weather data, significantly reducing load times and API costs.

## Features

### 1. Automatic Caching
- **Current weather** data is cached for 15 minutes per location
- **Forecast** data is cached for 15 minutes per location and day count
- Cache keys are based on rounded coordinates (to 2 decimal places) to avoid cache misses from tiny coordinate differences
- Both real API data and mock data are cached

### 2. Cache Statistics
- Track cache hits, misses, and API calls saved
- Calculate hit rate percentage
- Monitor cache sizes
- Access statistics via the weather page UI or API endpoint

### 3. Cache Busting
- Manual refresh button on the weather page
- Bypass cache parameter for programmatic refreshes
- API endpoint to clear entire cache

## Configuration

### Cache TTL (Time-To-Live)

The default cache TTL is **900 seconds (15 minutes)**. This can be customized when initializing the WeatherService:

```python
from garden_manager.services.weather_service import WeatherService

# Default: 15 minutes (900 seconds)
weather_service = WeatherService()

# Custom: 5 minutes (300 seconds)
weather_service = WeatherService(cache_ttl=300)

# Custom: 30 minutes (1800 seconds)
weather_service = WeatherService(cache_ttl=1800)
```

### Cache Size

The cache can store data for up to **100 different locations** by default. This is configured in the `weather_service.py` file:

```python
self._weather_cache = TTLCache(maxsize=100, ttl=cache_ttl)
self._forecast_cache = TTLCache(maxsize=100, ttl=cache_ttl)
```

## Usage

### In Application Code

#### Basic Usage (with caching)
```python
# Automatically uses cache if available
current_weather = weather_service.get_current_weather(latitude, longitude)
forecast = weather_service.get_forecast(latitude, longitude, days=5)
```

#### Bypass Cache
```python
# Force fresh API call
current_weather = weather_service.get_current_weather(
    latitude, longitude,
    bypass_cache=True
)
```

#### Get Cache Statistics
```python
stats = weather_service.get_cache_stats()
# Returns: {
#     'cache_hits': 42,
#     'cache_misses': 10,
#     'api_calls': 10,
#     'total_requests': 52,
#     'hit_rate_percent': 80.8,
#     'weather_cache_size': 3,
#     'forecast_cache_size': 3
# }
```

#### Clear Cache
```python
weather_service.clear_cache()
```

### Via Web Interface

#### Refresh Weather Data
Navigate to the weather page and click the **"🔄 Refresh Weather"** button to bypass the cache and fetch fresh data.

#### View Cache Statistics
Cache performance statistics are displayed at the bottom of the weather page, showing:
- Cache hits (number of times cached data was used)
- Cache misses (number of times fresh data was fetched)
- Hit rate percentage
- API calls saved

### Via API Endpoints

#### Get Cache Statistics
```bash
GET /api/cache_stats
```

Response:
```json
{
    "status": "success",
    "stats": {
        "cache_hits": 42,
        "cache_misses": 10,
        "api_calls": 10,
        "total_requests": 52,
        "hit_rate_percent": 80.8,
        "weather_cache_size": 3,
        "forecast_cache_size": 3
    }
}
```

#### Clear Cache
```bash
POST /api/clear_cache
```

Response:
```json
{
    "status": "success",
    "message": "Weather cache cleared successfully"
}
```

## Benefits

### 1. Reduced API Costs
- Each cache hit saves one API call
- With a typical hit rate of 60-80%, this can reduce API calls by more than half
- For applications with multiple users, savings compound significantly

### 2. Improved Performance
- Cached data loads instantly
- No network latency for cached requests
- Better user experience on slow connections

### 3. API Rate Limit Protection
- Reduces risk of hitting API rate limits
- Handles high traffic without overwhelming the weather API

### 4. Reliability
- Cached data remains available even if API is temporarily unavailable
- Graceful fallback to mock data on errors

## Cache Behavior

### When Cache is Used
- Subsequent requests to the same location within the TTL window
- Coordinates that round to the same value (e.g., 40.7128111 and 40.7128999 both round to 40.71)
- Both current weather and forecast have independent caches

### When Cache is Bypassed
- First request to a new location
- Requests after cache TTL expires (15 minutes by default)
- Manual refresh via UI or API
- Explicit `bypass_cache=True` parameter

### Cache Invalidation
- Automatic expiration after TTL (15 minutes)
- Manual clearing via API or code
- Location changes (different cache key)

## Testing

### With Mock Data
The caching system works identically with mock data (when no API key is configured):

```python
# No API key = mock data
weather_service = WeatherService(api_key="demo_key")

# First call - cache miss, returns mock data
result1 = weather_service.get_current_weather(40.7128, -74.0060)

# Second call - cache hit, returns cached mock data
result2 = weather_service.get_current_weather(40.7128, -74.0060)
```

### With Real API
When a valid OpenWeatherMap API key is configured:

```python
# Real API key from environment
weather_service = WeatherService()

# First call - cache miss, calls API
result1 = weather_service.get_current_weather(40.7128, -74.0060)

# Second call - cache hit, no API call
result2 = weather_service.get_current_weather(40.7128, -74.0060)
```

### Running Tests
```bash
# Run caching tests
pytest tests/unit/test_weather_caching.py -v

# Run all weather tests
pytest tests/unit/test_weather*.py -v
```

## Monitoring

### Key Metrics to Monitor

1. **Hit Rate**: Target 60-80% for typical usage
   - Low hit rate (<40%) may indicate TTL is too short
   - Very high hit rate (>95%) may indicate data is too stale

2. **API Calls Saved**: Track cumulative savings
   - Equal to the number of cache hits
   - Directly translates to cost savings

3. **Cache Size**: Monitor memory usage
   - Weather cache size: Current weather entries
   - Forecast cache size: Forecast entries
   - Default max: 100 locations each

### Example Monitoring Query
```python
stats = weather_service.get_cache_stats()
print(f"Cache Performance:")
print(f"  Hit Rate: {stats['hit_rate_percent']}%")
print(f"  API Calls Saved: {stats['cache_hits']}")
print(f"  Total Cache Entries: {stats['weather_cache_size'] + stats['forecast_cache_size']}")
```

## Troubleshooting

### Problem: Cache Not Working
**Symptoms**: Every request shows as a cache miss

**Solutions**:
1. Check if cache is properly initialized in `weather_service`
2. Verify coordinates are being passed consistently
3. Ensure TTL hasn't expired between requests

### Problem: Stale Data
**Symptoms**: Weather data doesn't update when expected

**Solutions**:
1. Click the refresh button on the weather page
2. Wait for TTL to expire (15 minutes)
3. Use cache clearing API endpoint
4. Reduce TTL in configuration if data needs to be fresher

### Problem: High Memory Usage
**Symptoms**: Application consuming excessive memory

**Solutions**:
1. Reduce cache `maxsize` from 100 to a lower value
2. Reduce TTL to free up entries faster
3. Call `clear_cache()` periodically if needed

## Best Practices

1. **Don't refresh too frequently**: The 15-minute TTL is optimal for weather data
2. **Monitor hit rates**: Aim for 60-80% in production
3. **Use bypass sparingly**: Only bypass cache when absolutely necessary
4. **Test with both modes**: Ensure caching works with both real API and mock data
5. **Document custom TTLs**: If changing from default, document why

## Future Enhancements

Potential improvements for future versions:

1. **Redis/Memcached Support**: For multi-instance deployments
2. **Smarter Cache Keys**: Account for time-of-day patterns
3. **Partial Cache Invalidation**: Clear only specific locations
4. **Cache Warming**: Pre-fetch common locations
5. **Adaptive TTL**: Adjust based on weather change rate
