# Changes Log

## 2023-11-02: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-01: Removed get_cached_messages Method from ShortTermMemoryManager

### Summary
Removed the `get_cached_messages` method from ShortTermMemoryManager and updated MemoryService to use `get_messages_parallel` directly.

### Changes
- Removed `get_cached_messages` method from ShortTermMemoryManager class
- Updated MemoryService to call `get_messages_parallel` directly instead of `get_cached_messages`
- Improved code organization by eliminating redundant compatibility methods
- Fixed formatting issues in the memory service code

### Benefits
- Simplified memory manager API by eliminating redundant methods
- Improved code clarity by using the primary retrieval method directly
- Reduced potential for bugs from method name inconsistency
- Streamlined memory retrieval code path 

## 2023-10-31: Fixed Import Paths and Memory Service Compatibility

### Summary
Fixed critical errors in the graph system and memory service functionality.

### Changes
- Updated import path in `graph.py` from 'ai_companion.graph.nodes' to 'ai_companion.graph.utils.nodes'
- Updated import path in `telegram_bot.py` to use the correct path for `get_patient_id_from_platform_id`
- Added missing `get_cached_messages` method to ShortTermMemoryManager for compatibility with memory service

### Benefits
- Fixed ModuleNotFoundError when running the Telegram bot
- Fixed 'ShortTermMemoryManager has no attribute get_cached_messages' error
- Ensured compatibility between memory service and memory manager implementations
- Improved system resilience with better error handling

## 2023-10-30: Improved Database Field Handling in Patient Identification

### Summary
Enhanced the patient identification system with robust error handling for database field differences.

### Changes
- Added dynamic database schema detection in `get_patient_id_from_platform_id`
- Implemented graceful handling for scenarios where the `system_id` column doesn't exist yet
- Added multiple fallback strategies when primary lookup methods fail
- Wrapped all database operations in try-except blocks for better error isolation

### Benefits
- More resilient patient identification that works regardless of database schema version
- Clearer error logging for troubleshooting database issues
- Ability to gracefully handle database schema migrations and changes
- Forward and backward compatibility with different database configurations

## 2023-10-29: Implemented System ID for Cross-Platform Patient Identification

### Summary
Enhanced the patient identification system by implementing a standardized `system_id` field for better cross-platform identification.

### Changes
- Modified `get_patient_id_from_platform_id` to use a consistent system_id format (`platform:platform_id`)
- Added logic to first search for patients by `system_id` for more efficient lookups
- Updated existing patient records with `system_id` when found by other methods
- Ensured all new patient records are created with `system_id` populated

### Benefits
- More reliable and consistent patient identification across platforms
- Better performance when identifying returning users
- Simplified migration path for users who switch between platforms
- Enhanced data integrity with standardized identification format

## 2023-10-28: Fixed Patient ID Field Name in Database Queries

### Summary
Updated the `get_patient_id_from_platform_id` function to use the correct column name in the patients table.

### Changes
- Changed column name in database queries from `patient_id` to `id`
- Updated all result data extraction to use the correct field name
- Fixed potential errors that would occur when querying and processing patient records

### Benefits
- Fixed errors in patient retrieval and creation from platform IDs
- Ensured proper cross-platform user identification
- Maintained cross-platform memory isolation

## 2023-10-27: Added Patient ID to Memory Service Calls

### Summary
Updated all memory service calls in the Telegram bot to include the required patient_id parameter.

### Changes
- Added helper method `_get_patient_id()` to fetch patient records from Supabase using telegram_id
- Modified all `get_session_memory()` calls to include patient_id parameter
- Modified all `store_session_memory()` calls to include patient_id parameter
- Added proper error handling when patient_id cannot be found
- Corrected import path for `get_patient_id_from_platform_id` function from graph.utils.nodes

### Benefits
- Fixed "MemoryService.get_session_memory() missing 1 required positional argument: 'patient_id'" error
- Improved patient context tracking in conversation history
- Better integration with the patient management system
- Automatic creation of patient records if they don't exist

## 2023-10-26: Reduced Scheduler Logging

### Summary
Modified the scheduler logging configuration to hide most scheduler-related logs by default.

### Changes
- Added `SCHEDULER_LOG_LEVEL` setting to control scheduler logging independently (defaults to ERROR)
- Modified Telegram bot to use this setting for all scheduler-related logs
- Updated scheduler modules to configure their loggers with the same level
- Made all scheduler log outputs conditional based on the configured log level

