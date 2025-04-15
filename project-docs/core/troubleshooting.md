# AI Companion Troubleshooting Guide

This document provides solutions for common issues encountered when running the AI Companion application.

## Common Issues

### 1. Database Connectivity Issues - "Error loading patients - TypeError: Failed to fetch"

**Symptoms:**
- Error message "Error loading patients - TypeError: Failed to fetch" appears in the UI
- Console logs show errors related to Supabase connections
- Patient data or other database-dependent features fail to load

**Causes:**
- Supabase credentials not properly configured
- Environment variables not being loaded correctly
- Network connectivity issues to Supabase
- Schema access method incompatibility

**Solutions:**
1. Ensure hardcoded credentials are used in all Supabase client files:
   ```typescript
   // Hardcoded Supabase credentials
   const SUPABASE_URL = 'https://aubulhjfeszmsheonmpy.supabase.co';
   const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUyODc0MTIsImV4cCI6MjA1MDg2MzQxMn0.ovHMLKm5nN4o7_P_Pld1vEzPpL1uKZK1xxtWn3RMMJw';
   ```

2. Check that the `patientService.ts` file is using the direct client creation approach:
   ```typescript
   async function getClient() {
     // Always use hardcoded credentials
     return createClient<Database>(SUPABASE_URL, SUPABASE_ANON_KEY);
   }
   ```

3. Verify that the tables exist in Supabase by running this SQL query in the Supabase SQL Editor:
   ```sql
   SELECT * FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name = 'patients';
   ```

4. If the table doesn't exist, create it using the schema definition in `database-schema.md`

5. Check network connectivity to Supabase by running:
   ```bash
   curl -I https://aubulhjfeszmsheonmpy.supabase.co
   ```

6. Review the console logs for specific error messages that might indicate the root cause

### 2. 404 Not Found for `/chat/` Endpoint

**Symptoms:**
- Accessing `http://localhost:8000/chat/` returns a 404 Not Found error
- Error logs show `"GET /chat/ HTTP/1.1" 404 Not Found`

**Causes:**
- The Chainlit service is not running on port 8080
- The main application is running but cannot connect to the Chainlit service

**Solutions:**
1. Check if the Chainlit service is running:
   ```bash
   curl http://localhost:8000/chat/status
   ```

2. If the status shows "unavailable", ensure the application was started with the `INTERFACE=all` environment variable:
   ```bash
   docker run -p 8000:8000 -e INTERFACE=all ai-companion:latest
   ```

3. Check the application logs for any errors related to starting Chainlit:
   ```bash
   docker logs <container_id>
   ```

4. If running locally, start the Chainlit service manually:
   ```bash
   cd src
   python -m ai_companion.interfaces.chainlit.app --host 0.0.0.0 --port 8080
   ```

### 3. Monitoring Endpoints Return 404 Not Found

**Symptoms:**
- Accessing `/health/metrics`, `/health/report`, or `/health/reset` returns a 404 Not Found error
- Error logs show `"GET /health/metrics HTTP/1.1" 404 Not Found`

**Causes:**
- The monitoring service is not running on port 8090
- The main application is running but cannot connect to the monitoring service

**Solutions:**
1. Check if the monitoring service is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. If the monitoring status shows "unavailable", ensure the application was started with the `INTERFACE=all` environment variable:
   ```bash
   docker run -p 8000:8000 -e INTERFACE=all ai-companion:latest
   ```

3. Check the application logs for any errors related to starting the monitoring service:
   ```bash
   docker logs <container_id>
   ```

4. If running locally, start the monitoring service manually:
   ```bash
   cd src
   python -m ai_companion.interfaces.monitor.app
   ```

### 4. "Invalid Input Syntax for Type UUID" Error When Checking Patients

**Symptoms:**
- Error logs show `ERROR:ai_companion.graph.nodes:Error checking for existing patient: {'code': '22P02', 'details': None, 'hint': None, 'message': 'invalid input syntax for type uuid: "NUMERIC_ID"'}`
- Patient registration or lookup fails for Telegram or WhatsApp users

**Causes:**
- The code is attempting to use a numeric Telegram/WhatsApp user ID directly as a UUID in the patient table
- Supabase's `patients` table uses the UUID format for the primary key, which is incompatible with numeric IDs

**Solutions:**
1. Never query the `id` field directly with a messaging platform ID:
   ```python
   # INCORRECT - will cause UUID error
   result = supabase.table("patients").select("id").eq("id", str(user_id)).execute()
   ```

2. Always use the LIKE query pattern to search in the email field's JSON metadata:
   ```python
   # CORRECT - search in the JSON metadata stored in email field
   metadata_search = f'%"user_id": "{user_id}"%'
   result = supabase.table("patients").select("id").like("email", metadata_search).execute()
   ```

3. For user registration, store the platform user ID in the metadata JSON, not as the primary ID:
   ```python
   platform_metadata = {
       "platform": platform,
       "user_id": user_id,
       "username": user_name
   }
   patient_data["email"] = json.dumps(platform_metadata)
   ```

4. If you've encountered this error, check the code in the `router_node` and `patient_registration_node` functions.

