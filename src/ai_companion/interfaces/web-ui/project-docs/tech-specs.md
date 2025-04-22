# Technical Specifications

## Tech Stack

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Backend:** Python with FastAPI
- **Database:** PostgreSQL with Supabase
- **Containerization:** Docker
- **Deployment:** Azure Container Apps

## Development Methods

- TypeScript for type safety
- Next.js App Router for routing
- Tailwind CSS for styling
- Supabase for authentication and database
- React for UI components

## Coding Standards

- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Ensure responsive design
- Write unit tests for critical functionality

## Database Design

The application uses Supabase (PostgreSQL) for data storage with the following main tables:

### patients

Stores information about patients in the system.

| Column | Type | Description |
|--------|------|-------------|
| id | string | Primary key |
| first_name | string | Patient's first name |
| last_name | string | Patient's last name |
| email | string | Patient's email address |
| phone | string | Patient's phone number |
| date_of_birth | string | Patient's birth date |
| medical_history | string | Medical history notes |
| created_at | string | Timestamp of creation |
| updated_at | string | Timestamp of last update |

### patient_risk_reports

Stores risk assessment reports for patients.

| Column | Type | Description |
|--------|------|-------------|
| id | string | Primary key |
| patient_id | string | Foreign key to patients table |
| risk_level | string | Level of risk (e.g., Low, Medium, High) |
| risk_factors | string[] | Array of identified risk factors |
| assessment_details | string | Detailed assessment notes |
| action_items | string | Recommended actions |
| follow_up_date | string | Date for follow-up |
| status | string | Current status (e.g., Open, Closed) |
| created_at | string | Timestamp of creation |
| updated_at | string | Timestamp of last update |

## Type Definitions

TypeScript type definitions for the database tables are located in:
`src/types/database.types.ts`

These definitions should be kept in sync with the actual database schema to ensure type safety throughout the application.

## Build Process

The application is built using Docker with separate configurations for development and production environments.

## API Endpoints

API endpoints are defined using Next.js API routes in the `src/app/api` directory. 