### Benefits
- Cleaner console output with less noise from scheduler operations
- Ability to control scheduler logging independently from other components
- More readable logs focusing on important application events

### How to Use
To adjust the scheduler logging level, set the `SCHEDULER_LOG_LEVEL` environment variable or modify it in settings.py. Valid values are: DEBUG, INFO, WARNING, ERROR, CRITICAL.

## 2023-10-25: Memory System Migration to Supabase-only

### Summary
Migrated short-term memory storage from SQLite to Supabase-only, removing local file system dependencies.

### Changes
- Modified `settings.py` to remove SQLite database file creation
- Updated `SHORT_TERM_MEMORY_DB_PATH` to use in-memory mode by default
- Removed unused checkpoint directory functionality from Telegram bot
- Ensured LangGraph configurations use `use_supabase_only: True` flag
- Deprecated local memory checkpoints in Telegram interface 

### Benefits
- Improved deployment flexibility across different environments
- Removed dependency on local file system for memory persistence
- Centralized data storage for better access across different interfaces
- Simplified maintenance and reduced potential for data corruption

### Breaking Changes
- Removed support for local SQLite database file for memory storage
- All deployments now require Supabase connection for memory persistence

## 2025-05-12: Updated Database Schema Compatibility

### Summary
Fixed patient registration and identification to work with current database schema.

### Changes
- Updated patient registration in `get_patient_id_from_platform_id` to use existing columns only
- Modified patient lookup to use `system_id` field as primary identifier
- Changed patient data storage to use `email` field for platform metadata
- Removed dependencies on non-existent columns like `telegram_id` and `platform_data`

### Benefits
- Fixed "column patients.telegram_id does not exist" errors
- Fixed "column patients.platform_data does not exist" errors
- Enabled successful patient creation in current database schema
- Ensured backward compatibility with existing patient records

## 2025-05-12: Improved Logging Configuration

### Summary
Enhanced logging configuration to reduce noise and better control verbosity.

### Changes
- Added `LOGGING_LEVEL` setting to control application-wide logging level
- Set HTTP client libraries (httpx, urllib3, httpcore) to WARNING level by default
- Updated telegram_bot.py to use the centralized logging configuration
- Removed redundant and verbose debug logs

### Benefits
- Cleaner console output with less noise from HTTP requests
- Centralized control of logging verbosity through environment variables
- Easier troubleshooting by focusing on important logs
- Reduced log storage requirements in production

## 2025-05-12: Fixed Import and API Issues

### Summary
Fixed critical import path errors and method synchronization issues.

### Changes
- Fixed import path in telegram_bot.py to use correct path for get_patient_id_from_platform_id (ai_companion.graph.nodes)
- Added get_cached_messages method to ShortTermMemoryManager for compatibility with memory service
- Fixed _get_patient_id method in TelegramBot to properly call get_patient_id_from_platform_id without await

### Benefits
- Fixed ModuleNotFoundError when running the Telegram bot
- Fixed 'ShortTermMemoryManager has no attribute get_cached_messages' error
- Enabled proper patient creation and identification in the Telegram interface
- Ensured compatibility between memory service and memory manager implementations

## 2025-05-12: Fixed OpenAI SDK Compatibility and Memory System Issues

### Summary
Fixed compatibility issues with OpenAI SDK v1.x and improved memory system reliability.

### Changes
- Updated imports in vector_store.py to use new OpenAI v1.x error class structure
- Fixed memory storage in conversation_node with proper metadata parameter
- Replaced hardcoded test patient ID in health checks with real database lookups
- Added comprehensive error handling for memory operations

### Benefits
- Fixed "No module named 'openai.error'" errors in RAG node
- Fixed "MemoryManager.add_memory() missing 1 required positional argument: 'metadata'" error
- Improved health check reliability with real patient data
- Better error handling and logging for memory operations

## 2025-05-12: Updated Database Schema Compatibility

### Summary
Fixed patient registration and identification to work with current database schema.

### Changes
- Updated patient registration in `get_patient_id_from_platform_id` to use existing columns only
- Modified patient lookup to use `system_id` field as primary identifier
- Changed patient data storage to use `email` field for platform metadata
- Removed dependencies on non-existent columns like `telegram_id` and `platform_data`

### Benefits
- Fixed "column patients.telegram_id does not exist" errors
- Fixed "column patients.platform_data does not exist" errors
- Enabled successful patient creation in current database schema
- Ensured backward compatibility with existing patient records

