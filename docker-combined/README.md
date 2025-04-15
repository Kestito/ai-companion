# Combined AI Companion Docker Container

This setup runs both the main AI Companion application and the Telegram scheduler in a single Docker container.

## Files

- `Dockerfile`: Creates a combined container with both processes
- `entrypoint.sh`: Script that starts both the main app and the scheduler
- `build.sh`: Linux/Mac script to build and run the container
- `build.ps1`: Windows PowerShell script to build and run the container

## Usage

### On Linux/Mac:

```bash
chmod +x build.sh
./build.sh
```

### On Windows:

```powershell
.\build.ps1
```

## Logs

- Main application: View with `docker logs ai-companion-combined`
- Telegram scheduler: Available in the container at `/app/logs/telegram_scheduler.log`
  - Access via: `docker exec -it ai-companion-combined cat /app/logs/telegram_scheduler.log`

## Management

- Stop container: `docker stop ai-companion-combined`
- Start container: `docker start ai-companion-combined`
- Remove container: `docker rm -f ai-companion-combined`