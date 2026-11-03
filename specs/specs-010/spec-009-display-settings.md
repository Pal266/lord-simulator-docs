# Title

Display Resolution and Fullscreen Settings

# Type

feature

# Description

Extend the existing Lord Simulator settings configuration with three new entries controlling the application's startup display mode:

* `Width`
* `Height`
* `Fullscreen`

`Width` and `Height` allow either an explicit numeric resolution or the value `auto`. Automatic resolution detection is valid only when both values are `auto`.

`Fullscreen` determines whether the application starts in fullscreen or windowed mode.

The application must validate the configured display settings before applying them and fall back to safe defaults when the configured resolution cannot be used.

# Requirements

## Settings entries

1. Add the following three entries to the existing Lord Simulator settings file:

    * `Width`
    * `Height`
    * `Fullscreen`

2. The default values MUST be:

    * `Width=auto`
    * `Height=auto`
    * `Fullscreen=1`

3. `Width` and `Height` MUST each accept:

    * the exact value `auto`; or
    * a positive integer representing the requested resolution dimension in pixels.

4. `Fullscreen` MUST accept:

    * `1` — start in fullscreen mode;
    * `0` — start in windowed mode.

## Automatic resolution

5. Automatic resolution detection MUST be used only when both settings are:

    * `Width=auto`
    * `Height=auto`

6. When both values are `auto`, the application MUST detect the current screen resolution at startup.

7. The detected screen width and height MUST be used as the application resolution.

8. Automatic detection MUST use the screen/display on which Lord Simulator is starting according to the platform/Unreal display information available during startup.

## Explicit resolution

9. When both `Width` and `Height` contain valid positive integers, the application MUST attempt to use the configured resolution.

10. Example:

    * `Width=1920`
    * `Height=1080`

    requests a resolution of `1920x1080`.

## Mixed `auto` and numeric configuration

11. A configuration where exactly one dimension is `auto` and the other dimension is numeric MUST be treated as invalid.

12. Examples of invalid mixed configurations include:

    * `Width=auto`, `Height=1080`;
    * `Width=1920`, `Height=auto`.

13. An invalid mixed configuration MUST NOT attempt to infer, calculate, or preserve the missing dimension.

14. Instead, the application MUST fall back to the default resolution behavior:

    * treat both dimensions as `auto`;
    * detect the current screen resolution;
    * use the detected resolution.

## Invalid values

15. A `Width` or `Height` value that is neither `auto` nor a valid positive integer MUST be treated as invalid.

16. Zero and negative numeric dimensions MUST be treated as invalid.

17. If either resolution dimension is invalid, the complete configured resolution MUST be rejected and the application MUST fall back to the default `auto`/`auto` resolution behavior.

18. A `Fullscreen` value other than `0` or `1` MUST be treated as invalid.

19. An invalid `Fullscreen` value MUST fall back to its default value:

    `Fullscreen=1`

## Applying display mode

20. When `Fullscreen=1`, the resolved width and height MUST be applied in fullscreen mode.

21. When `Fullscreen=0`, the resolved width and height MUST be applied in windowed mode.

22. Resolution and fullscreen configuration MUST be applied early enough during application startup that the player does not need to change display mode manually after reaching the main menu.

## Unsafe or unusable resolutions

23. The application MUST validate an explicitly configured numeric resolution as far as reasonably possible before applying it.

24. If Unreal or the operating system reports that the requested resolution/display configuration cannot be used safely, the application MUST NOT intentionally continue applying a configuration known to be unusable.

25. In such a case, the application MUST fall back to the default resolution behavior:

    * resolve the current screen resolution as if `Width=auto` and `Height=auto`;
    * preserve the valid configured `Fullscreen` value.

26. If applying a configured resolution fails in a recoverable way, the application MUST attempt the same fallback described in requirement 25.

27. The implementation MUST NOT intentionally terminate or crash the application merely because the settings file contains an invalid, unsupported, or unusable display resolution.

## Logging

28. When a configured resolution is rejected because it is malformed, invalid, unsupported, unusable, or fails during a recoverable application attempt, write an appropriate entry to the existing Lord Simulator logging system.

29. The log entry SHOULD include, when available:

    * configured `Width`;
    * configured `Height`;
    * configured `Fullscreen`;
    * the reason the configuration was rejected;
    * the fallback resolution being used.

30. If a failure occurs below the point where Lord Simulator can safely create its own log entry, use the existing Unreal/platform logging or crash-reporting facilities where available rather than introducing a new crash-handling subsystem.

31. Do not introduce a new Lord Simulator project log entry or separate display-settings log file as part of this specification.

## Settings-file compatibility

32. Existing settings entries and their behavior MUST remain unchanged.

33. If an existing settings file does not contain `Width`, use:

    `Width=auto`

