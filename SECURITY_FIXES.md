# Security Fixes - Certificate Distribution Platform

## Issues Fixed

### 1. ❌ Direct API Abuse (CRITICAL)
**Problem:** Students could bypass the web form and directly call the `/certificate` endpoint with fake names using browser DevTools.

**Solution:** 
- Implemented **CSRF token** requirement on all certificate download endpoints
- Frontend now fetches a secure token from `/csrf-token` endpoint before allowing downloads
- Tokens are single-use and expire after 1 hour
- Direct API calls without valid tokens are rejected

### 2. ❌ No Rate Limiting (HIGH)
**Problem:** Multiple fraudulent certificate requests from the same IP address could succeed without detection.

**Solution:**
- Implemented **rate limiting**: 5 requests per minute per IP address
- Rate limits are enforced on both `/certificate` and `/certificate-management` endpoints
- Exceeding limits returns HTTP 429 (Too Many Requests)

### 3. ❌ No Request Logging (HIGH)
**Problem:** No audit trail of certificate generation - couldn't track who generated what.

**Solution:**
- All certificate requests are now logged with:
  - Timestamp
  - Client IP address
  - Name and ID used
  - Success/failure status
  - Failure reason
- Logs stored in `logs/` directory with daily rotation
- Logs can be retrieved via admin endpoints

### 4. ❌ No Fraud Detection (MEDIUM)
**Problem:** Couldn't identify suspicious patterns (multiple failed attempts, bulk downloads).

**Solution:**
- Implemented **fraud detector** that flags:
  - > 5 failed authentication attempts within 10 minutes
  - > 3 successful downloads from same IP in 10 minutes
- Admin can view suspicious activity via `/admin/suspicious-ips` endpoint

### 5. ❌ Unhelpful Error Messages (LOW)
**Problem:** Error messages revealed which names exist/don't exist in system (information leakage).

**Solution:**
- Generic error message: "Student not found. Please verify your name and student ID."
- No differentiation between wrong name vs. wrong ID
- Prevents attackers from enumerating valid student names

## New Security Features

### CSRF Token Management
```python
GET /csrf-token
Returns: {"csrf_token": "secure_token_here"}
```
- Must be called before attempting certificate download
- Token is valid for 1 hour
- Single-use (consumed after certificate download)

### Rate Limiting
- **Limit:** 5 requests per minute per IP
- **Scope:** Per endpoint (students vs. management)
- **Response:** HTTP 429 if exceeded

### Request Logging
```python
GET /admin/logs?admin_key=YOUR_ADMIN_KEY
Returns: List of all certificate requests with full details
```

### Fraud Detection
```python
GET /admin/suspicious-ips?admin_key=YOUR_ADMIN_KEY
Returns: List of IPs with suspicious activity patterns
```

## Environment Variables

### Required (set in Render):
- `ADMIN_KEY` - Set a strong admin key to access `/admin/*` endpoints

### Example .env file:
```
CSV_PATH=students.csv
CERTIFICATES_DIR=certificates
TEMPLATE_IMAGE=templates/certificate_template.jpg
ADMIN_KEY=your_super_secret_admin_key_here
CERTIFICATE_TEMPLATE_IMAGE=templates/certificate_template.jpg
```

## How to Monitor for Fraud

### 1. Check Recent Logs
```bash
curl "https://your-domain.onrender.com/admin/logs?admin_key=YOUR_ADMIN_KEY" | jq '.'
```

### 2. Identify Suspicious IPs
```bash
curl "https://your-domain.onrender.com/admin/suspicious-ips?admin_key=YOUR_ADMIN_KEY" | jq '.'
```

### 3. Analyze Specific IP
Look for:
- High number of failed attempts (indicates enumeration/brute force)
- Too many successful downloads (indicates bulk certificate generation)
- Attempts with non-existent names

## Frontend Changes

### Before
- Form submission directly called `/certificate` endpoint
- No token requirement
- Students could inspect and modify requests

### After
1. Form submission gets CSRF token from `/csrf-token`
2. Verifies student in CSV (shows verification response)
3. Includes CSRF token when downloading certificate
4. Token is consumed after use

### Security Benefit
- Direct API calls without form submission are now blocked
- Attackers can't easily script certificate generation
- Each certificate download requires fresh token

## Deployment Instructions

1. **Update Render Environment Variables:**
   - Set `ADMIN_KEY` to a strong random value
   - Example: `ADMIN_KEY=xK9pL2mQ8rN5vB3jW4hC7sD1fG6eA9uT`

2. **Deploy Updated Code**
   ```bash
   git add -A
   git commit -m "Add security fixes: CSRF, rate limiting, logging"
   git push origin main
   ```

3. **Monitor Logs**
   - Access `/admin/logs` regularly to review certificate requests
   - Check `/admin/suspicious-ips` daily for fraud attempts
   - Look for patterns in failed authentication attempts

## Security Best Practices

✅ **DO:**
- Change `ADMIN_KEY` regularly
- Monitor logs for suspicious activity
- Use HTTPS only (enforced by Render)
- Review certificate PDFs for tampering

❌ **DON'T:**
- Share admin key with students
- Disable rate limiting for "convenience"
- Ignore fraud alerts
- Hardcode credentials in code

## Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Certificate downloaded successfully | Log successful download |
| 400 | Invalid request parameters | Check error message |
| 403 | CSRF token invalid/missing | Reload page and try again |
| 404 | Student/management member not found | Verify name and ID |
| 429 | Rate limit exceeded | Wait before retrying |
| 500 | Server error | Contact administrator |
| 503 | Database unavailable | Check CSV file exists |

## Testing the Security

### Test CSRF Token Requirement
```bash
# This should fail (no token)
curl "https://your-domain.onrender.com/certificate?name=John&student_id=123"

# This should fail (invalid token)
curl "https://your-domain.onrender.com/certificate?name=John&student_id=123&csrf_token=fake"

# This should work (valid token from /csrf-token)
```

### Test Rate Limiting
```bash
# Make 6 requests rapidly from same IP - 6th should get 429
for i in {1..6}; do
  curl "https://your-domain.onrender.com/csrf-token"
done
```

## Future Improvements

- [ ] IP-based geofencing (flag requests from unexpected locations)
- [ ] Webhook notifications on fraud detection
- [ ] Admin dashboard for viewing logs
- [ ] Two-factor authentication for certificate claims
- [ ] Captcha on verification form
- [ ] Email confirmation before certificate generation

## Questions?

Contact: [Your contact info]
