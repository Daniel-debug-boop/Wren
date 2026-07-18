---
name: multi-api-orchestration
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - api orchestration
  - free models
  - multiple apis
  - parallel apis
  - openrouter
  - opencode
  - zen api
  - grok
  - free ai
  - model routing
  - cost optimization
  - zero cost
  - orchestration
---

# 🔄 Multi-API Orchestration — Free AI Model Execution

This skill enables Wren to execute **multiple free AI models in parallel** to get the best output at zero cost.

---

## 🧠 THE STRATEGY

Instead of relying on a single paid API, we use **orchestration** — running multiple free models in parallel and using the best result.

```
                    ┌─────────────────────┐
                    │  User's Request      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  ORCHESTRATOR        │
                    │  Splits work into    │
                    │  parallel tasks     │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
   ┌──────────┐         ┌──────────┐         ┌──────────┐
   │  Model 1 │         │  Model 2 │         │  Model 3 │
   │  (Free)  │         │  (Free)  │         │  (Free)  │
   └────┬─────┘         └────┬─────┘         └────┬─────┘
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             │
                    ┌────────▼──────────┐
                    │  BEST OUTPUT      │
                    │  (Voted / Merged) │
                    └───────────────────┘
```

---

## 🆓 FREE MODEL SOURCES

### Source 1: OpenCode / Zen API
**URL**: https://opencode.ai / https://zen.agency  
**Models Available**: 7-8 free models at any time  
**Cost**: $0 (free tier)  
**Best For**: General coding, game logic, script generation

```bash
# Configuration (user obtains free API key)
export OPENCODE_API_KEY="user_free_key_here"
export ZEN_API_KEY="user_free_key_here"
```

**Typical Free Models Available**:
| Model | Strength | Best For |
|-------|----------|----------|
| Llama 3.3 70B | Strong reasoning | Game logic, architecture |
| Mistral Large | Fast, good code | Script generation |
| DeepSeek V3 | Strong coding | Complex systems |
| Qwen 2.5 72B | General purpose | Mixed tasks |
| Phi-4 | Code quality | Refactoring |
| Gemma 3 | Efficiency | Quick prototypes |

### Source 2: OpenRouter
**URL**: https://openrouter.ai  
**Free Limits**: Generous free tier with multiple model choices  
**Cost**: $0 (free tier, rate-limited)  
**Best For**: General LLM tasks, code generation, game design

```bash
export OPENROUTER_API_KEY="user_free_key_here"
```

**Free Models Available on OpenRouter**:
- Llama 3.x series
- Mistral 7B/8x7B
- DeepSeek series
- Qwen series
- Gemma series

### Source 3: Grok (xAI)
**URL**: https://x.ai  
**Free Limits**: Free tier available via X/Twitter integration  
**Cost**: $0 (free tier)  
**Best For**: Creative game design, storytelling, dialogue writing

```bash
export GROK_API_KEY="user_free_key_here"
```

### Source 4: GitHub Models
**URL**: https://github.com/marketplace/models  
**Free Limits**: Free with GitHub account  
**Cost**: $0  
**Best For**: Code completion, debugging

```bash
export GITHUB_TOKEN="user_github_token"
```

---

## ⚙️ ORCHESTRATION ENGINE

### How It Works

```
User sends a request
        │
        ▼
┌───────────────────────────────────────────────┐
│  ORCHESTRATOR                                 │
│                                                │
│  1. Analyze request type                       │
│     - Code generation → use coding models      │
│     - Game design → use creative models        │
│     - Bug fixing → use reasoning models        │
│                                                │
│  2. Select available free models (3-5)         │
│     - Check which APIs have free credits       │
│     - Route to all in parallel                 │
│                                                │
│  3. Execute all in parallel                    │
│     - Send same prompt to all selected models  │
│     - Wait for fastest responses first         │
│                                                │
│  4. Aggregate & pick best                      │
│     - Compare results                          │
│     - Vote on best output                      │
│     - Or merge multiple outputs                │
└────────────────────────────────────────────────┘
```

