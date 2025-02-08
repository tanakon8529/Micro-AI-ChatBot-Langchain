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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Tanakon Kabprapun

---
⭐ If you find this project helpful, please consider giving it a star!