### 4. Connection Refused Errors

**Symptoms:**
- Error logs show "Connection refused" when trying to connect to services
- Health checks show services as "unavailable"

**Causes:**
- Services are not running on the expected ports
- Firewall or network issues preventing connections

**Solutions:**
1. Check if the services are running and listening on the expected ports:
   ```bash
   # On Linux/macOS
   netstat -tuln | grep 8080  # Check Chainlit
   netstat -tuln | grep 8090  # Check Monitoring
   
   # On Windows
   netstat -an | findstr 8080  # Check Chainlit
   netstat -an | findstr 8090  # Check Monitoring
   ```

2. Ensure no firewall rules are blocking the connections

3. If running in Docker, ensure the ports are properly exposed:
   ```bash
   docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 -e INTERFACE=all ai-companion:latest
   ```

### 4. Services Start But Are Not Accessible

**Symptoms:**
- Logs show that services started successfully
- But accessing the endpoints still returns errors

**Causes:**
- Services are binding to localhost/127.0.0.1 instead of 0.0.0.0
- Port conflicts with other applications

**Solutions:**
1. Ensure services are binding to all interfaces (0.0.0.0):
   ```bash
   # For Chainlit
   python -m ai_companion.interfaces.chainlit.app --host 0.0.0.0 --port 8080
   
   # For Monitoring
   python -m ai_companion.interfaces.monitor.app --host 0.0.0.0 --port 8090
   ```

2. Check for port conflicts and use different ports if needed:
   ```bash
   # On Linux/macOS
   lsof -i :8080
   lsof -i :8090
   
   # On Windows
   netstat -ano | findstr 8080
   netstat -ano | findstr 8090
   ```

## Checking Service Status

You can check the status of all services using the health endpoint:

```bash
curl http://localhost:8000/health
```

This will return information about all services, including their status and availability.

For specific services:

- Chainlit: `curl http://localhost:8000/chat/status`
- Monitoring: `curl http://localhost:8000/health`

## Restarting Services

If you need to restart services:

1. If running in Docker, restart the container:
   ```bash
   docker restart <container_id>
   ```

2. If running locally, stop the current processes and start them again:
   ```bash
   # Start main application
   python -m ai_companion.main
   
   # Start Chainlit
   python -m ai_companion.interfaces.chainlit.app --host 0.0.0.0 --port 8080
   
   # Start Monitoring
   python -m ai_companion.interfaces.monitor.app --host 0.0.0.0 --port 8090
   ```

## Getting Help

If you continue to experience issues after trying these solutions, please:

1. Check the application logs for detailed error messages
2. Review the project documentation for any configuration requirements
3. Open an issue in the project repository with detailed information about the problem

## Chainlit Interface Not Working

### Symptoms
- The `/chat/` endpoint returns a 307 Temporary Redirect to `/chat/error`
- The error page shows "The Chainlit service is currently unavailable"
- Logs show: `Error checking service at localhost:8080: All connection attempts failed`

### Cause
The issue is related to the file path in the Docker container. The Chainlit service is trying to run the file at `ai_companion/interfaces/chainlit/app.py`, but in the container, the file structure is different. The file should be at `/app/src/ai_companion/interfaces/chainlit/app.py` instead.

### Solution
There are two ways to fix this issue:

#### Option 1: Update the Dockerfile
Modify the Dockerfile to use the correct path for the Chainlit app:

```dockerfile
# Change this line in the Dockerfile
/app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \
```

to:

```dockerfile
/app/.venv/bin/chainlit run src/ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \
```

#### Option 2: Create a Symbolic Link
Add a command to the Dockerfile to create a symbolic link:

```dockerfile
# Add this before the startup script
RUN ln -sf /app/src/ai_companion /app/ai_companion
```

### Implementation Steps
1. Update the Dockerfile with one of the solutions above
2. Rebuild the Docker image
3. Push the new image to the Azure Container Registry
4. Update the Azure Container App to use the new image

### 7. TypeError in Patients View

**Symptoms:**
- Client-side exception when viewing the patients page
- Error in console: "TypeError: Cannot read properties of undefined (reading 'charAt')"
- Patients list or patient details page fails to load

**Causes:**
- Missing null checks when accessing patient properties
- Attempting to access properties of potentially undefined patient objects
- Data inconsistency between the expected Patient type and actual data from the database

**Solutions:**
1. Add null checks for all patient properties before accessing them:
   ```tsx
   // Instead of this (which can cause errors)
   {patient.id.substring(0, 8)}...
   
   // Use this (with null check)
   {patient.id && patient.id.substring(0, 8)}...
   ```

2. Add additional validation when loading patient data:
   ```tsx
   if (data && data.name) {
     // Only set the patient if it has the required properties
     setPatient(data);
   }
   ```

3. Use optional chaining for nested properties:
   ```tsx
   {patient?.name ? patient.name.charAt(0) : 'P'}
   ```

4. Provide fallback values for all displayed properties:
   ```tsx
   {patient?.email || 'No email available'}
   ```

5. If the issue persists, check the database schema and ensure it matches the expected Patient type in the application.
