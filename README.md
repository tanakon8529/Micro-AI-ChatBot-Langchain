# 🤖 Micro-AI-ChatBot-Langchain

A powerful, microservices-based AI chatbot built with FastAPI, LangChain, and Redis, featuring OAuth2 authentication and vector-based conversation memory.

## 🌟 Features

- 🔒 OAuth2 Authentication System
- 💬 AI-powered Conversational Interface
- 🧠 Vector-based Memory using FAISS
- 🔄 Redis Cache Integration
- 🚀 FastAPI Microservices Architecture
- 🐳 Docker Containerization
- 📝 Conversation History Management
- 🔍 Advanced Query Processing

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI
- **AI/ML**: LangChain, OpenAI, FAISS
- **Cache**: Redis
- **Authentication**: OAuth2
- **Containerization**: Docker
- **Testing**: Pytest
- **Documentation**: Postman Collection

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- .env file (copy from .envexample)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/tanakon8529/Micro-AI-ChatBot-Langchain.git
cd Micro-AI-ChatBot-Langchain
```

2. Set up environment variables:
```bash
cp .envexample .env
# Edit .env with your configuration
```

3. Start the application:
```bash
sh ./start.sh
```

### 🧹 Cleanup

To stop and clean up containers:
```bash
# Stop and remove containers
docker compose down

# Remove all containers and cleanup (optional)
docker compose down -v
docker system prune -f
docker builder prune -a -f
docker images -f "dangling=true" -q | xargs -r docker rmi
```

## 🔌 API Endpoints

### OAuth2 Service
- `POST /v1/token/` - Generate access token
- `GET /v1/protected/` - Test protected route

### AI Chat Service
- `POST /v1/ask/` - Send questions to AI chatbot
- `POST /v1/conversation/` - Get conversation history
- `POST /v1/test/` - Test route for AI chatbot

## 📁 Project Structure

```
Micro-AI-ChatBot-Langchain/
├── src/
│   ├── fastapi-ai-chat/      # AI Chat Service
│   ├── fastapi-oauth2/       # OAuth2 Service
│   ├── share/                # Shared Utilities
│   └── tests/               # Test Files
├── postman/                  # API Documentation
├── docker-compose.yml        # Docker Compose Config
├── copy-env.sh              # Environment Setup Script
└── start.sh                 # Startup Script
```

## 📚 Documentation

Complete API documentation is available in the Postman collection:
- `postman/Micro-AI-ChatBot-Langchain.postman_collection.json`
- `postman/Micro-AI-ChatBot-Langchain (Dev).postman_environment.json`

## 🚀 CI/CD Pipeline

This project includes mockup GitHub Actions workflows for CI/CD. These are templates that you can customize for your needs.

### Workflow Templates

1. **Test (`test.yml`)**
   - Template for running unit tests, integration tests, and load tests
   - Includes mock Redis service setup
   - Placeholders for test commands and coverage reporting
   - ⚠️ **Customize**: Add your actual test commands and dependencies

2. **Build and Push (`build-and-push.yml`)**
   - Template for building and pushing Docker images to ECR
   - Mock steps for AWS authentication and ECR operations
   - ⚠️ **Customize**: Update AWS region, repository names, and build commands

3. **Deploy (`deploy.yml`)**
   - Template for ECS deployment
   - Mock steps for updating task definitions and services
   - ⚠️ **Customize**: Add your cluster, service names, and health checks

### Required Secrets

Add these to your GitHub repository settings:
```bash
AWS_ROLE_ARN          # For AWS authentication
MOCK_API_KEY          # Example API key - replace with your actual secrets
```

### How to Use These Templates

1. **Setup**:
   - Copy the workflow files to your `.github/workflows` directory
   - Update environment variables in each workflow
   - Replace mock commands with your actual commands

2. **Customization Points**:
   - Look for `# CUSTOMIZE:` comments in the workflows
   - Replace mock commands (echo statements) with real commands
   - Update service names and AWS resource identifiers
   - Add your specific build and test requirements

3. **Testing Locally**:
   ```bash
   # Test workflow syntax
   act -n

   # Run workflows locally (requires act)
   act -j test
   act -j build
   act -j deploy
   ```

### AWS Infrastructure Requirements

1. **ECR Setup**:
   ```bash
   # Create repositories
   aws ecr create-repository --repository-name my-app
   ```

2. **ECS Setup**:
   ```bash
   # Create cluster
   aws ecs create-cluster --cluster-name my-cluster

   # Create service
   aws ecs create-service ...
   ```

3. **IAM Roles**:
   - GitHub Actions role
   - ECS task execution role
   - ECS task role

### Local Development

For local testing without AWS:
```bash
# Run mock tests
./mock_tests.sh

# Build locally
docker compose up --build
```

## 📦 Release Process

This project uses semantic-release for automated versioning and changelog generation. Releases are triggered automatically on the main branch based on conventional commit messages.

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types that trigger releases:
- `feat`: Minor release (new feature)
- `fix`: Patch release (bug fix)
- `perf`: Patch release (performance improvement)
- `docs`: Patch release (if scope is "readme")
- `BREAKING CHANGE`: Major release (in commit body)

Examples:
```bash
feat(api): add new chat endpoint
fix(auth): resolve token validation issue
docs(readme): update installation guide
perf(cache): improve Redis query performance
```

### Automatic Releases

The release workflow:
1. Analyzes commits since last release
2. Determines version bump (major.minor.patch)
3. Generates CHANGELOG.md
4. Creates GitHub release
5. Tags Docker images with version

### Manual Release

For manual releases (if needed):
```bash
# Install dependencies
npm install

# Run semantic-release locally
npx semantic-release
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Tanakon Kabprapun

---
⭐ If you find this project helpful, please consider giving it a star!