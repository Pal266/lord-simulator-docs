# Title

Logging Framework

# Type

feature

# Description

Establish the Lord Simulator project logging framework.

The framework provides project-specific logging independently from general Unreal Engine logging. It supports two project logging modes, writes Lord Simulator log entries to a dedicated log file in the current Windows user's Documents folder, and initializes early enough to be available to other Lord Simulator systems.

This specification establishes the logging infrastructure and initial Default mode behavior. A mechanism for selecting or switching logging modes is outside the scope of this specification.

# Requirements

1. Implement a Lord Simulator project logging framework using functionality already available through the project's established Unreal Engine, C++ standard library, Windows platform facilities, or existing dependencies.

2. The logging framework MUST capture Lord Simulator project log entries only. General Unreal Engine log output MUST NOT be copied into the Lord Simulator log file.

3. The logging framework MUST support two project logging modes:

    * `Default`
    * `Development`

4. `Default` MUST be the active logging mode after implementation of this specification.

5. A mechanism for configuring, selecting, or switching between `Default` and `Development` modes MUST NOT be implemented as part of this specification.

6. Log entries designated for `Default` MUST be written when the logging framework operates in `Default` mode.

7. `Development` mode MUST include all log entries designated for `Default`, plus log entries designated specifically for `Development`.

8. Development-only log entries MUST NOT be written while the framework operates in `Default` mode.

9. `Development` mode is intended to support substantially more detailed diagnostic logging. Logging performed exclusively in `Development` mode MAY be performance-heavy.

10. The logging framework MUST be initialized as early as reasonably possible in the Lord Simulator application/module startup sequence and before other Lord Simulator systems that may produce project log entries.

11. The logging framework MUST operate both:

    * when Lord Simulator is executed during development through Unreal Editor/PIE;
    * when Lord Simulator is executed as a packaged Windows application.

12. The logging framework MUST use the current Windows user's Documents known folder as the root location for Lord Simulator logging data.

13. A directory named exactly:

    `Lord Simulator`

    MUST exist directly inside the current Windows user's Documents known folder.

14. The project installer MUST create the `Lord Simulator` directory in the current Windows user's Documents known folder during installation.

15. At application startup, the logging framework MUST ensure that the `Lord Simulator` directory exists.

16. If the `Lord Simulator` directory does not exist at application startup, the logging framework MUST attempt to create it.

17. The logging framework MUST use the following file as the Lord Simulator log file:

    `Documents\Lord Simulator\log.log`

    where `Documents` represents the current Windows user's Documents known folder rather than a hard-coded filesystem path.

18. On every application startup, the logging framework MUST start a new log for the current application session.

19. If `log.log` does not exist when the logging framework initializes, it MUST be created.

20. If `log.log` already exists when the logging framework initializes, its existing contents MUST be removed before log entries for the new application session are written.

21. Consequently, `log.log` MUST contain log entries for the current application session only. Preservation, rotation, or archival of previous session logs MUST NOT be implemented as part of this specification.

22. `log.log` MUST use UTF-8 encoding.

23. All Lord Simulator log messages MUST be written in English.

24. Every Lord Simulator log entry MUST contain a timestamp.

25. Timestamps MUST use the local system time.

26. Timestamps MUST use the following format:

    `YYYY-MM-DD HH:MM:SS`

    Example:

    `2026-10-29 15:20:31`

27. Every log entry MUST use the following basic format:

    `[YYYY-MM-DD HH:MM:SS] Message`

28. This specification MUST introduce exactly one required Lord Simulator log message:

    `New log file was created.`

29. The message `New log file was created.` MUST be designated for `Default` mode.

30. After the log file has been successfully created or an existing log file has been successfully cleared for the new application session, the logging framework MUST write:

    `[YYYY-MM-DD HH:MM:SS] New log file was created.`

    using the actual local system timestamp at the time the entry is written.

31. Because `Development` mode includes all `Default` log entries, `New log file was created.` MUST also be logged when the framework operates in `Development` mode in the future.

32. Failure to create the `Lord Simulator` directory, create or clear `log.log`, initialize file logging, or write a log entry MUST NOT prevent Lord Simulator from continuing its normal startup.

33. Logging failures MUST NOT intentionally terminate or crash the application.

34. No new third-party library, framework, package, plugin, SDK, or other external dependency is required by this specification.

# Acceptance Criteria

1. The project builds successfully after implementation of the logging framework.

2. Lord Simulator launches successfully in Unreal Editor/PIE with `Default` logging mode active.

3. Lord Simulator launches successfully as a packaged Windows application with `Default` logging mode active.

4. The project installer creates a directory named `Lord Simulator` inside the current Windows user's Documents known folder.

5. If the `Lord Simulator` directory is deleted after installation, launching Lord Simulator recreates the directory.

6. On application startup, `log.log` exists at:

   `Documents\Lord Simulator\log.log`

7. If `log.log` did not exist before startup, it is created.

8. If `log.log` contained data before startup, that data is removed and is not present after the new session starts.

9. `log.log` is encoded as UTF-8.

10. After startup, the log contains the entry:

    `[YYYY-MM-DD HH:MM:SS] New log file was created.`

    with the timestamp replaced by the actual local system time in the required format.

11. The startup log entry is produced when running through Unreal Editor/PIE.

12. The startup log entry is produced when running the packaged Windows application.

13. The Lord Simulator log file does not contain general Unreal Engine log output.

14. No Development-only log entries are produced while `Default` mode is active.

15. Failure to create or write the Lord Simulator log file does not intentionally terminate the application or prevent normal application startup.

16. No new third-party library, framework, package, plugin, SDK, or other external dependency is introduced to implement this specification.
