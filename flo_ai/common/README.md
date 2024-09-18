# Understanding Log Levels

FLO uses standard Python logging levels to indicate the severity of logged messages. Here are the common levels used (from least to most severe):

DEBUG: Detailed information for debugging purposes.
INFO: Informational messages about the normal operation of the system.
WARNING: Potential issues or unexpected conditions.
ERROR: Errors that may have caused the system to malfunction.
CRITICAL: Critical errors that have caused the system to crash.
By adjusting the log level, you can control how much information is logged and the verbosity of the output.

Controlling Log Levels
FLO provides multiple ways to control log levels:

1. Environment Variables:

Export environment variables to set the log level for specific components before running the application:

FLO_LOG_LEVEL_COMMON: Controls the level for the "CommonLogs" logger.
FLO_LOG_LEVEL_BUILDER: Controls the level for the "BuilderLogs" logger.
FLO_LOG_LEVEL_SESSION: Controls the level for the "SessionLogs" logger.

Example:

export FLO_LOG_LEVEL_COMMON=DEBUG
export FLO_LOG_LEVEL_BUILDER=INFO
export FLO_LOG_LEVEL_SESSION=WARNING


2. FloSession Creation:

When creating a FloSession object, you can specify the desired log level:

session = FloSession(llm, log_level="DEBUG")

 This session will log messages at DEBUG level and above.

3. Flo Instance Creation:

Similar to FloSession, you can set the log level when creating a Flo instance:

flo = Flo.build(session, yaml_config, log_level="DEBUG")

This Flo instance will inherit the specified log level.

4. Global Log Level Change (Runtime):

You can dynamically change the global log level at runtime using the set_global_log_level function from flo_ai.common.logging_config:

from flo_ai.common.logging_config import set_global_log_level

set_global_log_level("DEBUG")  # Set the global log level to DEBUG

This will affect all logging throughout the application.

5. Specific Logger Level Change (Runtime):

If you need to adjust the level for a specific logger, use the set_log_level method of the FloLogger class:

from flo_ai.common.logging_config import FloLogger

FloLogger.set_log_level("COMMON", "DEBUG")  # Set COMMON logger to DEBUG level


Environment variables: Use these for setting default levels without modifying code, useful in different deployment environments.
Object creation: This approach allows setting specific levels for individual sessions or Flo instances.
Runtime changes: Use these methods for dynamic adjustments during program execution.