## 2025-05-12: Improved Logging Configuration

### Summary
Enhanced logging configuration to reduce noise and better control verbosity.

### Changes
- Added `LOGGING_LEVEL` setting to control application-wide logging level
- Set HTTP client libraries (httpx, urllib3, httpcore) to WARNING level by default
- Updated telegram_bot.py to use the centralized logging configuration
- Removed redundant and verbose debug logs

### Benefits
- Cleaner console output with less noise from HTTP requests
- Centralized control of logging verbosity through environment variables
- Easier troubleshooting by focusing on important logs
- Reduced log storage requirements in production

## 2025-05-12: Fixed Import and API Issues

### Summary
Fixed critical import path errors and method synchronization issues.

### Changes
- Fixed import path in telegram_bot.py to use correct path for get_patient_id_from_platform_id (ai_companion.graph.nodes)
- Added get_cached_messages method to ShortTermMemoryManager for compatibility with memory service
- Fixed _get_patient_id method in TelegramBot to properly call get_patient_id_from_platform_id without await

### Benefits
- Fixed ModuleNotFoundError when running the Telegram bot
- Fixed 'ShortTermMemoryManager has no attribute get_cached_messages' error
- Enabled proper patient creation and identification in the Telegram interface
- Ensured compatibility between memory service and memory manager implementations

## 2025-05-12: Enhanced Patient Message Logging

### Summary
Improved logging system to provide clear visibility into patient communications and system operations.

### Changes
- Added structured message logging with patient ID tagging in telegram_bot.py
- Enhanced bot response logging with patient context and message details
- Added detailed memory extraction and retrieval logging
- Standardized log format for easier filtering and analysis

### Benefits
- Better debugging capabilities for patient communications
- Clear traceability between patients and their messages
- Improved visibility into memory operations
- More structured logs for better filtering and analysis

## 2025-05-12: Fixed Patient Memory System

### Summary
Fixed critical issues with patient memory retrieval and storage in the graph nodes.

### Changes
- Fixed memory extraction node to properly get user metadata from configurable
- Enhanced memory injection node with better error handling and metadata validation
- Updated conversation node to reliably store user and AI messages with patient_id
- Added comprehensive logging of memory operations
- Fixed patient_id detection and propagation throughout the system

### Benefits
- Fixed "No patient_id found for :, memory extraction skipped" error
- Fixed memory storage that was causing messages to be lost
- Improved debugging with detailed memory operation logs
- Enabled proper memory retrieval for existing patients
- Better error messages when patient identification fails

## 2025-05-13: Renamed user_id to external_system_id for Better Clarity

### Summary
Improved code clarity by renaming "user_id" to "external_system_id" to better distinguish between platform-specific IDs and internal patient IDs.

### Changes
- Renamed "user_id" to "external_system_id" in user_metadata structures
- Updated all references in telegram_bot.py to use the new naming
- Modified memory_extraction_node and memory_injection_node to handle the renamed field
- Added backward compatibility for existing code that still uses "user_id"

### Benefits
- Clearer distinction between external platform identifiers and internal patient IDs
- Reduced confusion in code dealing with different types of user identifiers
- Better self-documenting code with more descriptive variable names
- Maintained backward compatibility with existing code

## 2023-11-03: Fixed Database Queries in MemoryService

### Summary
Fixed multiple database errors in MemoryService including incorrect JSONB query syntax, non-existent 'metadata' column issue, and order() method parameters.

### Changes
- Updated database queries to use proper PostgreSQL JSONB path syntax (`context->'metadata'->>'session_id'`) for querying nested JSON fields
- Fixed `order()` method parameters to use `desc=True` instead of object notation that was causing "takes 2 positional arguments but 3 were given" errors
- Improved error handling for database queries
- Improved data retrieval from the short_term_memory table

### Benefits
- Fixed error "column short_term_memory.metadata does not exist"
- Fixed error "BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given"
- Fixed error "invalid input syntax for type json"
- Improved database query performance by using proper JSONB indexing paths
- More accurate record retrieval by using exact field matches
- Better compatibility with PostgreSQL JSON data types

## 2023-11-04: Improved Patient ID Propagation Across Memory System

### Summary
Fixed issues with patient ID propagation through the memory system where the patient was correctly identified initially but lost during processing.

