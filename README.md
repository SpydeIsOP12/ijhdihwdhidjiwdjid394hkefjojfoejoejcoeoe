# Braintree Auth API - Railway Deployment

## Deploy to Railway

1. Create a new project on Railway
2. Upload these files:
   - `braintree_api.py`
   - `requirements.txt`
   - `Procfile`

3. Railway will auto-deploy

## Usage

Once deployed, you'll get a URL like: `https://your-app.railway.app`

### Endpoints:

**Check Card:**
```
GET https://your-app.railway.app/check?cc=4147202773563216|09|30|268&proxy=p102.squidproxies.com:9496:818:5v9UAseK3tBX
```

**Response:**
```json
{
  "status": "approved",
  "message": "APPROVED ✅",
  "response": "APPROVED ✅", 
  "card": "4147202773563216|09|30|268",
  "gateway": "Braintree B3 1"
}
```

## Use in PHP

```php
$card = '4147202773563216|09|30|268';
$proxy = 'p102.squidproxies.com:9496:818:5v9UAseK3tBX';

$url = "https://your-app.railway.app/check?cc=" . urlencode($card) . "&proxy=" . urlencode($proxy);
$result = file_get_contents($url);
$data = json_decode($result, true);

echo $data['response']; // APPROVED ✅
```
