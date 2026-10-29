# Title

Log Application Shutdown

# Type

feature

# Description

Add a Lord Simulator log entry when the application begins a normal
shutdown.

# Requirements

1.  When Lord Simulator begins its normal application/module shutdown,
    write a log entry before the logging framework is shut down.

2.  The log entry MUST use `Default` logging mode.

3.  The exact log message MUST be:

    `Application shutdown started.`

# Acceptance Criteria

1.  When Lord Simulator performs a normal shutdown, the log contains:

    `[YYYY-MM-DD HH:MM:SS] Application shutdown started.`

2.  The shutdown log entry is written before the logging framework is
    shut down.

3.  The shutdown log entry uses `Default` logging mode.