### Changes
- Enhanced `memory_extraction_node` to properly store patient_id in state and metadata
- Updated `memory_injection_node` to use patient_id from state when available
- Improved `conversation_node` to prioritize patient_id from state and correctly check for its presence
- Upgraded `_send_direct_response` in TelegramBot to use multiple sources for user ID extraction
- Added more robust fallback mechanisms in all memory-related functions
- Enhanced logging for better debugging of patient ID issues

### Benefits
- Fixed "Patient: unknown" issue in bot responses even when patient is correctly identified
- More reliable memory storage and retrieval with proper patient context
- Better continuity of patient identity throughout conversation
- Improved memory extraction and storage success rate
- More comprehensive logging for easier troubleshooting

## 2023-11-05: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-06: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-07: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-08: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-09: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-10: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-11: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-12: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-13: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-14: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-15: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-16: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-17: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-18: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-19: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-20: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-21: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-22: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-23: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-24: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-25: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-26: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-27: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-28: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-29: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-30: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-01: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-02: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-03: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-04: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-05: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-06: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-07: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-08: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-09: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-10: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-12-11: Fixed Memory Retrieval Methods

### Summary
Fixed the error "ShortTermMemoryManager has no attribute 'get_messages_parallel'" by adding compatibility methods and improving error handling.

### Changes
- Added back the `get_cached_messages` method to ShortTermMemoryManager as a compatibility method that calls `get_messages_parallel`
- Updated MemoryService to try different memory retrieval methods with proper fallbacks
- Enhanced error handling in memory retrieval operations
- Added progressive fallback to direct database query if memory methods fail

### Benefits
- Fixed "ShortTermMemoryManager has no attribute 'get_messages_parallel'" error in memory service
- Improved reliability of memory retrieval with multiple fallback options
- Better logging and error reporting for memory operations
- Maintained backward compatibility with both memory retrieval methods

## 2023-11-05: Fixed Patient ID Storage in Short-Term Memory

### Summary
Fixed the issue where patient_id was being stored only in the JSON metadata but not in the dedicated patient_id column in the short_term_memory table.

### Changes
- Updated `store_memory` method in ShortTermMemoryManager to extract patient_id from metadata and store it in the database record's patient_id column
- Modified `get_relevant_memories` method to properly query the database using patient_id column 
- Changed `context` field storage format to ensure metadata is consistently accessible
- Fixed memory lookup to properly search by patient_id instead of only in context/metadata

### Benefits
- Fixed "Patient: unknown" issue where patient was identified but memories couldn't be found
- Improved memory retrieval reliability by using proper database schema
- Added proper support for the patient_id column in the short_term_memory table
- Enhanced error logging and detection for memory retrieval issues

## May 13, 2025
- Fixed memory extraction issue where patient_id wasn't being properly passed to memory extraction node
- Added patient_id to human message metadata before passing to graph processing
- Enhanced memory_extraction_node and memory_injection_node to better retrieve patient_id from various sources
- Improved logging for memory-related operations to facilitate debugging
- Fixed patient ID data flow from Telegram to memory extraction components

## May 12, 2025
- Fixed memory retrieval issues where patient IDs weren't being properly stored in the database
- Updated the `store_memory` method to extract patient_id from nested metadata/context structures
- Modified the `get_relevant_memories` method to properly query records by patient_id
- Fixed context JSON structure in database records to ensure consistent data access
- Created test script to validate memory storage and retrieval with patient_id
- Fixed database record creation to only include fields that exist in the schema
- Fixed SQL ordering to use expires_at instead of non-existent created_at field

## May 10, 2025
- Added support for multilingual conversations
- Expanded knowledge base with latest healthcare information
- Fixed image generation capability in the Telegram interface

## April 28, 2025
- Initial deployment of AI companion
- Added support for Telegram and Web interfaces
- Implemented conversation memory system
- Added RAG capabilities for medical information retrieval

## 2025-05-14: Fixed Memory Storage in Conversation Node

### Summary
Fixed the memory storage in conversation_node to properly use the memory manager API.

### Changes
- Removed unsupported memory_type and memory_key parameters from add_memory call in conversation_node
- Fixed TypeError: "MemoryManager.add_memory() got an unexpected keyword argument 'memory_type'"
- Aligned the memory storage code with the API specification of the MemoryManager.add_memory method

### Benefits
- Fixed critical error preventing proper memory storage during conversations
- Ensured conversation memories are properly stored in the database
- Restored memory functionality for contextual responses

## 2025-05-14: Fixed HumanMessage Import Error in Telegram Bot

### Summary
Fixed an error in the Telegram bot where HumanMessage was not being recognized despite being imported at the top of the file.

