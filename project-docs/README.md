# Project Documentation Organization

This document provides a guide for organizing the project documentation. Below is the recommended folder structure and file organization.

## Folder Structure

```
project-docs/
├── core/
│   ├── overview.md
│   ├── requirements.md
│   ├── tech-specs.md
│   ├── user-structure.md
│   └── timeline.md
├── architecture/
│   ├── scheduled_messaging_architecture.md
│   └── other architecture documents
├── diagrams/
│   ├── architecture-diagram.mmd
│   ├── deployment-architecture.mmd
│   ├── rag-flow.mmd
│   └── scheduled-messaging-flow.mmd
├── database/
│   ├── database-schema.md
│   ├── database-integration.md
│   └── schema_updates.md
├── api/
│   └── api-structure.md
├── deployment/
│   ├── AZURE-CONTAINER-APP-DEPLOYMENT.md
│   ├── CUSTOM-DOMAIN-SETUP.md
│   ├── azure-deployment.md
│   ├── azure-deployment-summary.md
│   ├── docker-interfaces.md
│   └── scheduled_messaging_deployment.md
├── implementation/
│   ├── implementation_roadmap.md
│   ├── plan.md
│   ├── processor_enhancements.md
│   └── scheduled_messaging_implementation.md
├── rag/
│   ├── rag.md
│   └── url_prioritization_guide.md
├── features/
│   ├── scheduled-messaging.md
│   ├── patient-registration.md
│   └── evelina_personality.md
├── interfaces/
│   ├── telegram.md
│   └── other interface documents
├── monitoring/
│   ├── logging.md
│   └── monitoring.md
└── testing/
    ├── telegram_tests.md
    └── message_delivery_test_plan.md
```

## Guide for File Organization

1. **Core Documentation**
   - Put main project documentation files in the `core` folder
   - These include overview, requirements, tech specs, etc.

2. **Architecture**
   - Architecture-related documents go here
   - Focus on system design and component interactions

3. **Diagrams**
   - All `.mmd` diagram files should be placed here
   - Mermaid diagrams for architecture, flows, etc.

4. **Database**
   - Database schemas, migration plans, and integration docs

5. **API**
   - API structure and reference documentation

6. **Deployment**
   - All deployment-related guides and documentation
   - Azure, Docker, and other deployment platforms

7. **Implementation**
   - Implementation details, roadmaps, and plans
   - Specific module implementation documents

8. **RAG**
   - Retrieval Augmented Generation related documentation

9. **Features**
   - Documentation for specific product features

10. **Interfaces**
    - Interface-specific documentation (telegram, web, etc.)

11. **Monitoring**
    - Monitoring and logging documentation

12. **Testing**
    - Test plans and testing-related documentation

## How to Use This Structure

1. When adding new documentation, place it in the appropriate folder
2. Keep file names consistent (use kebab-case or snake_case consistently)
3. Update cross-references when moving files
4. When reusing information, consider linking rather than duplicating content

## Files to Clean Up

- Remove duplicate or obsolete documents
- Consolidate similar documents where appropriate
- Convert any non-markdown documents to markdown format for consistency 