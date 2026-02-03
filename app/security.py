"""
Security module for certificate generation
Handles rate limiting, CSRF tokens, and request logging
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
import hashlib
import secrets


class RateLimiter:
    """Rate limiter based on IP address and endpoint"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, ip_address: str, endpoint: str) -> Tuple[bool, int]:
        """
        Check if request is allowed
        
        Args:
            ip_address: Client IP address
            endpoint: API endpoint name
            
        Returns:
            Tuple of (is_allowed: bool, requests_remaining: int)
        """
        key = f"{ip_address}:{endpoint}"
        now = time.time()
        
        # Clean old requests outside window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False, 0
        
        # Add current request
        self.requests[key].append(now)
        remaining = self.max_requests - len(self.requests[key])
        
        return True, remaining


class CSRFTokenManager:
    """Manage CSRF tokens for certificate requests"""
    
    def __init__(self, token_dir: str = "tokens"):
        """Initialize CSRF token manager"""
        self.token_dir = Path(token_dir)
        self.token_dir.mkdir(exist_ok=True)
        self.tokens: Dict[str, float] = {}
    
    def generate_token(self) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = time.time()
        return token
    
    def validate_token(self, token: str, max_age: int = 3600) -> bool:
        """
        Validate a CSRF token
        
        Args:
            token: The token to validate
            max_age: Maximum age of token in seconds
            
        Returns:
            True if valid, False otherwise
        """
        if token not in self.tokens:
            return False
        
        token_age = time.time() - self.tokens[token]
        if token_age > max_age:
            del self.tokens[token]
            return False
        
        # Invalidate token after use
        del self.tokens[token]
        return True


class RequestLogger:
    """Log all certificate requests for auditing"""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize request logger"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"certificate_requests_{datetime.now().strftime('%Y%m%d')}.json"
    
    def log_request(
        self,
        ip_address: str,
        endpoint: str,
        name: str,
        id_value: str,
        status: str,
        reason: str = ""
    ) -> None:
        """
        Log a certificate request
        
        Args:
            ip_address: Client IP address
            endpoint: API endpoint
            name: Name provided in request
            id_value: ID provided in request
            status: "success" or "failed"
            reason: Reason for failure (if applicable)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ip_address": ip_address,
            "endpoint": endpoint,
            "name": name,
            "id": id_value,
            "status": status,
            "reason": reason
        }
        
        # Append to log file
        logs = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def get_logs(self, ip_address: str = None, limit: int = 100) -> list:
        """
        Get logs for auditing
        
        Args:
            ip_address: Filter by IP (optional)
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        except:
            return []
        
        # Filter by IP if provided
        if ip_address:
            logs = [log for log in logs if log.get('ip_address') == ip_address]
        
        # Return most recent first
        return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]


class FraudDetector:
    """Detect suspicious patterns in certificate requests"""
    
    def __init__(self, logger: RequestLogger):
        """
        Initialize fraud detector
        
        Args:
            logger: RequestLogger instance
        """
        self.logger = logger
    
    def check_suspicious_activity(self, ip_address: str, window_minutes: int = 10) -> Dict:
        """
        Check for suspicious patterns
        
        Args:
            ip_address: IP address to check
            window_minutes: Time window to analyze
            
        Returns:
            Dictionary with suspicious flags
        """
        logs = self.logger.get_logs(ip_address=ip_address, limit=1000)
        
        recent_logs = [
            log for log in logs
            if (datetime.fromisoformat(log['timestamp']) - datetime.now()).total_seconds() < window_minutes * 60
        ]
        
        failed_attempts = len([log for log in recent_logs if log['status'] == 'failed'])
        success_count = len([log for log in recent_logs if log['status'] == 'success'])
        
        return {
            "ip": ip_address,
            "recent_requests": len(recent_logs),
            "failed_attempts": failed_attempts,
            "successful_downloads": success_count,
            "suspicious": failed_attempts > 5 or success_count > 3,
            "reason": "Multiple failed attempts" if failed_attempts > 5 else (
                "Too many successful downloads in short time" if success_count > 3 else "Normal"
            )
        }