### Changes
- Added explicit comment to the import statement for langchain_core.messages
- Ensured proper recognition of the HumanMessage class in the scope
- Fixed "NameError: name 'HumanMessage' is not defined" error

### Benefits
- Fixed critical error that was preventing the Telegram bot from running
- Improved code clarity with better import documentation
- Enhanced stability of the message handling in the Telegram interface

## 2025-05-15: Enhanced Memory Retrieval Logic

### Summary
Enhanced the memory retrieval logic to better handle different data formats and properly retrieve existing memories from the database.

### Changes
- Improved the `get_relevant_memories` method to handle various data formats and structures
- Enhanced the memory content extraction logic to handle both direct content and nested JSON structures
- Added robust error handling and detailed logging throughout the memory retrieval process
- Improved memory formatting for prompts to include timestamps and better content display
- Created test script to validate memory retrieval functionality works with existing records
- Fixed issues causing "NO MEMORIES" errors despite memories existing in the database

### Benefits
- Fixed critical issue where memories exist in database but were not being retrieved
- Improved system resilience when dealing with different memory storage formats
- Better debugging capabilities through enhanced logging
- More user-friendly memory display with timestamps and formatting

## 2025-05-16: Fixed Short-Term Memory Expiration

### Summary
Modified short-term memory system to prevent memories from expiring after a short period.

### Changes
- Changed default TTL (time-to-live) for memories from 60 minutes to 1 year (525600 minutes)
- Updated all memory storage methods to use the longer TTL value
- Modified cache initialization to use consistent TTL settings
- Added clear comments that memories should not expire

### Benefits
- Ensures patient memories persist long-term rather than being lost after an hour
- Improved conversation context by maintaining full memory history
- Consistent memory retention across all memory storage mechanisms
- Better knowledge continuity for returning patients

## 2025-05-12: Fixed Coroutine Await Issues

### Issues:
- Multiple `RuntimeWarning: coroutine was never awaited` errors throughout the application
- Memory retrieval failing with `object of type 'coroutine' has no len()` error
- Async functions not properly awaited in several places

### Fixes:
- Updated `memory_injection_node` to properly await the `get_relevant_memories` async function
- Fixed `memory_extraction_node` to properly await both `get_relevant_memories` and `extract_and_store_memories`
- Fixed `conversation_node` to properly await the `add_memory` call
- Created test script `test_coroutine_fix.py` to verify the fixes

### Impact:
- Eliminated runtime warnings about never-awaited coroutines
- Fixed memory retrieval functionality
- Improved stability of async operations throughout the memory system

### Notes:
- All async functions now properly use the `await` keyword when calling other async functions
- Added better error handling around async calls
- Updated logging to handle awaited results properly

## 2025-05-12: SQLite Database Removal

Migrated short-term memory storage from SQLite to Supabase-only, removing local file system dependencies.

### Changes:
- Modified `settings.py` to remove SQLite database file creation
- Updated WhatsApp and Chainlit integrations to use Supabase
- Fixed indentation and formatting issues in related code
- Added proper patient ID handling in web interfaces
- Updated documentation in project-docs/memory_update.md

### Benefits:
- Eliminated permission issues with local file creation
- Improved reliability by centralizing storage
- Fixed inconsistent memory storage issues
- Enabled better cross-platform support
- Removed support for local SQLite database file for memory storage

### Testing:
- Verified successful Supabase connections
- Confirmed memory retrieval works for different patient records
- Validated proper handling of different data formats

## Previous Changes
// ... existing content ...

## 2025-05-12: Memory Storage System Upgrade

* Removed all SQLite database file dependencies from the application
* Deleted existing SQLite database files that were causing permission issues
* Updated WhatsApp interface to use Supabase exclusively for memory storage
* Fixed Chainlit interface to remove SQLite dependencies
* Verified all interfaces now use Supabase for memory storage
* Updated test scripts to validate proper Supabase memory functionality
* Documented changes in project documentation

## 2025-05-01: Memory System Update

* Implemented comprehensive memory system using Supabase
* Fixed inconsistent JSON handling across interfaces
* Added patient ID tracking for all interfaces
* Improved memory injection workflow
* Standardized conversation history access

## 2025-04-15: LangGraph Integration

* Updated the code base to use LangGraph for conversational workflows
* Implemented node-based conversation processing
* Added support for multi-step reasoning
* Integrated memory system with graph state management
* Created new documentation for graph-based workflow