34. If an existing settings file does not contain `Height`, use:

    `Height=auto`

35. If an existing settings file does not contain `Fullscreen`, use:

    `Fullscreen=1`

36. Missing display settings MUST therefore produce the same effective behavior as a settings file explicitly containing all three default values.

## Standards update

37. Update `PROJECT_STANDARD.md` before this specification is considered complete.

38. `PROJECT_STANDARD.md` MUST document the three resulting display settings, their accepted values, defaults, fallback behavior, and `auto`/`auto` rule.

39. Review `SPEC_STANDARD.md`, `IMPLEMENTATION_STANDARD.md`, and `VISUAL_STANDARD.md` for statements made inaccurate by this change.

40. If another standard becomes inaccurate because of this implementation, update that standard as part of this specification.

41. If those standards remain accurate, leave them unchanged.

## Scope boundaries

42. Do not add a graphical settings screen as part of this specification.

43. Do not enable the existing disabled `SETTINGS` main-menu button.

44. Do not add runtime resolution controls, resolution dropdowns, fullscreen controls, or other display-related UI.

45. Do not add borderless-windowed or additional display modes.

46. Do not introduce a new settings-file format or replace the existing settings infrastructure.

47. Do not modify unrelated settings behavior.

## Verification and tests

48. Add or update deterministic automated coverage sufficient to verify at minimum:

    * missing `Width` resolves to its default;
    * missing `Height` resolves to its default;
    * missing `Fullscreen` resolves to its default;
    * `auto`/`auto` invokes automatic screen-resolution behavior;
    * numeric/numeric produces the requested explicit resolution;
    * `auto`/numeric falls back to automatic resolution;
    * numeric/`auto` falls back to automatic resolution;
    * malformed width falls back to automatic resolution;
    * malformed height falls back to automatic resolution;
    * zero or negative dimensions fall back to automatic resolution;
    * `Fullscreen=1` resolves to fullscreen;
    * `Fullscreen=0` resolves to windowed mode;
    * an invalid fullscreen value resolves to fullscreen;
    * rejection of an invalid resolution does not intentionally terminate the application.

49. Where deterministic automation cannot reliably reproduce physical monitor resolution or operating-system display failures, isolate the resolution-detection/application boundary sufficiently to test the configuration and fallback logic deterministically.

50. Existing Lord Simulator automation tests MUST continue to pass.

51. Build and verify the standard `LordSimulatorEditor` Win64 Development target.

52. Build/package the standard Win64 Shipping game.

53. Verify the packaged build with the default configuration and confirm that:

    * the current screen resolution is detected;
    * the application uses that resolution;
    * the application starts fullscreen.

54. Verify the packaged build with a valid explicit numeric resolution in fullscreen mode.

55. Verify the packaged build with a valid explicit numeric resolution in windowed mode.

56. Verify at least one mixed `auto`/numeric configuration and confirm that the application falls back to automatic screen resolution.

57. Verify at least one invalid numeric resolution configuration and confirm that the application remains operational and uses the defined fallback behavior.

# Acceptance Criteria

1. The existing Lord Simulator settings configuration supports `Width`, `Height`, and `Fullscreen`.

2. Their defaults are exactly:

    * `Width=auto`;
    * `Height=auto`;
    * `Fullscreen=1`.

3. `auto` resolution detection is used only when both `Width` and `Height` are `auto`.

4. `auto`/`auto` resolves to the current screen resolution.

5. Valid numeric/numeric values request the explicitly configured resolution.

6. A mixed `auto`/numeric configuration is rejected and falls back to automatic screen resolution.

7. Invalid, zero, or negative resolution values are rejected and fall back to automatic screen resolution.

8. `Fullscreen=1` starts the application fullscreen.

9. `Fullscreen=0` starts the application windowed.

10. Invalid `Fullscreen` values fall back to fullscreen.

11. Missing display settings use their defined defaults.

12. Unsupported or otherwise unusable explicitly configured resolutions fall back safely when the failure can be detected or recovered from.

13. Rejected display configurations are logged through the existing logging facilities whenever logging is technically possible.

14. Invalid display settings do not intentionally cause application termination or a crash.

15. No graphical settings UI, new display mode, new settings infrastructure, or unrelated settings behavior is introduced.

16. Existing settings behavior and existing Lord Simulator functionality remain unchanged except for the display configuration introduced by this specification.

17. Required automated coverage passes and all previously existing Lord Simulator automation tests continue to pass.

18. The standard `LordSimulatorEditor` Win64 Development build succeeds.

19. The standard Win64 Shipping packaged build succeeds and respects the configured resolution and fullscreen behavior.

20. `PROJECT_STANDARD.md` is updated to document the resulting display-settings contract, and any other standard made inaccurate by the implementation is updated.
