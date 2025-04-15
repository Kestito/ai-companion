# AI Companion

An AI companion application using LangChain and modern AI technologies.

## Features

- WhatsApp integration
- Telegram integration
  - Patient registration on first contact
  - Conversation capabilities with context memory
  - Command-based scheduling functionality
  - Complete user journey testing
- RAG capabilities
- Speech-to-text and text-to-speech
- Image analysis

## Setup

1. Clone the repository
2. Install dependencies with `uv sync`
3. Run the application with `fastapi run ai_companion/interfaces/whatsapp/webhook_endpoint.py`
4. For Telegram bot, run `fastapi run ai_companion/interfaces/telegram/bot.py`

## Environment Variables

See the `.env` file for required environment variables.

## Testing

### Telegram Interface

The Telegram interface includes standalone tests that simulate user interactions:

```bash
# Run complete Telegram user flow test
python src/ai_companion/interfaces/telegram/test_full_user_flow.py

# Run individual component tests
python src/ai_companion/interfaces/telegram/test_patient_creation.py
python src/ai_companion/interfaces/telegram/test_existing_patient.py
python src/ai_companion/interfaces/telegram/test_schedule_message.py
```

See [Telegram Interface Documentation](project-docs/interfaces/telegram.md) and [Telegram Test Guide](project-docs/testing/telegram_tests.md) for more details.

<p align="center">
        <img alt="logo" src="img/project_overview_diagram.gif" width=600 />
    <h1 align="center">📱 Evelina 📱</h1>
    <h3 align="center">Turning the Turing Test into a Whatsapp Agent</h3>
</p>

<p align="center">
    <img alt="logo" src="img/whatsapp_logo.png" width=100 />
</p>

