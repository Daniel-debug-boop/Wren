---
name: VibeSec-Skill
description: Security patterns for vibe coding — 10 rules covering IDOR, XSS, CSRF, SSRF, SQLi, auth, encryption, secrets, API security, dependencies, logging
triggers:
  - security
  - vulnerability
  - secure
  - injection
  - XSS
  - CSRF
  - SSRF
  - SQL
  - authentication
  - authorization
  - OWASP
  - sanitize
  - validate
  - encrypt
  - secret
  - token
  - permission
  - access control
  - exploit
  - OWASP
  - Top 10
  - dependency
  - CVE
  - patch
  - update
  - secure coding
  - secure by default
  - security-first
---

# VibeSec-Skill: Secure Vibe Coding Patterns

## Purpose
10 essential security rules for writing secure code with AI coding agents. Covers 60-70% of common vulnerabilities.

## The 10 Rules

### Rule 1: IDOR Prevention
**Never trust user-provided IDs for data access.**

```typescript
// ❌ BAD: Direct ID from user
const user = await db.users.findById(req.params.id);

// ✅ GOOD: Use authenticated user's ID
const user = await db.users.findById(req.session.userId);
```

**Pattern:**
- Always derive resource ownership from authenticated session
- Never accept client-provided IDs for data access
- Validate resource belongs to authenticated user before operations

---

### Rule 2: XSS Prevention
**Escape output. Never inject user input into HTML.**

```typescript
// ❌ BAD: Direct injection
element.innerHTML = userInput;

// ✅ GOOD: Text content or escaping
element.textContent = userInput;
```

**Pattern:**
- Use `textContent` instead of `innerHTML`
- Sanitize HTML with DOMPurify before rendering
- Encode output for HTML, JavaScript, URL, CSS contexts
- Use frameworks' auto-escaping (React, Vue, Angular)

---

### Rule 3: CSRF Protection
**Validate state-changing requests.**

```typescript
// ❌ BAD: No CSRF protection
app.post('/transfer', (req, res) => {
  // Process transfer
});

// ✅ GOOD: CSRF token validation
app.post('/transfer', csrfProtection, (req, res) => {
  // Process transfer
});
```

**Pattern:**
- Use anti-CSRF tokens for state-changing operations
- Validate `Origin` and `Referer` headers
- Use `SameSite` cookie attribute
- Require re-authentication for sensitive operations

---

### Rule 4: SSRF Prevention
**Validate and restrict outbound requests.**

```typescript
// ❌ BAD: Unvalidated URL fetch
const response = await fetch(req.body.url);

// ✅ GOOD: URL validation and allowlist
const allowedHosts = ['api.example.com', 'cdn.example.com'];
const url = new URL(req.body.url);
if (!allowedHosts.includes(url.hostname)) {
  throw new Error('Invalid URL');
}
const response = await fetch(url);
```

**Pattern:**
- Validate URLs against allowlist
- Block internal/private IP ranges
- Disable unnecessary URL schemes (`file://`, `gopher://`)
- Use metadata endpoint blocking for cloud environments

---

### Rule 5: SQL Injection Prevention
**Use parameterized queries. Never concatenate user input.**

```typescript
// ❌ BAD: String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE id = ?';
const result = await db.query(query, [userId]);
```

**Pattern:**
- Always use parameterized queries/prepared statements
- Never build SQL from user input
- Use ORM query builders when available
- Validate input types before query execution

---

### Rule 6: Authentication Security
**Use proven libraries. Never roll your own crypto.**

```typescript
// ❌ BAD: Custom password hashing
const hash = crypto.createHash('md5').update(password).digest('hex');

// ✅ GOOD: Use bcrypt/argon2
const hash = await bcrypt.hash(password, 12);
```

**Pattern:**
- Use bcrypt, argon2, or scrypt for password hashing
- Implement rate limiting on login attempts
- Use multi-factor authentication
- Store session data server-side (not JWT for sensitive apps)

---

### Rule 7: Input Validation
**Validate on server. Never trust client-side validation.**

