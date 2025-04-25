import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from ai_companion.modules.scheduler.scheduled_message_service import (
    ScheduledMessageService,
)


class TestScheduledMessageService:
    """Test suite for the ScheduledMessageService class."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"id": "test-id"}])

        mock_select = MagicMock()
        mock_select.select.return_value = mock_execute

        mock_table = MagicMock()
        mock_table.table.return_value = mock_select

        return mock_table

    @pytest.fixture
    def service(self, mock_supabase):
        """Create a ScheduledMessageService with a mock Supabase client."""
        with patch(
            "ai_companion.modules.scheduler.scheduled_message_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = ScheduledMessageService()
            return service

    def test_init(self, service, mock_supabase):
        """Test service initialization."""
        assert service.supabase == mock_supabase
        assert service.table_name == "scheduled_messages"

    def test_create_scheduled_message(self, service, mock_supabase):
        """Test creating a scheduled message."""
        # Setup
        chat_id = 123456789
        message_content = "Test message"
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        platform = "telegram"

        # Mock uuid.uuid4 to return a predictable value
        with patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
        ):
            # Execute
            message_id = service.create_scheduled_message(
                chat_id=chat_id,
                message_content=message_content,
                scheduled_time=scheduled_time,
                platform=platform,
            )

            # Verify
            assert message_id == "12345678-1234-5678-1234-567812345678"

            # Verify the correct data was passed to Supabase
            mock_insert = mock_supabase.table.return_value.insert
            mock_insert.assert_called_once()

            # Extract the call arguments
            args, _ = mock_insert.call_args
            data = args[0]

            # Verify the message data
            assert data["id"] == "12345678-1234-5678-1234-567812345678"
            assert data["message_content"] == message_content
            assert data["scheduled_time"] == scheduled_time.isoformat()
            assert data["platform"] == platform
            assert data["status"] == "pending"
            assert data["attempts"] == 0
            assert data["metadata"]["platform_data"]["chat_id"] == chat_id

    def test_get_message_by_id(self, service, mock_supabase):
        """Test retrieving a message by ID."""
        # Setup
        message_id = "test-id"
        mock_data = {"id": message_id, "message_content": "Test message"}

        # Configure the mock to return specific data
        mock_eq = MagicMock()
        mock_eq.eq.return_value = MagicMock(
            execute=MagicMock(return_value=MagicMock(data=[mock_data]))
        )

        mock_select = MagicMock()
        mock_select.select.return_value = mock_eq

        mock_supabase.table.return_value = mock_select

        # Execute
        result = service.get_message_by_id(message_id)

        # Verify
        assert result == mock_data
        mock_supabase.table.assert_called_with("scheduled_messages")
        mock_select.select.assert_called_with("*")
        mock_eq.eq.assert_called_with("id", message_id)

    def test_get_due_messages(self, service, mock_supabase):
        """Test retrieving due messages."""
        # Setup
        limit = 10
        mock_data = [
            {"id": "message1", "message_content": "Test message 1"},
            {"id": "message2", "message_content": "Test message 2"},
        ]

        # Configure the mock to directly return data
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=mock_data)

        mock_limit = MagicMock()
        mock_limit.limit.return_value = mock_execute

        mock_order2 = MagicMock()
        mock_order2.order.return_value = mock_limit

        mock_order1 = MagicMock()
        mock_order1.order.return_value = mock_order2

        mock_lte = MagicMock()
        mock_lte.lte.return_value = mock_order1

        mock_eq = MagicMock()
        mock_eq.eq.return_value = mock_lte

        mock_select = MagicMock()
        mock_select.select.return_value = mock_eq

        mock_supabase.table.return_value = mock_select

        # Execute
        result = service.get_due_messages(limit)

        # Verify
        assert result == mock_data
        mock_supabase.table.assert_called_with("scheduled_messages")
        mock_select.select.assert_called_with("*")
        mock_eq.eq.assert_called_with("status", "pending")

    def test_update_message_status(self, service, mock_supabase):
        """Test updating a message status."""
        # Setup
        message_id = "test-id"
        status = "sent"

        # Mock for get_message_by_id
        service.get_message_by_id = MagicMock(
            return_value={"id": message_id, "attempts": 0}
        )

        # Configure the mock chain for update
        mock_eq = MagicMock()
        mock_eq.eq.return_value = MagicMock(
            execute=MagicMock(return_value=MagicMock(data=[{"id": message_id}]))
        )

        mock_update = MagicMock()
        mock_update.update.return_value = mock_eq

        mock_supabase.table.return_value = mock_update

        # Execute
        result = service.update_message_status(message_id, status)

        # Verify
        assert result is True
        mock_supabase.table.assert_called_with("scheduled_messages")
        mock_update.update.assert_called_once()

        # Extract the call arguments
        args, _ = mock_update.update.call_args
        update_data = args[0]

        # Verify the update data
        assert update_data["status"] == status

        mock_eq.eq.assert_called_with("id", message_id)

    def test_calculate_next_execution_time_daily(self, service):
        """Test calculating next execution time for daily recurrence."""
        # Setup
        message_id = "test-id"
        base_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)

        # Mock the message
        message = {
            "id": message_id,
            "scheduled_time": base_time.isoformat(),
            "metadata": {"recurrence": {"type": "daily", "interval": 1}},
        }

        service.get_message_by_id = MagicMock(return_value=message)

        # Execute
        next_time = service.calculate_next_execution_time(message_id)

        # Verify
        assert next_time is not None
        assert (next_time - base_time).days == 1  # Should be one day later
        assert next_time.hour == base_time.hour
        assert next_time.minute == base_time.minute

    def test_calculate_next_execution_time_weekly(self, service):
        """Test calculating next execution time for weekly recurrence."""
        # Setup
        message_id = "test-id"
        base_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)

        # Get the current weekday (0-6)
        current_weekday = base_time.weekday()

        # Choose the next day after the current weekday
        next_weekday = (
            current_weekday + 2
        ) % 7  # Skip one day to ensure it's not today

        # Mock the message
        message = {
            "id": message_id,
            "scheduled_time": base_time.isoformat(),
            "metadata": {
                "recurrence": {"type": "weekly", "interval": 1, "days": [next_weekday]}
            },
        }

        service.get_message_by_id = MagicMock(return_value=message)

        # Execute
        next_time = service.calculate_next_execution_time(message_id)

        # Verify
        assert next_time is not None

        # Calculate expected days difference
        days_diff = next_weekday - current_weekday
        if days_diff <= 0:
            days_diff += 7

        assert (next_time - base_time).days == days_diff
        assert next_time.hour == base_time.hour
        assert next_time.minute == base_time.minute
