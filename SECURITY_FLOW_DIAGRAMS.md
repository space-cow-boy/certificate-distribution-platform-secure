# Security Flow Diagrams

## ❌ BEFORE (Vulnerable)

### Attack Flow - How Students Exploited the System

```
┌─────────────┐
│  Attacker   │
└──────┬──────┘
       │
       │ 1. Opens browser DevTools
       │    Finds /certificate endpoint
       ▼
┌──────────────────────────────────────────┐
│  Direct API Call (No Validation)         │
│  GET /certificate?name=Fake&id=12345    │
└──────────────────┬───────────────────────┘
                   │
                   │ 2. No CSRF token required
                   │ 3. No rate limiting
                   │ 4. No logging
                   ▼
┌──────────────────────────────────────────┐
│  Backend generates PDF                   │
│  - No validation that Fake exists        │
│  - Creates certificate immediately      │
│  - No record of the request              │
└──────────────────┬───────────────────────┘
                   │
                   ▼
        ✅ Fraudulent Certificate Downloaded
```

**Why This Worked:**
- ❌ No CSRF token requirement
- ❌ No rate limiting
- ❌ No request logging
- ❌ Generic error messages (information leakage)
- ❌ Certificate generated without verification

---

## ✅ AFTER (Secure)

### Legitimate Flow - How Students Get Certificates Now

```
┌──────────────────┐
│  Student/Form    │
└────────┬─────────┘
         │
         │ 1. Fills form (name + ID)
         │    Clicks "Download Certificate"
         ▼
┌─────────────────────────────────────────────┐
│  Step 1: Get CSRF Token                     │
│  Frontend calls: GET /csrf-token            │
└────────┬────────────────────────────────────┘
         │
         │ Returns: {"csrf_token": "..."}
         ▼
┌─────────────────────────────────────────────┐
│  Step 2: Verify Student                     │
│  Frontend calls: GET /verify?name=X&id=Y   │
└────────┬────────────────────────────────────┘
         │
         │ ✅ Checks database
         │ Returns: Student details OR 404
         ▼
┌─────────────────────────────────────────────┐
│  Step 3: Download with Token                │
│  Frontend includes CSRF token:              │
│  GET /certificate?name=X&id=Y&csrf=TOKEN  │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Backend Validation:                        │
│  ✅ Check CSRF token is valid               │
│  ✅ Check rate limit (5/min per IP)        │
│  ✅ Check student exists in CSV             │
│  ✅ Log request with IP + timestamp         │
└────────┬────────────────────────────────────┘
         │
         ▼ All checks passed
         │
┌─────────────────────────────────────────────┐
│  Generate Certificate                       │
│  ✅ Use verified student name               │
│  ✅ Create PDF file                         │
│  ✅ Log successful generation               │
│  ✅ Check for fraud patterns                │
└────────┬────────────────────────────────────┘
         │
         ▼
    ✅ Legitimate Certificate Downloaded
```

---

## 🚨 Attack Attempt - How Fraud is Blocked Now

### Attacker Tries Direct API Call

```
┌─────────────┐
│  Attacker   │
└──────┬──────┘
       │
       │ Tries: GET /certificate?name=Fake&id=999
       │
       ▼
┌──────────────────────────────────────────┐
│  Backend Checks:                         │
│  ✅ CSRF token missing? → 403 FORBIDDEN  │
│  ✅ Invalid token? → 403 FORBIDDEN       │
│  ✅ Rate limit exceeded? → 429 TOO MANY  │
│  ✅ Student not in CSV? → 404 NOT FOUND  │
│                                          │
│  Request logged:                         │
│  IP: 123.45.67.89                       │
│  Name: "Fake"                           │
│  Status: FAILED                         │
│  Reason: "Invalid CSRF token"           │
└──────────────────┬───────────────────────┘
                   │
                   ▼
        ❌ Request Blocked - No PDF
        ⚠️  Fraud Alert Generated
```

---

## 📊 Rate Limiting Behavior

### Legitimate User (Normal Pattern)

```
Timeline: 0-60 seconds

Request 1: ✅ Success (4 remaining)
Request 2: ✅ Success (3 remaining)
Request 3: ✅ Success (2 remaining)
Request 4: ✅ Success (1 remaining)
Request 5: ✅ Success (0 remaining)
Request 6: ❌ 429 Rate Limited

Wait 60 seconds...

Request 7: ✅ Success (4 remaining)
```

### Attacker (Abnormal Pattern)

```
Timeline: 0-5 seconds

Request 1: ✅ Success (4 remaining)
Request 2: ✅ Success (3 remaining)
Request 3: ✅ Success (2 remaining)
Request 4: ✅ Success (1 remaining)
Request 5: ✅ Success (0 remaining)
Request 6: ❌ 429 Rate Limited
...tries 10 more times...
Request 16: ❌ 429 Rate Limited

⚠️ FRAUD ALERT: IP 123.45.67.89
   - 15 failed requests in 5 seconds
   - Likely brute force or enumeration
```