startuoti studio - langgraph dev 
startuoti whatsapp webhook endpoint - uvicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint:app --reload --log-level debug --port 8080 
startuoti - docker run -p 8000:8000 --env-file .env evelina-chainlit

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Course Overview](#course-overview)
- [The tech stack](#the-tech-stack)
- [Course Outline](#course-outline)
  - [🛠️ Lesson 0: Before we begin](#️-lesson-0-before-we-begin)
  - [🏗️ Lesson 1: Project overview](#️-lesson-1-project-overview)
  - [🕸️ Lesson 2: Dissecting Evelina's brain](#️-lesson-2-dissecting-evelinas-brain)
  - [🧠 Lesson 3: Unlocking Evelina's memories](#-lesson-3-unlocking-evelinas-memories)
  - [🗣️ Lesson 4: Giving Evelina a Voice](#️-lesson-4-giving-evelina-a-voice)
  - [👀 Lesson 5: Evelina learns to see](#-lesson-5-evelina-learns-to-see)
  - [📱 Lesson 6: Evelina installs Whatsapp](#-lesson-6-evelina-installs-whatsapp)
- [Contributors](#contributors)
- [License](#license)

## Course Overview

<p align="center">
    <img alt="logo" src="img/ex_machina_faceswap.jpg" width=400 />
</p>

What happens when [two ML Engineers](#contributors) with a love for sci-fi movies team up? 🤔

You get **Evelina**, a Whatsapp agent that can engage with users in a "realistic" way, inspired by the great film [Ex Machina](https://www.imdb.com/es-es/title/tt0470752/). Ok, you won't find a fully sentient robot here, but you **will** have some pretty interesting Whatsapp conversations.

>You can think of it as a modern reinterpretation of the Turing Test 🤣

By the end of this course, you'll have built your own Evelina too, capable of:


* Receiving and sending Whatsapp messages 📲
* Understanding your voice 🗣️
* Recognizing your images 🖼️
* Sending voice notes back 🎤
* Sharing updates about its "daily activities" 🚣
* Sending you images of its current activities 🖼️

Excited? Let's get started! 

## The tech stack

<table>
  <tr>
    <th>Technology</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><img src="img/groq_logo.png" width="100" alt="Groq Logo"/></td>
    <td>Powering the project with Llama 3.3, Llama 3.2 Vision, and Whisper. Groq models are awesome (and fast!!)</td>
  </tr>
  <tr>
    <td><img src="img/qdrant_logo.png" width="100" alt="Qdrant Logo"/></td>
    <td>Serving as the long-term database, enabling our agent to recall details you shared months ago.</td>
  </tr>
  <tr>
    <td><img src="img/cloud_run_logo.png" width="100" alt="Cloud Run Logo"/></td>
    <td>Deploying your containers easily to Google Cloud Platform</td>
  </tr>
  <tr>
    <td><img src="img/langgraph_logo.png" width="100" alt="LangGraph Logo"/></td>
    <td>Learn how to build production-ready LangGraph workflows</td>
  </tr>
  <tr>
    <td><img src="img/elevenlabs_logo.png" width="100" alt="ElevenLabs Logo"/></td>
    <td>Amazing TTS models</td>
  </tr>
  <tr>
    <td><img src="img/together_logo.png" width="100" alt="Together AI Logo"/></td>
    <td>Behind Evelina's image generation process</td>
  </tr>
</table>

## Course Outline

This course is divided into 6 lessons. Each lesson is a step forward in building Evelina, and it has a written and video version. 

These two versions are complementaty, so we recommend you to go through both, as it will improve your learning experience. Don't forget to check the [Before we start](#before-we-start) section to get everything ready for the course.

---

### 🛠️ Lesson 0: Before we begin

This project uses a lot of services and tools, so we need to get everything ready before we start. Follow the instructions in [this document](docs/before_we_begin.md).

---

### [🏗️ Lesson 1: Project overview](https://theneuralmaze.substack.com/p/meet-evelina-the-whatsapp-agent)

Date: **2025-02-05**

<p align="center">
        <img alt="lesson1" src="img/lesson1.png" width=400 />
</p>

The first lesson is about getting to know the project and its general structure. 

> 🔗 Article ✨ [Meet Evelina - The WhatsApp Agent](https://theneuralmaze.substack.com/p/meet-evelina-the-whatsapp-agent)

<div align="center">
  <a href="https://youtu.be/u5y06cFK2WA?si=RCx__sJNtr2DYf0U">
    <img src="img/video_thumbnails/thumbnail_1_play.png" alt="Watch the video" width=400/>
  </a>
</div>

---

### [🕸️ Lesson 2: Dissecting Evelina's brain](https://theneuralmaze.substack.com/p/dissecting-evelinas-brain)

Date: **2025-02-12**

<p align="center">
        <img alt="lesson2" src="img/lesson2.png" width=400 />
</p>

Lesson 2 is about LangGraph. Simple as that. You'll learn about graphs, state, nodes and edges and understand how Evelina's "brain" actually works.

> 🔗 Article ✨ [Dissecting Evelina's brain](https://theneuralmaze.substack.com/p/dissecting-evelinas-brain)

<div align="center">
  <a href="https://youtu.be/nTsLL3htkCU?si=aSmSkpL-U3rzw9Za">
    <img src="img/video_thumbnails/thumbnail_2_play.png" alt="Watch the video" width=400/>
  </a>
</div>

---

### 🧠 Lesson 3: Unlocking Evelina's memories
        
Date: **2025-02-19**

> WIP ... 👷

---

### 🗣️ Lesson 4: Giving Evelina a Voice

Date: **2025-02-26**

> WIP ... 👷

---

### 👀 Lesson 5: Evelina learns to see

Date: **2025-03-05**

> WIP ... 👷

---

### 📱 Lesson 6: Evelina installs Whatsapp

Date: **2025-03-12**

> WIP ... 👷

---

## Contributors

<table>
  <tr>
    <td><img src="https://github.com/MichaelisTrofficus.png" width="100" style="border-radius:50%;"/></td>
    <td>
      <strong>Miguel Otero Pedrido | Senior ML / AI Engineer </strong><br />
      <i>Founder of The Neural Maze. Rick and Morty fan.</i><br /><br />
      <a href="https://www.linkedin.com/in/migueloteropedrido/">LinkedIn</a><br />
      <a href="https://www.youtube.com/@TheNeuralMaze">YouTube</a><br />
      <a href="https://theneuralmaze.substack.com/">The Neural Maze Newsletter</a>
    </td>
  </tr>
  <tr>
    <td><img src="https://github.com/jesuscopado.png" width="100" style="border-radius:50%;"/></td>
    <td>
      <strong>Jesús Copado | Senior ML / AI Engineer </strong><br />
      <i>Equal parts cinema fan and AI enthusiast.</i><br /><br />
      <a href="https://www.youtube.com/@jesuscopado-en">YouTube</a><br />
      <a href="https://www.linkedin.com/in/copadojesus/">LinkedIn</a><br />
    </td>
  </tr>
</table>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Project Documentation Structure

This folder contains all documentation for the AI Companion project. Documents are organized by category to make information easier to find.

## Folder Structure

- **core/**: Core project information
  - Overview, requirements, technical specifications, project timeline, etc.

- **architecture/**: System architecture documentation
  - Architectural diagrams, system flows, component relationships

- **diagrams/**: Visual diagrams
  - Mermaid diagrams (.mmd files) and other visual representations

- **database/**: Database related documentation
  - Schema definitions, database integration details, schema updates

- **api/**: API documentation
  - API structures, endpoints, request/response formats

- **deployment/**: Deployment instructions
  - Azure deployment, Docker setup, custom domain configuration

- **implementation/**: Implementation details
  - Development plans, roadmaps, specific implementation guides

- **rag/**: RAG (Retrieval-Augmented Generation) documentation
  - RAG configuration, usage guides, URL prioritization

- **features/**: Feature specifications
  - Detailed documentation for individual features

- **interfaces/**: Interface documentation
  - Web UI, Chainlit, and other user interfaces

- **monitoring/**: Monitoring and logging
  - Logging configuration, monitoring setup

- **testing/**: Testing documentation
  - Test plans, testing methodologies

- **troubleshooting/**: Troubleshooting guides
  - Common issues and fixes, websocket issues, performance optimizations

## File Organization

All documentation files are organized in Markdown (.md) format. Related diagram files are placed in the diagrams folder.

## Contributing

When adding new documentation:
1. Place the file in the appropriate folder
2. Follow the existing naming conventions
3. Link to related documentation when relevant
4. Update this README if you create new categories

For any questions about the documentation structure, contact the project maintainers.