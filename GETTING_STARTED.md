# 🚀 Getting Started with Wren

Welcome to **Wren**, the self-hosted AI engineering platform! This guide will walk you through setting up and running Wren on your machine.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running Wren](#running-wren)
5. [First Steps](#first-steps)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## 📦 System Requirements

Before you begin, ensure your system meets these requirements:

### Minimum Requirements

- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk Space**: 5GB+ free space
- **Internet**: Required for LLM provider communication

### Software Dependencies

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Node.js** | 22.12.x or later | Frontend runtime | [nodejs.org](https://nodejs.org/) |
| **Python** | 3.12 - 3.13 | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **Git** | 2.0+ | Version control | [git-scm.com](https://git-scm.com/) |
| **Docker** | (Optional) | Sandboxed execution | [docker.com](https://www.docker.com/products/docker-desktop) |

### Verify Your Installation

```bash
# Check Node.js
node --version
# Expected: v22.12.0 or higher

# Check Python
python3 --version
# Expected: Python 3.12 or higher

# Check Git
git --version
# Expected: git version 2.0 or higher
```

---

## 📥 Installation

### Step 1: Clone the Repository

```bash
# Clone Wren repository
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren
```

### Step 2: Install Poetry (Python Dependency Manager)

Wren uses **Poetry** for Python dependency management. Install it if you haven't already:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to your PATH (if not already done)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

### Step 3: Run the Build Script

This will install all dependencies for both frontend and backend:

```bash
# Run the build command (this may take 5-10 minutes)
make build
```

**What does `make build` do?**
- ✅ Checks system dependencies
- ✅ Installs Python dependencies via Poetry
- ✅ Installs Node.js dependencies via npm
- ✅ Sets up pre-commit hooks for code quality
- ✅ Builds the frontend

---

## ⚙️ Configuration

### Step 1: Set Up Your LLM Provider

Wren requires an LLM API key. Choose one:

#### Option A: OpenAI (Recommended for beginners)

```bash
# Sign up at: https://platform.openai.com
# Create an API key at: https://platform.openai.com/api-keys

# Set environment variable
export LLM_API_KEY="sk-your-openai-key-here"
export LLM_MODEL="gpt-4o"
```

#### Option B: Anthropic Claude

```bash
# Sign up at: https://console.anthropic.com
# Create an API key

export LLM_API_KEY="sk-ant-your-anthropic-key"
export LLM_MODEL="claude-3-5-sonnet-20241022"
```

#### Option C: Local LLM (Advanced)

```bash
# Use Ollama or similar local LLM server
export LLM_API_KEY="local"
export LLM_MODEL="llama2"
export LLM_BASE_URL="http://localhost:11434/v1"
```

### Step 2: Create Configuration File (Optional)

Create a `config.toml` file for persistent configuration:

```bash
# Interactive setup
make setup-config

# Or manually create config.toml
cat > config.toml << EOF
[core]
workspace_base = "./workspace"

[llm]
model = "gpt-4o"
api_key = "sk-your-openai-key-here"
EOF
```

### Step 3: Set Environment Variables

```bash
# Create .env file (optional)
cat > .env << EOF
# LLM Configuration
LLM_API_KEY=sk-your-openai-key-here
LLM_MODEL=gpt-4o

# Server Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=3000
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=3001

# Workspace
WORKSPACE_DIR=./workspace
EOF

# Load environment variables
source .env
```

---

## 🎯 Running Wren

### Option 1: Local Development (Recommended for First Run)

```bash
# Set your LLM API key
export LLM_API_KEY="sk-your-key"

# Start Wren
make run
```

**What happens?**
- Backend starts on `http://localhost:3000`
- Frontend starts on `http://localhost:3001`
- Both services connect via WebSocket

**Open your browser to:** [http://localhost:3001](http://localhost:3001)

### Option 2: Separate Frontend & Backend

```bash
# Terminal 1: Start Backend
LLM_API_KEY="sk-your-key" make start-backend

# Terminal 2: Start Frontend
make start-frontend
```

### Option 3: Docker (Production-like)

```bash
# Build and run in Docker
make docker-run

# Access at: http://localhost:3001
```

---

## 🎓 First Steps

### 1. Create Your First Project

Once Wren is running:

1. Open [http://localhost:3001](http://localhost:3001)
2. Click **"New Project"** or **"Start Chat"**
3. Enter your LLM API key (if not set globally)
4. Select your preferred mode:
   - **🎯 Vibe Code** — Interactive coding
   - **⚡ Autonomous** — Self-driving agent
   - **🎮 Game** — Game development

### 2. Ask Wren to Build Something

```
💬 You: "Build me a simple React Todo app with TypeScript"

🤖 Wren will:
  1. Analyze your request
  2. Create a plan
  3. Generate code files
  4. Run the application
  5. Show you a preview
```

### 3. Review & Iterate

- Review generated code in the **Review Panel**
- Add comments or suggest changes
- Let Wren iterate and improve
- Execute code and see results in real-time

---

## 🔧 Troubleshooting

### Issue: "Port 3001 already in use"

```bash
# Find what's using port 3001
lsof -i :3001

# Kill the process
kill -9 <PID>

# Or use a different port
make run FRONTEND_PORT=3002
```

### Issue: "Python version error"

```bash
# Verify Python version
python3 --version

# If wrong version, install correct version or use pyenv
# macOS:
brew install python@3.12

# Linux (Ubuntu/Debian):
sudo apt install python3.12 python3.12-venv
```

### Issue: "ModuleNotFoundError: No module named 'wren'"

```bash
# Reinstall Python dependencies
poetry install

# Or activate Poetry environment
poetry shell
poetry install
```

### Issue: "npm ERR! code ERESOLVE"

```bash
# Clear npm cache and reinstall
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Issue: "Connection refused to LLM API"

```bash
# 1. Check your LLM API key
echo $LLM_API_KEY

# 2. Test the API key
curl https://api.openai.com/v1/models -H "Authorization: Bearer $LLM_API_KEY"

# 3. If using local LLM, verify it's running
curl http://localhost:11434/api/tags
```

---

## 🚀 Next Steps

### Learn More

- **[Development Guide](./Development.md)** — Advanced development setup
- **[Agent Architecture](./AGENTS.md)** — How Wren's agents work
- **[API Documentation](./docs/)** — REST and WebSocket APIs
- **[Skills Guide](./skills/)** — Creating custom AI skills

### Join the Community

- 💬 **[Discord](https://discord.gg/example)** — Chat with developers
- 🐛 **[Issues](https://github.com/Daniel-debug-boop/Wren/issues)** — Report bugs
- 💡 **[Discussions](https://github.com/Daniel-debug-boop/Wren/discussions)** — Share ideas
- 📖 **[Documentation](https://wren.dev)** — Full docs site

### Tips for Success

✅ **Start simple** — Begin with basic coding tasks  
✅ **Review code** — Always check generated code before running  
✅ **Use skills** — Leverage domain-specific skills for better results  
✅ **Iterate** — Let agents learn and improve over multiple turns  
✅ **Experiment** — Try different modes and LLM providers  

---

## 📞 Getting Help

### Quick Questions?

1. Check [Troubleshooting](#troubleshooting) above
2. Search [Existing Issues](https://github.com/Daniel-debug-boop/Wren/issues)
3. Ask in [Discussions](https://github.com/Daniel-debug-boop/Wren/discussions)

### Found a Bug?

Report it on [GitHub Issues](https://github.com/Daniel-debug-boop/Wren/issues) with:
- Your OS and Python version
- Steps to reproduce
- Error messages or logs
- Expected vs actual behavior

---

<div align="center">
  <p><strong>Ready to build with Wren?</strong></p>
  <p>
    <a href="http://localhost:3001">→ Open Wren</a> |
    <a href="./README.md">← Back to README</a>
  </p>
</div>
