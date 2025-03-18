# Using Swagger UI with API Keys - Step-by-Step Guide

This guide will walk you through the correct way to authorize API requests in Swagger UI using your API key.

## Step 1: Access the Swagger UI

Open your browser and navigate to:
```
http://localhost:8000/docs
```

## Step 2: Find the Authorize Button

Look for the "Authorize" button at the top right of the Swagger UI page. It typically looks like a lock icon.

![Authorize Button](https://swagger.io/swagger-ui-tutorial/assets/images/images1/authorize.png)

## Step 3: Enter Your API Key

When you click the Authorize button, a dialog will appear:

1. In the "Value" field, enter your API key **exactly as is** - do not include any extra characters:
   ```
   tmk_40af9844458144dc9ba5f5859c8b0f02
   ```

2. **Do not** prefix it with "Bearer" or add quotes. Just paste the raw API key.

3. Click the "Authorize" button in the dialog to save it.

4. Click "Close" to dismiss the dialog.

## Step 4: Verify Authorization

After successful authorization:

1. The lock icon should appear closed/locked
2. The "Authorize" button may show "Logout" or remain as "Authorize" but with a different color

## Step 5: Try an Endpoint

1. Expand the `/api/v1/me` endpoint (or any other endpoint)
2. Click the "Try it out" button
3. Click "Execute" to make the request

## Common Issues and Solutions

### If you still get a 401 Unauthorized error:

1. **Check header case sensitivity**: Ensure your API is configured to accept "X-API-Key" with this exact capitalization.

2. **Check browser developer tools**: Open your browser developer tools (F12) and look at the Network tab while making a request. Check if:
   - The API key is being sent in the request headers
   - The format of the header is correct

3. **Check for CORS issues**: If you see CORS errors in the console, this could prevent the API key from being sent correctly.

4. **Try incognito/private browsing**: Browser extensions or cached data might interfere with requests.

5. **Try a different browser**: Some browsers handle Swagger UI authorization differently.

## Using cURL Instead

If Swagger UI is still not working, you can test your endpoints with cURL:

```bash
curl -H "X-API-Key: tmk_40af9844458144dc9ba5f5859c8b0f02"" http://localhost:8000/api/v1/me
```

## Using the Test Scripts

We've created several scripts to help test API authentication:

1. **Check API key validity**:
   ```bash
   python scripts/check_api_key.py tmk_40af9844458144dc9ba5f5859c8b0f02
   ```

2. **Test GET requests**:
   ```bash
   python scripts/test_api_request.py /api/v1/me tmk_40af9844458144dc9ba5f5859c8b0f02
   ```

3. **Test POST requests**:
   ```bash
   python scripts/test_post_request.py tmk_40af9844458144dc9ba5f5859c8b0f02
   ``` 