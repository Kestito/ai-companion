# Telegram Bot Testing Strategy

This document outlines the testing strategy for the Telegram bot interface component of the AI Companion system.

## Test Files

The Telegram interface has several test files for different aspects of functionality:

1. **test_full_user_flow.py** - Tests a complete user journey from first message to scheduling
2. **test_patient_creation.py** - Tests the patient creation process for new Telegram users
3. **test_schedule_message.py** - Tests the message scheduling functionality
4. **test_scheduler.py** - Tests the scheduled message processor that runs as a separate service
5. **test_telegram_responses.py** - Tests the response handling for different types of messages

## Testing Levels

### Unit Tests

Unit tests verify the functionality of individual components of the Telegram bot:

- Message extraction and parsing
- Response formatting and sending
- Command handling (like the /schedule command)
- Long message chunking
- Error handling

### Integration Tests

Integration tests verify the interaction between multiple components:

- Bot interaction with the graph processing system
- Database integration for saving conversations and patient data
- Scheduled message integration with the scheduler component

### End-to-End Tests

End-to-end tests simulate complete user journeys:

- New user registration flow
- Existing user conversation flow
- Scheduling functionality

## Testing Approach

### Mocked Dependencies

For unit and integration tests, the following dependencies are mocked:

- Telegram API (using AsyncMock for network requests)
- Graph processing components
- Database connections

### Test Data

Test data is generated to simulate real Telegram messages, including:

- Text messages
- Command messages
- Media messages (voice, images)
- Edge cases (empty messages, very long messages)

### Test Coverage

Tests should cover the following aspects:

- Happy path scenarios (normal operation)
- Error handling (network errors, invalid input)
- Edge cases (message size limits, rate limiting)
- Graceful degradation (partial system failures)

## Running Tests

### Local Development

Tests can be run locally using the Python unittest framework:

```bash
# Run a specific test file
python -m src.ai_companion.interfaces.telegram.test_telegram_responses

# Run all tests in the telegram package
python -m unittest discover -s src.ai_companion.interfaces.telegram
```

### CI/CD Pipeline

Tests are automatically run as part of the CI/CD pipeline to ensure quality and prevent regressions. The pipeline includes:

1. Code linting and style checks
2. Unit tests
3. Integration tests
4. End-to-end tests (with mocked external dependencies)

## Future Improvements

Planned improvements to the testing strategy include:

- Adding property-based testing for edge cases
- Implementing load and performance testing for high-volume scenarios
- Creating a mocked Telegram API server for more realistic testing
- Adding observability metrics to track test coverage and quality

## Test Data Management

Test data, including sample messages and expected responses, is stored in a structured format to ensure consistency and reproducibility across test runs.

## Test Metrics

The following metrics are tracked for test quality:

- Code coverage percentage (aim for 80%+)
- Test pass rate
- Test execution time
- Number of mocked vs. real components 