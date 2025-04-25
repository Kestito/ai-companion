import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from ai_companion.modules.scheduler.scheduled_message_service import (
    ScheduledMessageService,
)
from ai_companion.modules.scheduler.scheduler_worker import SchedulerWorker


class TestSchedulerIntegration:
    """Integration tests for the scheduler module components."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client with realistic behavior."""
        # Mock data for scheduled messages
        self.scheduled_messages = [
            {
                "id": "message1",
                "message_content": "Test message 1",
                "scheduled_time": (
                    datetime.utcnow() - timedelta(minutes=5)
                ).isoformat(),
                "platform": "telegram",
                "status": "pending",
                "priority": 1,
                "attempts": 0,
                "metadata": {"platform_data": {"chat_id": 123456789}},
            },
            {
                "id": "message2",
                "message_content": "Test message 2",
                "scheduled_time": (
                    datetime.utcnow() - timedelta(minutes=10)
                ).isoformat(),
                "platform": "telegram",
                "status": "pending",
                "priority": 2,
                "attempts": 0,
                "metadata": {"platform_data": {"chat_id": 123456789}},
            },
        ]

        # Create mock supabase with realistic behavior
        mock_supabase = MagicMock()

        # Configure table method
        def mock_table(table_name):
            if table_name == "scheduled_messages":
                # Return a mock object with select/insert/update methods
                table_mock = MagicMock()

                # Configure the select method
                def mock_select(columns="*"):
                    select_mock = MagicMock()

                    # Add eq method for filtering
                    def mock_eq(field, value):
                        eq_mock = MagicMock()

                        # For get_message_by_id
                        if field == "id":
                            found_message = next(
                                (
                                    msg
                                    for msg in self.scheduled_messages
                                    if msg["id"] == value
                                ),
                                None,
                            )

                            # Configure the execute method
                            eq_mock.execute.return_value = MagicMock(
                                data=[found_message] if found_message else []
                            )

                        # For get_due_messages (status filter)
                        elif field == "status" and value == "pending":
                            lte_mock = MagicMock()

                            # Add lte method for time filtering
                            def mock_lte(field, value):
                                # Assuming value is current time
                                order_mock = MagicMock()

                                # Add order method for sorting
                                def mock_order(field):
                                    order2_mock = MagicMock()

                                    # Second order call
                                    def mock_order2(field):
                                        limit_mock = MagicMock()

                                        # Add limit method
                                        def mock_limit(limit):
                                            due_messages = [
                                                msg
                                                for msg in self.scheduled_messages
                                                if msg["status"] == "pending"
                                                and msg["scheduled_time"] <= value
                                            ]

                                            # Sort by priority and time
                                            due_messages.sort(
                                                key=lambda m: (
                                                    m["priority"],
                                                    m["scheduled_time"],
                                                )
                                            )

                                            # Apply limit
                                            due_messages = due_messages[:limit]

                                            execute_mock = MagicMock()
                                            execute_mock.execute.return_value = (
                                                MagicMock(data=due_messages)
                                            )
                                            return execute_mock

                                        limit_mock.limit = mock_limit
                                        return limit_mock

                                    order2_mock.order = mock_order2
                                    return order2_mock

                                order_mock.order = mock_order
                                return order_mock

                            lte_mock.lte = mock_lte
                            return lte_mock

                        return eq_mock

                    select_mock.eq = mock_eq
                    return select_mock

                table_mock.select = mock_select

                # Configure the insert method
                def mock_insert(data):
                    # Add the data to our mock database
                    self.scheduled_messages.append(data)

                    # Return a mock that can be executed
                    insert_mock = MagicMock()
                    insert_mock.execute.return_value = MagicMock(data=[data])
                    return insert_mock

                table_mock.insert = mock_insert

                # Configure the update method
                def mock_update(data):
                    update_mock = MagicMock()

                    # Add eq method for finding the record to update
                    def mock_eq(field, value):
                        # Find the message
                        for i, msg in enumerate(self.scheduled_messages):
                            if msg["id"] == value:
                                # Update the message
                                self.scheduled_messages[i].update(data)

                                # Return a mock that can be executed
                                eq_mock = MagicMock()
                                eq_mock.execute.return_value = MagicMock(
                                    data=[self.scheduled_messages[i]]
                                )
                                return eq_mock

                        # Message not found
                        eq_mock = MagicMock()
                        eq_mock.execute.return_value = MagicMock(data=[])
                        return eq_mock

                    update_mock.eq = mock_eq
                    return update_mock

                table_mock.update = mock_update

                return table_mock

            # Return a default mock for other tables
            return MagicMock()

        mock_supabase.table = mock_table
        return mock_supabase

    @pytest.fixture
    def service(self, mock_supabase):
        """Create a ScheduledMessageService with a mock Supabase client."""
        with patch(
            "ai_companion.modules.scheduler.scheduled_message_service.get_supabase_client",
            return_value=mock_supabase,
        ):
            service = ScheduledMessageService()
            return service

    @pytest.fixture
    def mock_telegram_bot(self):
        """Create a mock Telegram bot."""
        mock_bot = MagicMock()
        # Configure _send_message as an async method
        mock_bot._send_message = AsyncMock()
        return mock_bot

    @pytest.fixture
    def worker(self, service, mock_telegram_bot):
        """Create a SchedulerWorker with the service."""
        with patch(
            "ai_companion.modules.scheduler.scheduler_worker.get_scheduled_message_service",
            return_value=service,
        ):
            worker = SchedulerWorker(telegram_bot=mock_telegram_bot)
            yield worker
            # Clean up
            worker.stop()

    @pytest.mark.asyncio
    async def test_end_to_end_message_processing(
        self, worker, service, mock_telegram_bot, mock_supabase
    ):
        """Test the entire flow from checking for due messages to sending and updating."""

        # Configure fake sleep to prevent actual waiting
        async def fake_sleep(seconds):
            pass

        # Patch asyncio.sleep
        with patch("asyncio.sleep", fake_sleep):
            # Manually initiate the scheduler cycle
            worker.running = True

            # Get initial pending count
            initial_pending_count = sum(
                1 for msg in self.scheduled_messages if msg["status"] == "pending"
            )

            # Process a batch manually
            messages = service.get_due_messages(limit=10)
            assert len(messages) > 0, "Expected to find due messages"

            # Process the messages
            await worker._process_messages(messages)

            # Verify the messages were processed
            remaining_pending = sum(
                1 for msg in self.scheduled_messages if msg["status"] == "pending"
            )
            sent_count = sum(
                1 for msg in self.scheduled_messages if msg["status"] == "sent"
            )

            # There should be fewer pending messages
            assert (
                remaining_pending < initial_pending_count
            ), "Expected fewer pending messages"

            # There should be some sent messages
            assert sent_count > 0, "Expected some messages to be marked as sent"

            # Verify Telegram bot was called for each message
            assert mock_telegram_bot._send_message.call_count == len(
                messages
            ), "Expected one call per message"

    @pytest.mark.asyncio
    async def test_create_and_process_message(self, worker, service, mock_telegram_bot):
        """Test creating a message and then processing it."""
        # Create a message due now
        scheduled_time = datetime.utcnow() - timedelta(minutes=1)
        message_id = service.create_scheduled_message(
            chat_id=123456789,
            message_content="Integration test message",
            scheduled_time=scheduled_time,
            platform="telegram",
        )

        # Verify the message was created
        message = service.get_message_by_id(message_id)
        assert message is not None, "Message should be created and retrievable"
        assert message["status"] == "pending", "Message should be in pending status"

        # Get due messages
        due_messages = service.get_due_messages(limit=10)
        assert len(due_messages) > 0, "Should have at least one due message"

        # Make sure our message is in the due messages
        test_message = None
        for msg in due_messages:
            if msg["id"] == message_id:
                test_message = msg
                break

        # If we found our message, process just that one to avoid other messages affecting the test
        if test_message:
            await worker._process_messages([test_message])

            # Verify the message was sent and status updated
            updated_message = service.get_message_by_id(message_id)
            assert (
                updated_message["status"] == "sent"
            ), "Message status should be 'sent'"

            # Verify Telegram bot was called with this specific message
            mock_telegram_bot._send_message.assert_called_with(
                123456789, "Integration test message"
            )
        else:
            # Process all messages
            await worker._process_messages(due_messages)

            # Verify the message was sent and status updated
            updated_message = service.get_message_by_id(message_id)
            assert (
                updated_message["status"] == "sent"
            ), "Message status should be 'sent'"

            # Here we can't verify the exact call parameters due to other messages
            # so we just check that the bot was called
            assert (
                mock_telegram_bot._send_message.call_count > 0
            ), "Telegram bot send method should be called"

    @pytest.mark.asyncio
    async def test_recurring_message(self, worker, service, mock_telegram_bot):
        """Test creating and processing a recurring message."""
        # Create a daily recurring message due now
        scheduled_time = datetime.utcnow() - timedelta(minutes=1)
        metadata = {"recurrence": {"type": "daily", "interval": 1}}

        message_id = service.create_scheduled_message(
            chat_id=123456789,
            message_content="Daily recurring test message",
            scheduled_time=scheduled_time,
            platform="telegram",
            metadata=metadata,
        )

        # Get due messages
        due_messages = service.get_due_messages(limit=10)
        assert any(
            msg["id"] == message_id for msg in due_messages
        ), "New message should be in due messages"

        # Process the messages
        await worker._process_messages(due_messages)

        # Verify the message was sent and status updated to rescheduled
        updated_message = service.get_message_by_id(message_id)
        assert (
            updated_message["status"] == "rescheduled"
        ), "Message status should be 'rescheduled'"

        # New scheduled time should be roughly 1 day in the future
        new_time = datetime.fromisoformat(
            updated_message["scheduled_time"].replace("Z", "+00:00")
        )
        time_diff = new_time - scheduled_time
        assert (
            0.9 <= time_diff.days <= 1.1
        ), "Next execution should be about 1 day later"
