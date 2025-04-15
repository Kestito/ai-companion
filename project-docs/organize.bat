@echo off
REM This script organizes the project-docs folder according to the README.md structure

REM Create folders if they don't exist
echo Creating directory structure...
mkdir "core" 2>nul
mkdir "architecture" 2>nul
mkdir "diagrams" 2>nul
mkdir "database" 2>nul
mkdir "api" 2>nul
mkdir "deployment" 2>nul
mkdir "implementation" 2>nul
mkdir "rag" 2>nul
mkdir "features" 2>nul
mkdir "interfaces" 2>nul
mkdir "monitoring" 2>nul
mkdir "testing" 2>nul

REM Copy core documents
echo Organizing core documents...
copy "overview.md" "core\" /Y
copy "requirements.md" "core\" /Y
copy "tech-specs.md" "core\" /Y
copy "user-structure.md" "core\" /Y
copy "timeline.md" "core\" /Y

REM Copy architecture documents
echo Organizing architecture documents...
copy "scheduled_messaging_architecture.md" "architecture\" /Y

REM Copy diagrams
echo Organizing diagrams...
copy "architecture-diagram.mmd" "diagrams\" /Y
copy "deployment-architecture.mmd" "diagrams\" /Y
copy "rag-flow.mmd" "diagrams\" /Y
copy "scheduled-messaging-flow.mmd" "diagrams\" /Y

REM Copy database documents
echo Organizing database documents...
copy "database-schema.md" "database\" /Y
copy "database-integration.md" "database\" /Y
copy "schema_updates.md" "database\" /Y

REM Copy API documents
echo Organizing API documents...
copy "api-structure.md" "api\" /Y

REM Copy deployment documents
echo Organizing deployment documents...
copy "AZURE-CONTAINER-APP-DEPLOYMENT.md" "deployment\" /Y
copy "CUSTOM-DOMAIN-SETUP.md" "deployment\" /Y
copy "azure-deployment.md" "deployment\" /Y
copy "azure-deployment-summary.md" "deployment\" /Y
copy "docker-interfaces.md" "deployment\" /Y
copy "scheduled_messaging_deployment.md" "deployment\" /Y
copy "scheduled_messaging_azure.md" "deployment\" /Y

REM Copy implementation documents
echo Organizing implementation documents...
copy "implementation_roadmap.md" "implementation\" /Y
copy "plan.md" "implementation\" /Y
copy "processor_enhancements.md" "implementation\" /Y
copy "scheduled_messaging_implementation.md" "implementation\" /Y

REM Copy RAG documents
echo Organizing RAG documents...
copy "rag.md" "rag\" /Y
copy "url_prioritization_guide.md" "rag\" /Y

REM Copy feature documents
echo Organizing feature documents...
copy "scheduled-messaging.md" "features\" /Y
copy "patient-registration.md" "features\" /Y
copy "evelina_personality.md" "features\" /Y

REM Copy interface documents
echo Organizing interface documents...
copy "web-ui.md" "interfaces\" /Y
copy "telegram.md" "interfaces\" /Y

REM Copy monitoring documents
echo Organizing monitoring documents...
copy "logging.md" "monitoring\" /Y
copy "monitoring.md" "monitoring\" /Y

REM Copy testing documents
echo Organizing testing documents...
copy "telegram_tests.md" "testing\" /Y
copy "message_delivery_test_plan.md" "testing\" /Y

echo Organization complete. Please review the files and delete duplicates as needed.
echo See README.md for the recommended folder structure. 