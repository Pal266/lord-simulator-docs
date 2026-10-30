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

4.  The persistent settings file MUST contain a `[Settings]` section.
    Persistent Lord Simulator settings MUST be stored in this section.

5.  The `[Settings]` section name MUST be matched case-sensitively.
    Leading and trailing whitespace surrounding the complete
    section-header line MUST be ignored. Whitespace inside the section
    header MUST NOT be ignored. Only the exact section name `[Settings]`
    identifies the Lord Simulator settings section.

6.  If `settings.ini` does not exist during startup:

    -   create it;
    -   write the complete settings object using defined default values;
    -   continue startup using those values.

7.  When the settings file is created or saved, it MUST contain every
    persistent setting, including settings whose current values equal
    their defaults.

8.  Settings MUST be loaded from persistent storage as one complete
    state. Individual settings MUST NOT be independently loaded or
    reloaded from the settings file.

9.  Reading settings from disk MUST construct a complete settings state
    before replacing the current in-memory settings state.

10. Introduce the persistent setting `LogMode`.

11. `LogMode` MUST be stored in the `[Settings]` section.

12. `LogMode` MUST support exactly these case-sensitive values:

-   `Default`
-   `Development`

13. The default value of `LogMode` MUST be:

    `Default`

14. Setting keys and defined setting values MUST be matched
    case-sensitively. Leading and trailing whitespace surrounding keys
    and values MUST be ignored when reading them.

15. Blank lines and lines beginning with `;` or `#` MAY be ignored when
    reading the settings file.

16. A setting appearing more than once in the `[Settings]` section MUST
    be treated as invalid. For `LogMode`, the defined invalid-value
    fallback and log behavior MUST apply.

17. A setting outside the `[Settings]` section MUST NOT satisfy the
    requirement for that setting in the `[Settings]` section.

18. If `LogMode` is missing from the `[Settings]` section of an existing
    settings file, use its default value.

19. If `LogMode` contains any value other than the exact case-sensitive
    values `Default` or `Development`, use its default value.

20. If the settings file cannot be read, load the complete settings
    object using defined default values.

21. Application startup MUST occur in this order:

    1.  initialize the Lord Simulator logging framework in `Default`
        mode;
    2.  log that settings loading has started;
    3.  load the complete settings object;
    4.  apply the loaded `LogMode` to the logging framework;
    5.  log that settings loading has completed;
    6.  continue application startup.

22. The logging framework MUST support applying the `LogMode` stored in
    the settings object at runtime.

23. Reading or reloading settings from persistent storage MUST always
    reload the complete settings state. Runtime modification of a
    setting MUST modify the in-memory settings object without
    independently reloading that setting from persistent storage.

24. During normal application shutdown, after the existing
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

25. Anything that prevents the persistent settings file from producing a
    complete state equivalent to the in-memory settings object during
    shutdown comparison MUST be treated as a difference. This includes
    the file being missing, unreadable, lacking the exact `[Settings]`
    section, or containing a missing, duplicate, or invalid required
    setting.

26. When a shutdown save is required, the complete in-memory settings
    state MUST overwrite the persistent settings file. External changes
    made to `settings.ini` while the application is running do not
    override the current in-memory settings state.

27. Failure to save settings during shutdown MUST NOT intentionally
    crash the application or prevent shutdown from continuing.

28. Use the following Lord Simulator log entries. All entries MUST use
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

    -   When `LogMode` is missing from the exact `[Settings]` section
        during settings loading:

        `Setting 'LogMode' is missing. Default value 'Default' will be used.`

    -   When `LogMode` contains an invalid value during settings
        loading, including when `LogMode` appears more than once in the
        `[Settings]` section:

        `Setting 'LogMode' has an invalid value. Default value 'Default' will be used.`

    -   When changed settings are successfully saved during shutdown:

        `Settings were saved.`

    -   When settings that require saving cannot be saved during
        shutdown:

        `Settings could not be saved.`

29. Shutdown comparison MUST NOT load the persistent file into the
    active in-memory settings object. Its purpose is only to determine
    whether the persistent state is equivalent to the current in-memory
    state.

30. No new third-party dependency is required for this specification.

# Acceptance Criteria

1.  On first startup without `settings.ini`, the application creates:

    `Documents\Lord Simulator\settings.ini`

2.  The newly created file contains the `[Settings]` section and the
    complete persistent settings state, including:

    ``` ini
    [Settings]
    LogMode=Default
    ```

3.  `[Settings]` and a section-header line with leading or trailing
    whitespace such as `[Settings]` are recognized as the Lord Simulator
    settings section.

4.  `[settings]`, `[SETTINGS]`, and `[ Settings ]` are not recognized as
    the Lord Simulator settings section.

5.  A valid `LogMode=Default` in the `[Settings]` section is loaded and
    the logging framework operates in `Default` mode.

6.  A valid `LogMode=Development` in the `[Settings]` section is loaded
    and the logging framework operates in `Development` mode.

7.  Setting keys and values are case-sensitive, while leading and
    trailing whitespace surrounding keys and values is ignored.

8.  Blank lines and lines beginning with `;` or `#` do not prevent valid
    settings from being read.

9.  `LogMode` outside the exact `[Settings]` section does not satisfy
    the required `LogMode` setting.

10. A missing `LogMode` in the exact `[Settings]` section results in
    `Default` being used and the required missing-setting log entry
    being written.

11. An invalid `LogMode` results in `Default` being used and the
    required invalid-setting log entry being written.

12. Multiple `LogMode` entries in the `[Settings]` section are treated
    as invalid, result in `Default` being used, and produce the required
    invalid-setting log entry.

13. An unreadable settings file results in the complete settings state
    using defined defaults and the required read-failure log entry being
    written.

14. Settings loading writes `Settings loading started.` before reading
    the settings and writes `Settings loading completed.` after the
    loaded `LogMode` has been applied.

15. During normal shutdown, an unchanged persistent settings state is
    not rewritten.

16. During normal shutdown, a persistent settings state that differs
    from the in-memory settings state is overwritten with the complete
    in-memory settings state and `Settings were saved.` is logged.

17. A missing, unreadable, incomplete, duplicate, invalid, or
    incorrectly cased/formed settings section during shutdown is treated
    as different and causes the system to attempt to write the complete
    in-memory settings state.

18. If a required shutdown save fails, `Settings could not be saved.` is
    logged and application shutdown continues.

19. Settings persistence completes before the Lord Simulator logging
    framework is shut down.

20. All settings-related log entries required by this specification use
    `Default` mode and exactly match the messages defined in the
    Requirements.
