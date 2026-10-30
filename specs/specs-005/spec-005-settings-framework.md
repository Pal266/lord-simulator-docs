# Title

Settings Framework

# Type

feature

# Description

Implement the Lord Simulator persistent settings framework and introduce
`LogMode` as the first setting.

Settings are stored between application launches in a complete INI
settings file and are loaded into a complete in-memory settings object
during application startup.

# Requirements

1.  Implement a Lord Simulator settings system with a complete in-memory
    settings object.

2.  Store persistent settings in:

    `Documents\Lord Simulator\settings.ini`

3.  Use INI format for the settings file.

4.  If `settings.ini` does not exist during startup:

    -   create it;
    -   write the complete settings object using defined default values;
    -   continue startup using those values.

5.  When the settings file is created or saved, it MUST contain every
    persistent setting, including settings whose current values equal
    their defaults.

6.  Settings MUST be loaded from persistent storage as one complete
    state. Individual settings MUST NOT be independently loaded or
    reloaded from the settings file.

7.  Reading settings from disk MUST construct a complete settings state
    before replacing the current in-memory settings state.

8.  Introduce the persistent setting `LogMode`.

9.  `LogMode` MUST support exactly these case-sensitive values:

    -   `Default`
    -   `Development`

10. The default value of `LogMode` MUST be:

    `Default`

11. If `LogMode` is missing from an existing settings file, use its
    default value.

12. If `LogMode` contains any value other than the exact case-sensitive
    values `Default` or `Development`, use its default value.

13. If the settings file cannot be read, load the complete settings
    object using defined default values.

14. Application startup MUST occur in this order:

    1.  initialize the Lord Simulator logging framework in `Default`
        mode;
    2.  log that settings loading has started;
    3.  load the complete settings object;
    4.  apply the loaded `LogMode` to the logging framework;
    5.  log that settings loading has completed;
    6.  continue application startup.

15. The logging framework MUST support applying the `LogMode` stored in
    the settings object at runtime.

16. Reading or reloading settings from persistent storage MUST always
    reload the complete settings state. Runtime modification of a
    setting MUST modify the in-memory settings object without
    independently reloading that setting from persistent storage.

17. During normal application shutdown, after the existing
    application-shutdown log entry and before the logging framework is
    shut down:

    1.  read the actual persistent settings file;
    2.  compare its complete persistent settings state with the current
        complete in-memory settings object;
    3.  if they are equivalent, do not write the settings file;
    4.  if they differ, write the complete in-memory settings object to
        `settings.ini`;
    5.  keep the logging framework active until settings persistence and
        settings-system shutdown are complete.

18. Anything that prevents the persistent settings file from producing a
    complete state equivalent to the in-memory settings object during
    shutdown comparison MUST be treated as a difference. This includes
    the file being missing, unreadable, or containing a missing or
    invalid required setting.

19. When a shutdown save is required, the complete in-memory settings
    state MUST overwrite the persistent settings file. External changes
    made to `settings.ini` while the application is running do not
    override the current in-memory settings state.

20. Failure to save settings during shutdown MUST NOT intentionally
    crash the application or prevent shutdown from continuing.

21. Use the following Lord Simulator log entries. All entries MUST use
    `Default` logging mode and the exact messages shown:

    -   When settings loading begins:

        `Settings loading started.`

    -   When settings loading completes:

        `Settings loading completed.`

    -   When `settings.ini` does not exist during startup:

        `Settings file does not exist. A new settings file will be created.`

    -   When a new settings file is successfully created:

        `Settings file was created.`

    -   When a new settings file cannot be created:

        `Settings file could not be created. Default settings will be used.`

    -   When an existing settings file cannot be read during settings
        loading:

        `Settings file could not be read. Default settings will be used.`

    -   When `LogMode` is missing during settings loading:

        `Setting 'LogMode' is missing. Default value 'Default' will be used.`

    -   When `LogMode` contains an invalid value during settings
        loading:

        `Setting 'LogMode' has an invalid value. Default value 'Default' will be used.`

    -   When changed settings are successfully saved during shutdown:

        `Settings were saved.`

    -   When settings that require saving cannot be saved during
        shutdown:

        `Settings could not be saved.`

22. Shutdown comparison MUST NOT load the persistent file into the
    active in-memory settings object. Its purpose is only to determine
    whether the persistent state is equivalent to the current in-memory
    state.

23. No new third-party dependency is required for this specification.

# Acceptance Criteria

1.  On first startup without `settings.ini`, the application creates:

    `Documents\Lord Simulator\settings.ini`

2.  The newly created file contains the complete persistent settings
    state, including:

    `LogMode=Default`

3.  A valid `LogMode=Default` is loaded and the logging framework
    operates in `Default` mode.

4.  A valid `LogMode=Development` is loaded and the logging framework
    operates in `Development` mode.

5.  `LogMode` values are case-sensitive.

6.  A missing `LogMode` results in `Default` being used and the required
    missing-setting log entry being written.

7.  An invalid `LogMode` results in `Default` being used and the
    required invalid-setting log entry being written.

8.  An unreadable settings file results in the complete settings state
    using defined defaults and the required read-failure log entry being
    written.

9.  Settings loading writes `Settings loading started.` before reading
    the settings and writes `Settings loading completed.` after the
    loaded `LogMode` has been applied.

10. During normal shutdown, an unchanged persistent settings state is
    not rewritten.

11. During normal shutdown, a persistent settings state that differs
    from the in-memory settings state is overwritten with the complete
    in-memory settings state and `Settings were saved.` is logged.

12. A missing, unreadable, incomplete, or invalid persistent settings
    state during shutdown is treated as different and causes the system
    to attempt to write the complete in-memory settings state.

13. If a required shutdown save fails, `Settings could not be saved.` is
    logged and application shutdown continues.

14. Settings persistence completes before the Lord Simulator logging
    framework is shut down.

15. All settings-related log entries required by this specification use
    `Default` mode and exactly match the messages defined in the
    Requirements.
