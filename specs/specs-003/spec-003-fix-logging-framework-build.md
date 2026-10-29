# Title

Fix Logging Framework Build

# Type

bugfix

# Description

Fix the compilation failure in the Lord Simulator logging framework.

The logging framework source file currently includes
`Logging/LordSimulatorLog.h`, but the project's current module structure
and include configuration do not allow the compiler to resolve that
header path.

As a result, both the `LordSimulatorEditor` Development build and the
`LordSimulator` Shipping build fail with a `C1083` header-not-found
compilation error.

This specification fixes the build issue without changing the intended
behavior of the existing logging framework.

# Requirements

1.  Fix the Lord Simulator logging framework so that its header files
    are correctly resolved by the Unreal Engine build system.

2.  The following compilation error MUST be eliminated:

    `fatal error C1083: Cannot open include file: 'Logging/LordSimulatorLog.h': No such file or directory`

3.  The implementation MUST use a module source/header structure and
    include configuration that are valid for the Lord Simulator Unreal
    Engine module.

4.  The fix MUST NOT rely on machine-specific or absolute filesystem
    include paths.

5.  The `LordSimulatorEditor` target MUST compile successfully for:

    -   Platform: `Win64`
    -   Configuration: `Development`

6.  The `LordSimulator` target MUST compile successfully for:

    -   Platform: `Win64`
    -   Configuration: `Shipping`

7.  The existing Lord Simulator logging framework behavior MUST remain
    unchanged by this bugfix.

8.  The logging framework MUST continue to support the existing project
    logging modes:

    -   `Default`
    -   `Development`

9.  `Default` MUST remain the active logging mode.

10. The logging framework MUST continue to write Lord Simulator project
    log entries only and MUST NOT capture general Unreal Engine log
    output.

11. The logging framework MUST continue to create or recreate the
    `Lord Simulator` directory under the current Windows user's
    Documents known folder when required at application startup.

12. The logging framework MUST continue to create or truncate:

    `Documents\Lord Simulator\log.log`

    at application startup.

13. The log file MUST continue to use UTF-8 encoding.

14. Existing log entries MUST continue to use local system timestamps in
    the following format:

    `YYYY-MM-DD HH:MM:SS`

15. Application startup MUST continue to produce the existing
    Default-mode log entry:

    `[YYYY-MM-DD HH:MM:SS] New log file was created.`

16. The logging framework MUST continue to operate when Lord Simulator
    is executed through Unreal Editor/PIE and when executed as a
    packaged Windows application.

17. Logging failures MUST continue to avoid intentionally terminating or
    preventing normal startup of Lord Simulator.

18. No new third-party library, framework, package, plugin, SDK, or
    other external dependency is required by this specification.

# Acceptance Criteria

1.  Building `LordSimulatorEditor Win64 Development` completes
    successfully without the `C1083` error for
    `Logging/LordSimulatorLog.h`.

2.  Building `LordSimulator Win64 Shipping` completes successfully
    without the `C1083` error for `Logging/LordSimulatorLog.h`.

3.  No machine-specific or absolute filesystem include path is required
    for either build.

4.  Lord Simulator launches successfully through Unreal Editor/PIE after
    the fix.

5.  The packaged Windows application builds and launches successfully
    after the fix.

6.  Starting Lord Simulator creates or truncates:

    `Documents\Lord Simulator\log.log`

7.  After startup, the log contains:

    `[YYYY-MM-DD HH:MM:SS] New log file was created.`

    with the timestamp replaced by the actual local system time in the
    required format.

8.  The log file contains Lord Simulator project log entries only and
    does not contain general Unreal Engine log output.

9.  `Default` remains the active logging mode.

10. No new third-party library, framework, package, plugin, SDK, or
    other external dependency is introduced by the bugfix.
