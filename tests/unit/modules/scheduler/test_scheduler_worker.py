import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from ai_companion.modules.scheduler.scheduler_worker import SchedulerWorker


class TestSchedulerWorker:
    """Test suite for the SchedulerWorker class."""

    @pytest.fixture
    def mock_scheduled_message_service(self):
        """Create a mock ScheduledMessageService."""
        mock_service = MagicMock()
        # Configure common mock methods
        mock_service.get_due_messages.return_value = []
        return mock_service

    @pytest.fixture
    def mock_telegram_bot(self):
        """Create a mock Telegram bot."""
        mock_bot = MagicMock()
        # Configure _send_message as an async method
        mock_bot._send_message = AsyncMock()
        return mock_bot

    @pytest.fixture
    def worker(self, mock_scheduled_message_service):
        """Create a SchedulerWorker with mocked dependencies."""
        with patch(
            "ai_companion.modules.scheduler.scheduler_worker.get_scheduled_message_service",
            return_value=mock_scheduled_message_service,
        ):
            worker = SchedulerWorker()
            yield worker
            # Clean up any running tasks
            worker.stop()

    def test_init(self, worker, mock_scheduled_message_service):
        """Test worker initialization."""
        assert worker.scheduled_message_service == mock_scheduled_message_service
        assert worker.check_interval == 30
        assert worker.max_batch_size == 10
        assert worker.running is False
        assert worker.task is None

    @pytest.mark.asyncio
    async def test_start_stop(self, worker):
        """Test starting and stopping the worker."""
        # Patch the _run_scheduler_loop to be a no-op
        with patch.object(worker, "_run_scheduler_loop", return_value=asyncio.Future()):
            # Start the worker
            await worker.start()

            # Verify worker state
            assert worker.running is True
            assert worker.task is not None

            # Stop the worker
            worker.stop()

            # Verify worker state
            assert worker.running is False

    @pytest.mark.asyncio
    async def test_start_with_telegram_bot(self, worker, mock_telegram_bot):
        """Test starting the worker with a Telegram bot."""
        # Patch the _run_scheduler_loop to be a no-op
        with patch.object(worker, "_run_scheduler_loop", return_value=asyncio.Future()):
            # Start the worker with a Telegram bot
            await worker.start(telegram_bot=mock_telegram_bot)

            # Verify worker state
            assert worker.telegram_bot == mock_telegram_bot
            assert worker.running is True
            assert worker.task is not None

    @pytest.mark.asyncio
    async def test_run_scheduler_loop(self, worker, mock_scheduled_message_service):
        """Test the scheduler loop."""
        # Configure mock to return messages on the first call, then no messages
        mock_due_messages = [
            {"id": "message1", "message_content": "Test message 1"},
            {"id": "message2", "message_content": "Test message 2"},
        ]
        mock_scheduled_message_service.get_due_messages.return_value = mock_due_messages

        # Patch asyncio.sleep to avoid waiting
        async def fake_sleep(seconds):
            # After mocking sleep, stop the worker to exit the loop
            worker.running = False

        # Patch process_messages to track calls and patch sleep
        process_messages_mock = AsyncMock()

        with patch("asyncio.sleep", side_effect=fake_sleep):
            with patch.object(worker, "_process_messages", process_messages_mock):
                # Make the worker running and manually call the loop
                worker.running = True

                # Run the loop directly
                await worker._run_scheduler_loop()

                # Verify get_due_messages was called
                mock_scheduled_message_service.get_due_messages.assert_called_once_with(
                    limit=worker.max_batch_size
                )

                # Verify process_messages was called with the mock messages
                process_messages_mock.assert_called_once_with(mock_due_messages)

    @pytest.mark.asyncio
    async def test_process_messages_success(
        self, worker, mock_telegram_bot, mock_scheduled_message_service
    ):
        """Test processing messages successfully."""
        # Set the telegram bot
        worker.telegram_bot = mock_telegram_bot

        # Mock message data
        message = {
            "id": "message1",
            "message_content": "Test message",
            "metadata": {"platform_data": {"chat_id": 123456789}},
            "attempts": 0,
        }

        # Configure calculate_next_execution_time to return None (non-recurring)
        mock_scheduled_message_service.calculate_next_execution_time.return_value = None

        # Call process_messages
        await worker._process_messages([message])

        # Verify the message was sent
        mock_telegram_bot._send_message.assert_called_with(
            message["metadata"]["platform_data"]["chat_id"], message["message_content"]
        )

        # Verify message status was updated
        mock_scheduled_message_service.update_message_status.assert_called_with(
            message_id=message["id"], status="sent"
        )

    @pytest.mark.asyncio
    async def test_process_messages_recurring(
        self, worker, mock_telegram_bot, mock_scheduled_message_service
    ):
        """Test processing a recurring message."""
        # Set the telegram bot
        worker.telegram_bot = mock_telegram_bot

        # Mock message data
        message = {
            "id": "message1",
            "message_content": "Test recurring message",
            "metadata": {
                "platform_data": {"chat_id": 123456789},
                "recurrence": {"type": "daily", "interval": 1},
            },
            "attempts": 0,
        }

        # Configure calculate_next_execution_time to return a future time
        next_time = datetime.utcnow() + timedelta(days=1)
        mock_scheduled_message_service.calculate_next_execution_time.return_value = (
            next_time
        )

        # Call process_messages
        await worker._process_messages([message])

        # Verify the message was sent
        mock_telegram_bot._send_message.assert_called_with(
            message["metadata"]["platform_data"]["chat_id"], message["message_content"]
        )

        # Verify message status was updated to "rescheduled"
        mock_scheduled_message_service.update_message_status.assert_called_with(
            message_id=message["id"],
            status="rescheduled",
            next_scheduled_time=next_time,
        )

    @pytest.mark.asyncio
    async def test_process_messages_error(
        self, worker, mock_telegram_bot, mock_scheduled_message_service
    ):
        """Test processing a message that fails to send."""
        # Set the telegram bot
        worker.telegram_bot = mock_telegram_bot

        # Configure _send_message to raise an exception
        mock_telegram_bot._send_message.side_effect = Exception(
            "Failed to send message"
        )

        # Mock message data
        message = {
            "id": "message1",
            "message_content": "Test message",
            "metadata": {"platform_data": {"chat_id": 123456789}},
            "attempts": 0,
        }

        # Call process_messages
        await worker._process_messages([message])

        # Verify message status was updated to "pending" for retry
        mock_scheduled_message_service.update_message_status.assert_called_once()
        call_args = mock_scheduled_message_service.update_message_status.call_args[1]
        assert call_args["message_id"] == message["id"]
        assert call_args["status"] == "pending"
        assert "next_scheduled_time" in call_args
        assert "error_message" in call_args

    @pytest.mark.asyncio
    async def test_process_messages_max_retries(
        self, worker, mock_telegram_bot, mock_scheduled_message_service
    ):
        """Test processing a message that reaches max retries."""
        # Set the telegram bot
        worker.telegram_bot = mock_telegram_bot

        # Configure _send_message to raise an exception
        mock_telegram_bot._send_message.side_effect = Exception(
            "Failed to send message"
        )

        # Mock message data with max attempts reached
        message = {
            "id": "message1",
            "message_content": "Test message",
            "metadata": {"platform_data": {"chat_id": 123456789}, "max_attempts": 3},
            "attempts": 3,  # Already at max attempts
        }

        # Call process_messages
        await worker._process_messages([message])

        # Verify message status was updated to "failed"
        mock_scheduled_message_service.update_message_status.assert_called_with(
            message_id=message["id"],
            status="failed",
            error_message="Max retries reached: Failed to send message",
        )

    @pytest.mark.asyncio
    async def test_process_messages_no_telegram_bot(
        self, worker, mock_scheduled_message_service
    ):
        """Test processing messages with no Telegram bot set."""
        # Ensure no telegram bot is set
        worker.telegram_bot = None

        # Mock message data
        message = {
            "id": "message1",
            "message_content": "Test message",
            "metadata": {"platform_data": {"chat_id": 123456789}},
        }

        # Call process_messages
        await worker._process_messages([message])

        # Verify no calls to update_message_status
        mock_scheduled_message_service.update_message_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_messages_no_chat_id(
        self, worker, mock_telegram_bot, mock_scheduled_message_service
    ):
        """Test processing a message with no chat_id."""
        # Set the telegram bot
        worker.telegram_bot = mock_telegram_bot

        # Mock message data with no chat_id
        message = {
            "id": "message1",
            "message_content": "Test message",
            "metadata": {
                "platform_data": {}  # Missing chat_id
            },
        }

        # Call process_messages
        await worker._process_messages([message])

        # Verify message status was updated to "failed"
        mock_scheduled_message_service.update_message_status.assert_called_with(
            message_id=message["id"],
            status="failed",
            error_message="Missing chat_id in metadata",
        )

        # Verify no calls to _send_message
        mock_telegram_bot._send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_messages_no_content(
        self, worker, mock_telegram_bot, mock_scheduled_message_service
    ):
        """Test processing a message with no content."""
        # Set the telegram bot
        worker.telegram_bot = mock_telegram_bot

        # Mock message data with no content
        message = {
            "id": "message1",
            "metadata": {"platform_data": {"chat_id": 123456789}},
        }

        # Call process_messages
        await worker._process_messages([message])

        # Verify message status was updated to "failed"
        mock_scheduled_message_service.update_message_status.assert_called_with(
            message_id=message["id"],
            status="failed",
            error_message="Missing message content",
        )

        # Verify no calls to _send_message
        mock_telegram_bot._send_message.assert_not_called()