---

## 📋 Request Logging Flow

### What Gets Logged

```
Every certificate request:

{
  "timestamp": "2026-02-04T10:30:45.123456",
  "ip_address": "192.168.1.100",
  "endpoint": "get_certificate",
  "name": "John Doe",
  "id": "25101234567",
  "status": "success",      ← or "failed"
  "reason": ""              ← e.g., "Invalid CSRF token"
}
```

### Log Analysis

```
Daily Log Review (Feb 4, 2026):

Total Requests: 342
├─ Successful: 320 ✅
├─ Failed: 22 ⚠️
│  ├─ Invalid CSRF token: 10
│  ├─ Rate limit exceeded: 8
│  ├─ Student not found: 4
│  └─ Other: 0
│
└─ Suspicious IPs: 2 ⚠️
   ├─ 192.168.1.100 (12 failed attempts in 30s)
   └─ 203.0.113.45 (18 downloads in 10s)
```

---

## 🔐 Token Management

### CSRF Token Lifecycle

```
User visits certificate portal
         │
         ▼
    Frontend page loads
         │
    User enters name + ID
    Clicks "Download"
         │
         ▼
    Frontend: GET /csrf-token
         │
         ▼
    Backend generates token
    Stores in memory with timestamp
    Returns to frontend
         │
         ▼
    Frontend: GET /certificate?...&csrf_token=XYZ
         │
         ▼
    Backend validates token:
    ✅ Token exists in memory
    ✅ Token < 1 hour old
    ✅ Student in database
         │
         ▼
    Token consumed (deleted from memory)
    PDF generated
    Response sent
         │
         ▼
    ✅ Certificate downloaded

--- Token Expires After 1 Hour ---

User comes back 2 hours later
         │
         ▼
    Frontend still has old token
    Tries: GET /certificate?...&csrf_token=OLD
         │
         ▼
    Backend checks:
    ❌ Token not in memory (expired)
         │
         ▼
    Returns: 403 Forbidden
    Message: "Invalid or expired security token"
         │
         ▼
    ❌ Request blocked
    ℹ️  User must reload page to get fresh token
```

---

## 📈 Security Metrics Dashboard

### Before Security Fixes
```
Fraudulent Certificates Generated: 🔴 [UNKNOWN - not tracked]
Request Logging: 🔴 NONE
Rate Limiting: 🔴 NONE
CSRF Protection: 🔴 NONE
Fraud Detection: 🔴 NONE
```

### After Security Fixes
```
Fraudulent Certificates Generated: 🟢 [Tracked & Blocked]
Request Logging: 🟢 FULL AUDIT TRAIL
Rate Limiting: 🟢 5/min per IP
CSRF Protection: 🟢 Single-use tokens
Fraud Detection: 🟢 Automatic alerts
```

---

## 🎯 Attack Scenarios - Before vs After

### Scenario 1: Brute Force Attack

**Before:**
```
Attacker sends 1000 requests in 1 minute
Result: ❌ 1000 fraudulent certificates created
Detection: NONE
```

**After:**
```
Attacker sends 1000 requests in 1 minute
Result: ✅ First 5 succeed (if valid CSRF tokens)
        ✅ Next 995 blocked with 429 error
Detection: 🟢 Fraud alert: "1000 requests from IP X in 60s"
```

### Scenario 2: Name Enumeration

**Before:**
```
Attacker tries: "GET /certificate?name=Alice&id=123"
Response: 404 "Student not found"
Attacker: "OK, Alice is not enrolled"

Attacker tries: "GET /certificate?name=Bob&id=123"
Response: 404 "Student not found"
Attacker: "Bob not enrolled either"

[Attacker enumerates all valid names...]
```

**After:**
```
Attacker tries: "GET /certificate?name=Alice&id=123&csrf_token=..."
Response: 404 "Student not found with name/ID"
Attacker: ??? "Can't tell if name or ID is wrong"
[Enumeration becomes ineffective]
```

---

## ✅ Security Checklist

- ✅ CSRF tokens required for all certificate downloads
- ✅ Rate limiting prevents bulk downloads (5/min per IP)
- ✅ All requests logged with timestamp, IP, name, ID
- ✅ Fraud detector flags suspicious patterns
- ✅ Admin endpoints for monitoring (`/admin/logs`, `/admin/suspicious-ips`)
- ✅ Error messages don't reveal what exists/doesn't exist
- ✅ Tokens are single-use and expire after 1 hour
- ✅ Logs stored in `logs/` directory for auditing

---

## 🔄 Recommended Daily Actions

```
Morning:
1. Check /admin/suspicious-ips?admin_key=...
2. Review /admin/logs for any fraud attempts
3. Verify legitimate requests went through

End of Day:
1. Archive certificate PDFs (evidence preservation)
2. Note any anomalies in logs
3. Update admin key if suspicious activity detected

Weekly:
1. Analyze logs for trends
2. Review certificate PDFs for tampering
3. Update documentation with findings
```
