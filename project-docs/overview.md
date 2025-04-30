# AI Companion Project Overview

## Project Description

The AI Companion is a conversational AI system that provides intelligent responses and assistance using advanced language models. It is designed to understand user queries, provide relevant information, and assist with various tasks through natural language interaction.

## Core Components

1. **Backend Services**
   - Python-based AI processing engine
   - Azure OpenAI integration for advanced language models
   - Vector database (Qdrant) for semantic search
   - Supabase for authentication and data storage

2. **Frontend Interface**
   - Next.js web application
   - Modern UI with responsive design
   - Real-time chat functionality

3. **Deployment Infrastructure**
   - Azure Container Apps
   - Azure Container Registry
   - Optimized Docker images for cloud deployment

## Docker Optimization

The project now includes optimized Docker configurations specifically designed for Azure deployment:

- **60-70% smaller Docker images** through multi-stage builds
- **Azure-specific base images** for better compatibility and performance
- **Improved build caching** for faster deployments
- **Health monitoring** integration for robust production environments

The deployment system provides a customizable experience allowing users to:
- Use optimized builds by default
- Option to use original builds if needed for specific use cases
- Transparent size reduction without functionality changes

## Key Features

- Conversational AI interface for natural interaction
- Memory and context retention across conversations
- Integration with external knowledge sources
- Secure authentication and user management
- Responsive design for desktop and mobile use
- Optimized cloud deployment

## Getting Started

See the following documentation for details:

- [Requirements & Features](./requirements.md)
- [Technical Specifications](./tech-specs.md)
- [Azure Deployment Guide](./azure-deployment.md)
- [User Flow & Project Structure](./user-structure.md) 