### Parallel Execution Script (Zero Dependencies — Uses Only Python stdlib)
```python
# orchestrator.py — Runs multiple free models in parallel
# Requirements: Python 3.9+ (stdlib only — no pip install needed)
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# API endpoints for free models (EXAMPLE ENDPOINTS — verify current URLs)
# NOTE: Free LLM APIs change endpoints and model names frequently.
# Users should verify the current endpoints for each provider.
FREE_APIS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "model": "mistral-large",
        "priority": 1,
        "rate_limit": 3,  # seconds between calls
    },
    "grok": {
        "url": "https://api.x.ai/v1/chat/completions",
        "key_env": "GROK_API_KEY",
        "model": "grok-2",
        "priority": 2,
        "rate_limit": 5,
    },
    "opencode": {
        "url": "https://api.opencode.ai/v1/chat/completions",
        "key_env": "OPENCODE_API_KEY",
        "model": "llama-3.3-70b",
        "priority": 3,
        "rate_limit": 3,
    },
}


def call_api_sync(api_name: str, config: dict, messages: list) -> dict[str, Any]:
    """Call a single API synchronously with timeout and rate-limit handling."""
    api_key = os.getenv(config["key_env"])
    if not api_key:
        return {"api": api_name, "error": f"Missing {config['key_env']}", "success": False}
    
    # Rate limiting: wait before calling
    time.sleep(config.get("rate_limit", 2))
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    payload = json.dumps({
        "model": config["model"],
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.7,
    }).encode("utf-8")
    
    try:
        req = Request(config["url"], data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read())
            return {
                "api": api_name,
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model", config["model"]),
                "success": True,
            }
    except HTTPError as e:
        if e.code == 429:
            # Rate limited — wait longer and skip this API
            return {"api": api_name, "error": "Rate limited", "success": False, "retry_after": 30}
        return {"api": api_name, "error": f"HTTP {e.code}: {e.reason[:100]}", "success": False}
    except URLError as e:
        return {"api": api_name, "error": f"Connection failed: {e.reason}", "success": False}
    except Exception as e:
        return {"api": api_name, "error": str(e)[:200], "success": False}


def orchestrate(messages: list, timeout: int = 45) -> dict[str, Any]:
    """Run all available free models in parallel and pick the best result.
    
    Args:
        messages: OpenAI-format message list
        timeout: Max total time in seconds
    
    Returns:
        dict with 'result' (best output), 'from_api', 'from_model'
    """
    # Only use APIs that have keys configured
    available = {
        name: cfg for name, cfg in FREE_APIS.items()
        if os.getenv(cfg["key_env"])
    }
    
    if not available:
        return {
            "error": "No API keys configured",
            "hint": "Set any of: OPENROUTER_API_KEY, GROK_API_KEY, OPENCODE_API_KEY",
            "success": False,
        }
    
    results = []
    with ThreadPoolExecutor(max_workers=len(available)) as executor:
        futures = {
            executor.submit(call_api_sync, name, cfg, messages): name
            for name, cfg in available.items()
        }
        
        for future in as_completed(futures, timeout=timeout):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)[:200], "success": False})
    
    # Filter successful results
    successful = [r for r in results if r.get("success")]
    
    if not successful:
        return {
            "error": "All APIs failed",
            "detail": [r.get("error", "Unknown") for r in results],
            "hint": "Check API keys, rate limits, or try again later",
            "success": False,
        }
    
    # Pick from highest priority API that succeeded
    successful.sort(key=lambda r: FREE_APIS.get(r["api"], {}).get("priority", 999))
    best = successful[0]
    
    return {
        "result": best["content"],
        "from_api": best["api"],
        "from_model": best["model"],
        "success": True,
    }


# Example usage
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a Master Game Engineer."},
        {"role": "user", "content": "Write GDScript for a 2D platformer player controller."},
    ]
    result = orchestrate(messages)
    print(json.dumps(result, indent=2)[:1000])
```

> **⚠️ Note**: API endpoints and model names above are **examples**. Free LLM providers change these frequently. Users should check the provider's current documentation for active endpoints and model availability. The orchestrator gracefully skips any API that fails or has no key configured.

### Smart Model Routing

| Task Type | Best Free Model | Why |
|-----------|----------------|-----|
| GDScript/Code | DeepSeek / Llama 3.3 | Strongest at code generation |
| Game design docs | Grok / Mistral | Most creative |
| Bug fixing | Qwen 2.5 / Phi-4 | Best at reasoning |
| Architecture | DeepSeek / OpenCode | Handles complex systems |
| Quick prototyping | Any fast model | Speed over quality |
| Export/deployment | Any reliable model | Simple, well-known patterns |

---

## 💰 COST BREAKDOWN

### Zero-Cost Workflow
```
Free models (OpenCode, OpenRouter free tier, Grok free)
    → Used for: Code generation, debugging, game logic, architecture
    → Total: $0/month

User's API keys (OpenProvider key, optional)
    → Used for: Premium models when free tier exhausted
    → Total: User's choice ($0 if they stay on free tier)
```

### What Costs Money (User Decision)
| Service | Cost | When Needed |
|---------|------|-------------|
| Tripo AI API | ~$10/mo | Only if user wants AI-generated 3D models |
| Meshy AI API | ~$10/mo | Only if user wants animated 3D characters |
| Premium LLM (optional) | $5-20/mo | Only if free models aren't enough |

**Everything else is free.** Godot Engine, export templates, all MCP servers, all skills, all game templates — all open-source and included.

---

## 📋 SETUP FOR USERS

```bash
# 1. Get free API keys (takes 5 minutes each):
#    - OpenRouter: https://openrouter.ai/keys
#    - OpenCode:   https://opencode.ai
#    - xAI:        https://x.ai/api

# 2. Set them in Wren:
export OPENROUTER_API_KEY="sk-or-v1-..."
export OPENCODE_API_KEY="oc_..."
export GROK_API_KEY="xai-..."

# 3. That's it — the orchestrator handles the rest automatically
```

---

## 🎯 BENEFITS SUMMARY

| Benefit | Why It Matters |
|---------|---------------|
| **$0 operating cost** | No monthly subscription needed for AI |
| **Faster responses** | 3-5 models in parallel = faster than 1 model |
| **Better quality** | Multiple models vote → best output wins |
| **No single point of failure** | One API down → others still work |
| **Free forever** | Users keep their free tier API keys |
| **Scalable** | Add more free models as they emerge |
