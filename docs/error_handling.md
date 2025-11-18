# Error Handling Documentation

## Overview

Planted implements a comprehensive error handling system that provides user-friendly error pages for common HTTP errors and JSON responses for API endpoints.

## Error Pages

### Available Error Pages

1. **404 - Page Not Found** (`/garden_manager/web/templates/errors/404.html`)
   - Displayed when a user tries to access a non-existent page
   - Provides helpful suggestions and navigation options
   - Shows the requested URL that was not found

2. **403 - Forbidden** (`/garden_manager/web/templates/errors/403.html`)
   - Displayed when a user doesn't have permission to access a resource
   - Different actions shown for guest users vs. logged-in users
   - Explains common reasons for forbidden access

3. **500 - Internal Server Error** (`/garden_manager/web/templates/errors/500.html`)
   - Displayed when an unexpected server error occurs
   - Logs error details for debugging
   - Reassures users that the issue has been reported

4. **503 - Service Unavailable** (`/garden_manager/web/templates/errors/503.html`)
   - Displayed during maintenance or when services are down
   - Provides retry options
   - Includes maintenance notice

### Design Features

All error pages include:
- **Animated icons**: Visual feedback with CSS animations (sway, shake, spin, pulse)
- **Clear messaging**: User-friendly explanations of what went wrong
- **Helpful suggestions**: Actionable steps users can take
- **Action buttons**: Links to dashboard, plants page, or go back
- **Support links**: Access to help page
- **Consistent styling**: Matches the application's garden theme
- **Responsive design**: Works on mobile and desktop

## Error Handlers

### Web Error Handlers (app.py)

```python
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 Page Not Found errors."""
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden errors."""
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 Internal Server Error."""
    logger.error("Internal server error: %s", e, exc_info=True)
    return render_template('errors/500.html'), 500

@app.errorhandler(503)
def service_unavailable(e):
    """Handle 503 Service Unavailable errors."""
    return render_template('errors/503.html'), 503
```

### API Error Handlers (garden_manager/web/blueprints/api/__init__.py)

API endpoints return JSON error responses:

```python
@api_bp.errorhandler(404)
def api_not_found(e):
    """Handle 404 errors for API endpoints with JSON response."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status': 404
    }), 404

@api_bp.errorhandler(403)
def api_forbidden(e):
    """Handle 403 errors for API endpoints with JSON response."""
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource',
        'status': 403
    }), 403

@api_bp.errorhandler(500)
def api_internal_error(e):
    """Handle 500 errors for API endpoints with JSON response."""
    logger.error("API internal server error: %s", e, exc_info=True)
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal error occurred while processing your request',
        'status': 500
    }), 500

@api_bp.errorhandler(400)
def api_bad_request(e):
    """Handle 400 Bad Request errors for API endpoints."""
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request could not be understood or was missing required parameters',
        'status': 400
    }), 400
```

### Existing Error Handlers

The application also maintains existing error handlers:

- **CSRF Error Handler** (400): Handles CSRF token validation failures
- **Rate Limit Handler** (429): Handles rate limit exceeded errors
  - Returns JSON for API endpoints
  - Returns HTML for web pages

## Error Logging

All 500-level errors are automatically logged with full stack traces:

```python
logger.error("Internal server error: %s", e, exc_info=True)
```

This ensures that developers can debug issues while users see friendly error messages.

## Testing

The error handling system includes comprehensive tests in `tests/unit/test_error_handlers.py`:

- **Web error handler tests**: Verify correct templates are rendered
- **API error handler tests**: Verify JSON responses with correct structure
- **Existing handler tests**: Ensure CSRF and rate limiting still work
- **Accessibility tests**: Verify error pages have proper landmarks
- **Logging tests**: Verify errors are logged appropriately

All 13 tests pass successfully.

## Future Enhancements

### Error Tracking Integration (Optional)

For production deployments, you can integrate error tracking services like Sentry:

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if app.config.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration()],
        environment=app.config.get('ENV', 'production')
    )
```

Add to `.env`:
```
SENTRY_DSN=your_sentry_dsn_here
```

This would provide:
- Real-time error notifications
- Error aggregation and trends
- User context and breadcrumbs
- Performance monitoring

## Best Practices

1. **Always log errors**: Use `logger.error()` for 500-level errors
2. **Be user-friendly**: Explain what happened in plain language
3. **Provide next steps**: Give users actionable suggestions
4. **Maintain consistency**: Use the same design language across all error pages
5. **Test thoroughly**: Verify error handlers work in all scenarios
6. **Monitor in production**: Use error tracking to catch issues early

## Troubleshooting

### Error pages not displaying

If error pages aren't showing:
1. Check that templates exist in `garden_manager/web/templates/errors/`
2. Verify error handlers are registered in `app.py`
3. Check Flask's debug mode is OFF (error handlers don't work in debug mode)
4. Review application logs for any template rendering errors

### API endpoints returning HTML instead of JSON

Blueprint error handlers may not override app-level handlers in some Flask versions. Ensure:
1. API blueprint is registered before other blueprints
2. Error handlers are registered on the blueprint correctly
3. Request path starts with `/api/` to be handled by API blueprint

### 500 errors not being logged

Check:
1. Logging is properly configured in `garden_manager/config/logging_config.py`
2. Log directory exists and is writable
3. Log level is set to INFO or DEBUG

## Security Considerations

- Error pages don't expose sensitive information
- Stack traces are logged but not shown to users
- API errors don't reveal internal implementation details
- Rate limiting protects against abuse
