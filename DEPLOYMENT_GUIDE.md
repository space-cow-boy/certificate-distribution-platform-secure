# Deployment Guide - Security Updates

## Quick Start

### Step 1: Set Admin Key in Render

1. Go to your Render dashboard
2. Select your certificate service
3. Go to **Settings** → **Environment**
4. Add/Update this variable:
   ```
   ADMIN_KEY=xK9pL2mQ8rN5vB3jW4hC7sD1fG6eA9uT
   ```
   (Use a strong random string, not this example!)

5. **Save** and your service will auto-deploy

### Step 2: Test the Deployment

After Render redeploys (you'll see "Deploy Successful"):

```bash
# Test CSRF token generation
curl "https://your-domain.onrender.com/csrf-token"

# Should return:
# {"csrf_token":"...long token..."}
```

### Step 3: Monitor for Fraud

View logs:
```bash
curl "https://your-domain.onrender.com/admin/logs?admin_key=xK9pL2mQ8rN5vB3jW4hC7sD1fG6eA9uT"
```

View suspicious IPs:
```bash
curl "https://your-domain.onrender.com/admin/suspicious-ips?admin_key=xK9pL2mQ8rN5vB3jW4hC7sD1fG6eA9uT"
```

## What Changed

### New Files
- `app/security.py` - Rate limiting, CSRF tokens, logging, fraud detection
- `logs/` - Directory for request logs (auto-created)
- `tokens/` - Directory for CSRF tokens (auto-created)
- `SECURITY_FIXES.md` - Detailed documentation

### Modified Files
- `app/main.py` - Added security features to certificate endpoints
- `templates/index.html` - Updated forms to use CSRF tokens

## Backwards Compatibility

⚠️ **BREAKING CHANGE**: Direct API calls to `/certificate` endpoint now require a valid CSRF token.

### Old Way (No Longer Works)
```
GET /certificate?name=John&student_id=123
→ Returns 403 Forbidden (missing CSRF token)
```

### New Way (Required)
```
GET /csrf-token
→ {"csrf_token": "..."}

GET /certificate?name=John&student_id=123&csrf_token=...
→ Returns PDF
```

## Monitoring Checklist

Daily:
- [ ] Check `/admin/suspicious-ips` for fraud attempts
- [ ] Review `/admin/logs` for unusual patterns
- [ ] Verify log files in `logs/` directory

Weekly:
- [ ] Analyze trends in failed vs. successful requests
- [ ] Update admin key if compromised
- [ ] Review certificate PDFs for tampering

## Troubleshooting

### Issue: "Invalid or expired security token"
**Solution:** Page was left open for >1 hour. Reload page to get fresh token.

### Issue: "Too many requests. Please wait"
**Solution:** Rate limit is 5 per minute per IP. Wait 60 seconds and try again.

### Issue: Logs directory is growing large
**Solution:** Logs auto-rotate daily. Old logs are archived in `logs/` folder.

### Issue: Admin endpoints return 403
**Solution:** Check that `ADMIN_KEY` environment variable is set in Render correctly.

## Files to Watch

- `logs/certificate_requests_*.json` - Daily certificate request logs
- `certificates/` - Generated PDF files (check for suspicious names)
- `tokens/` - Active CSRF tokens (should have ~10-20 files)

## Rollback Instructions

If you need to revert security changes:

```bash
git log --oneline
# Find the commit before security fixes
git reset --hard COMMIT_HASH
git push origin main --force
```

## Need Help?

Common issues and solutions are in [SECURITY_FIXES.md](SECURITY_FIXES.md)

Key sections:
- "Testing the Security"
- "Response Codes"
- "Monitoring for Fraud"