```typescript
// ❌ BAD: Only client validation
if (clientSideValid) {
  await saveData(data);
}

// ✅ GOOD: Server-side validation
const sanitized = validateAndSanitize(data);
await saveData(sanitized);
```

**Pattern:**
- Validate all input on the server
- Use schema validation (Zod, Joi, Yup)
- Reject unexpected fields
- Enforce strict type checking

---

### Rule 8: Secrets Management
**Never hardcode secrets. Use environment variables.**

```typescript
// ❌ BAD: Hardcoded secret
const apiKey = 'sk-1234567890abcdef';

// ✅ GOOD: Environment variable
const apiKey = process.env.API_KEY;
```

**Pattern:**
- Use environment variables or secret managers
- Never commit secrets to version control
- Rotate secrets regularly
- Use `.env.example` without real values

---

### Rule 9: API Security
**Validate and sanitize all API inputs.**

```typescript
// ❌ BAD: No validation
app.post('/api/data', (req, res) => {
  db.insert(req.body);
});

// ✅ GOOD: Input validation
app.post('/api/data', validateSchema(dataSchema), (req, res) => {
  db.insert(req.body);
});
```

**Pattern:**
- Validate request body, query params, headers
- Use rate limiting
- Implement proper error handling (no stack traces in production)
- Use HTTPS only

---

### Rule 10: Dependency Security
**Keep dependencies updated. Audit regularly.**

```bash
# Check for vulnerabilities
npm audit
pip check
```

**Pattern:**
- Run security audits before deployment
- Use lockfiles (package-lock.json, poetry.lock)
- Subscribe to security advisories
- Remove unused dependencies

---

## Quick Reference Checklist

- [ ] **IDOR**: Use authenticated user's ID, not client-provided
- [ ] **XSS**: Escape output, sanitize HTML
- [ ] **CSRF**: Validate tokens on state changes
- [ ] **SSRF**: Validate URLs, block internal IPs
- [ ] **SQLi**: Parameterized queries only
- [ ] **Auth**: Use proven libraries (bcrypt, argon2)
- [ ] **Input**: Server-side validation always
- [ ] **Secrets**: Environment variables, never hardcoded
- [ ] **API**: Validate all inputs, rate limit
- [ ] **Dependencies**: Audit regularly, keep updated

---

## Framework-Specific Notes

### React/Vue/Auto-escaping Frameworks
- Still sanitize HTML with DOMPurify
- Avoid `dangerouslySetInnerHTML` / `v-html`
- Validate props and state

### Node.js/Express
- Use `helmet` for security headers
- Use `cors` middleware properly
- Use `express-validator` for input validation

### Python/Django/Flask
- Use Django's ORM (auto-escapes)
- Use Flask-WTF for CSRF
- Use parameterized queries with SQLAlchemy

### Java/Spring
- Use Spring Security
- Use JPA/Hibernate (parameterized)
- Validate with Bean Validation

### .NET
- Use ASP.NET Core Identity
- Use Entity Framework (parameterized)
- Use anti-forgery tokens

---

## Cloud-Specific Patterns

### AWS
- Block metadata endpoints (169.254.169.254)
- Use IAM roles, not hardcoded credentials
- Enable S3 bucket blocking

### GCP
- Block metadata endpoints
- Use service accounts
- Enable storage bucket lockdown

### Azure
- Block IMDS (169.254.169.254)
- Use managed identities
- Restrict storage access

---

## Agent Instructions

When you encounter security-related code:

1. **Review for IDOR**: Ensure resource access uses authenticated user ID
2. **Check XSS vectors**: Verify output encoding and HTML sanitization
3. **Validate CSRF**: Ensure state-changing operations have CSRF protection
4. **Scan for SSRF**: Validate any outbound URL fetching
5. **Check SQL queries**: Ensure parameterized queries are used
6. **Review auth**: Use proven libraries, not custom implementations
7. **Validate input**: Server-side validation for all user input
8. **Scan secrets**: No hardcoded credentials
9. **Review API**: Proper validation and error handling
10. **Check deps**: Known vulnerabilities in dependencies

**If you find a violation, fix it immediately and explain the security impact.**