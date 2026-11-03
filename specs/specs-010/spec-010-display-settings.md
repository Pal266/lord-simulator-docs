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

The application must validate configured display settings before applying them where technically possible and fall back to automatic screen resolution when the configured resolution is invalid or cannot be safely applied.

# Requirements

## Settings entries

1. Add the following three entries to the canonical Lord Simulator settings object and persistent settings file:

    * `Width`
    * `Height`
    * `Fullscreen`

2. The default values MUST be exactly:

    * `Width=auto`
    * `Height=auto`
    * `Fullscreen=1`

3. `Width` and `Height` MUST each accept:

    * the exact value `auto`; or
    * a positive integer representing the requested resolution dimension in pixels.

4. `Fullscreen` MUST accept:

    * `1` — fullscreen mode;
    * `0` — windowed mode.

5. The new settings MUST participate in the existing complete in-memory and persistent settings state using the canonical Lord Simulator settings framework.

6. Do not create a separate display-settings persistence mechanism, settings file, reload path, save lifecycle, or independent settings state.

## Automatic resolution

7. Automatic resolution detection MUST be used when both settings resolve to:

    * `Width=auto`
    * `Height=auto`

8. When both values are `auto`, the application MUST detect the current screen resolution during startup.

9. The detected screen width and height MUST become the resolved application resolution.

10. Automatic resolution detection MUST use the screen/display information provided by the existing Unreal Engine/platform facilities available during Lord Simulator startup.

11. The implementation MUST NOT use a hard-coded resolution as the normal result of `Width=auto` and `Height=auto`.

## Explicit resolution

12. When both `Width` and `Height` contain valid positive integers, the application MUST treat them as an explicit requested resolution.

13. For example:

    * `Width=1920`
    * `Height=1080`

    requests a resolution of exactly `1920x1080`.

14. The explicit configured resolution MUST be validated as far as technically possible before it is applied.

## Mixed `auto` and numeric configuration

15. A configuration where exactly one dimension is `auto` and the other dimension is numeric MUST be treated as an invalid resolution configuration.

16. Examples include:

    * `Width=auto`, `Height=1080`;
    * `Width=1920`, `Height=auto`.

17. The application MUST NOT infer, calculate, preserve, or otherwise derive the missing dimension.

18. The complete configured resolution MUST instead be rejected.

19. After rejection, resolution MUST fall back to the default resolution behavior:

    * resolve both dimensions as `auto`;
    * detect the current screen resolution;
    * use that detected resolution.

20. A valid configured `Fullscreen` value MUST remain effective when resolution falls back.

## Invalid resolution values

21. A `Width` or `Height` value that is neither the exact value `auto` nor a valid positive integer MUST be treated as invalid.

22. Zero and negative numeric dimensions MUST be treated as invalid.

23. If either resolution dimension is invalid, the complete configured resolution MUST be rejected.

24. Rejection of an invalid resolution MUST fall back to the same automatic resolution behavior defined for `Width=auto` and `Height=auto`.

25. A valid configured `Fullscreen` value MUST remain effective when resolution falls back.

## Fullscreen validation

26. `Fullscreen=1` MUST resolve to fullscreen mode.

27. `Fullscreen=0` MUST resolve to windowed mode.

28. Any `Fullscreen` value other than `0` or `1` MUST be treated as invalid.

29. An invalid `Fullscreen` value MUST fall back to the default:

    `Fullscreen=1`

30. An invalid `Fullscreen` value MUST NOT invalidate an otherwise valid resolution configuration.

## Applying display configuration

31. When the resolved fullscreen value is `1`, the resolved width and height MUST be applied in fullscreen mode.

32. When the resolved fullscreen value is `0`, the resolved width and height MUST be applied in windowed mode.

33. Resolution and fullscreen configuration MUST be resolved and applied during the existing Lord Simulator startup lifecycle.

34. The display configuration MUST be applied early enough that the application reaches the main menu using the resolved display mode without requiring player interaction.

35. The implementation MUST preserve the existing canonical startup lifecycle and MUST NOT introduce a new global startup phase solely for display configuration.

## Unavailable or unusable explicit resolutions

36. The application MUST validate an explicitly configured numeric resolution as far as technically possible using existing Unreal Engine/platform facilities before applying it.

37. If an explicitly configured numeric resolution is determined to be unavailable or unusable before application, the complete configured resolution MUST be rejected.

38. If application of an explicitly configured numeric resolution reports a recoverable failure, the configured resolution MUST be rejected.

39. In either case, the application MUST attempt to fall back to:

    * automatic current-screen resolution detection;
    * the detected width and height;
    * the already resolved `Fullscreen` value.

40. The application MUST NOT intentionally terminate or crash merely because the settings file contains an invalid, unsupported, or unavailable display resolution.

41. This specification does not require the implementation to guarantee recovery from an operating-system, graphics-driver, Unreal Engine, or other lower-level failure that terminates the process before Lord Simulator can execute fallback logic.

## Logging

42. Add one new Lord Simulator project log entry for rejection of a configured resolution.

43. The logging mode MUST be exactly:

    `Default`

44. The exact English log message MUST be:

    `Configured display resolution '{Width}x{Height}' is invalid or unavailable. Falling back to automatic screen resolution.`

45. `{Width}` MUST be replaced at runtime with the raw configured `Width` value that participated in the rejected resolution configuration.

46. `{Height}` MUST be replaced at runtime with the raw configured `Height` value that participated in the rejected resolution configuration.

47. The log entry MUST be written exactly once for each startup resolution configuration that is rejected because:

    * exactly one of `Width` or `Height` is `auto`;
    * `Width` is malformed;
    * `Height` is malformed;
    * either numeric dimension is zero or negative;
    * an explicitly configured numeric resolution is determined to be unavailable or unusable before application;
    * applying an explicitly configured numeric resolution reports a recoverable failure.

48. The log entry MUST NOT be written when:

    * both `Width` and `Height` are valid `auto`;
    * both dimensions are valid positive integers and the requested resolution is accepted;
    * only `Fullscreen` is invalid;
    * a display-related failure occurs before the Lord Simulator project logging framework is available;
    * the process terminates before Lord Simulator can execute the logging operation.

49. The log entry MUST use the existing Lord Simulator project logging framework and its existing formatting, lifecycle, and file behavior.

50. Do not create a separate display-settings log file, logging framework, crash-reporting subsystem, or parallel logging mechanism.

51. General Unreal Engine/platform logging and crash reporting MAY continue to operate according to their existing behavior, but MUST NOT be substituted for the required Lord Simulator project log when the application is able to execute requirement 42.

## Missing settings and backward compatibility

52. Existing settings entries and their behavior MUST remain unchanged except where necessary to integrate the three new settings into the canonical complete settings state.

53. If an existing settings file does not contain `Width`, its loaded value MUST use the default:

    `Width=auto`

54. If an existing settings file does not contain `Height`, its loaded value MUST use the default:

    `Height=auto`

55. If an existing settings file does not contain `Fullscreen`, its loaded value MUST use the default:

    `Fullscreen=1`

56. A settings file missing all three entries MUST therefore have the same effective display configuration as:

    * `Width=auto`
    * `Height=auto`
    * `Fullscreen=1`

57. Existing settings-file loading, validation, comparison, and persistence behavior MUST remain consistent with the canonical settings framework.

## Standards update

58. Update `PROJECT_STANDARD.md` before this specification is considered complete.

59. `PROJECT_STANDARD.md` MUST document `Width`, including:

    * accepted values;
    * default value;
    * numeric validation;
    * `auto` behavior.

60. `PROJECT_STANDARD.md` MUST document `Height`, including:

    * accepted values;
    * default value;
    * numeric validation;
    * `auto` behavior.

61. `PROJECT_STANDARD.md` MUST document `Fullscreen`, including:

    * accepted values;
    * default value;
    * fullscreen/windowed meaning;
    * invalid-value fallback.

62. `PROJECT_STANDARD.md` MUST document that automatic resolution is valid only when both dimensions are `auto`.

63. `PROJECT_STANDARD.md` MUST document that a mixed `auto`/numeric pair is invalid and falls back to automatic current-screen resolution.

64. `PROJECT_STANDARD.md` MUST document that an invalid, unavailable, or recoverably failed explicit resolution falls back to automatic current-screen resolution while preserving the resolved fullscreen value.

65. `PROJECT_STANDARD.md` MUST document the new `Default`-mode project log entry and its exact English message.

66. Review `SPEC_STANDARD.md`, `IMPLEMENTATION_STANDARD.md`, and `VISUAL_STANDARD.md` for statements made inaccurate by this change.

67. If another standard becomes inaccurate because of this implementation, update that standard as part of this specification so no contradiction remains between implementation and current standards.

68. If `SPEC_STANDARD.md`, `IMPLEMENTATION_STANDARD.md`, or `VISUAL_STANDARD.md` remain accurate after the change, leave them unchanged.

## Scope boundaries

69. Do not add a graphical settings screen as part of this specification.

70. Do not enable the existing disabled `SETTINGS` main-menu button.

71. Do not add runtime resolution controls, resolution dropdowns, fullscreen controls, or other display-related UI.

72. Do not add borderless-windowed mode or another display mode.

73. Do not introduce a new settings-file format.

74. Do not replace the existing Lord Simulator settings framework.

75. Do not introduce a new external dependency.

76. Do not introduce a new logging framework, display-settings log file, or crash-handling subsystem.

77. Do not modify unrelated settings behavior.

78. Do not add additional display settings beyond `Width`, `Height`, and `Fullscreen`.

## Verification and tests

79. Add or update deterministic Unreal Automation coverage sufficient to verify at minimum:

    * missing `Width` resolves to `auto`;
    * missing `Height` resolves to `auto`;
    * missing `Fullscreen` resolves to `1`;
    * `auto`/`auto` selects automatic screen-resolution behavior;
    * valid numeric/numeric values select the exact requested explicit resolution;
    * `auto`/numeric rejects the configured resolution and selects automatic resolution;
    * numeric/`auto` rejects the configured resolution and selects automatic resolution;
    * malformed `Width` rejects the configured resolution;
    * malformed `Height` rejects the configured resolution;
    * zero `Width` or `Height` rejects the configured resolution;
    * negative `Width` or `Height` rejects the configured resolution;
    * `Fullscreen=1` resolves to fullscreen;
    * `Fullscreen=0` resolves to windowed;
    * an invalid `Fullscreen` value resolves to fullscreen;
    * an invalid `Fullscreen` value does not invalidate an otherwise valid resolution;
    * rejection of a configured resolution preserves a valid resolved fullscreen value;
    * rejection of a configured resolution selects automatic resolution fallback rather than a hard-coded resolution;
    * rejection of a configured resolution produces the exact required `Default`-mode project log entry when the logging framework is available;
    * a valid accepted resolution does not produce the rejection log entry;
    * an invalid `Fullscreen` value alone does not produce the resolution-rejection log entry.

80. Where deterministic automation cannot reliably reproduce physical monitor resolution or operating-system display failures, provide an internal test seam around the environment-dependent resolution detection/application boundary sufficient to test success, rejection, and fallback logic deterministically.

81. Any test seam introduced under requirement 80 MUST comply with the existing testing requirements in `IMPLEMENTATION_STANDARD.md` and MUST NOT alter normal production behavior.

82. Existing Lord Simulator settings tests MUST continue to pass.

83. All previously existing Lord Simulator automation tests MUST continue to pass.

84. Build and verify the standard `LordSimulatorEditor` Win64 Development target.

85. Build/package the standard Win64 Shipping game.

86. Verify the packaged build with the default display configuration:

    * `Width=auto`;
    * `Height=auto`;
    * `Fullscreen=1`.

87. For requirement 86, confirm that:

    * the current screen resolution is detected;
    * the detected resolution is applied;
    * the application starts in fullscreen mode;
    * no resolution-rejection project log entry is produced.

88. Verify the packaged build with at least one valid explicit numeric resolution and `Fullscreen=1`.

89. Confirm that the requested explicit resolution is applied in fullscreen mode.

90. Verify the packaged build with at least one valid explicit numeric resolution and `Fullscreen=0`.

91. Confirm that the requested explicit resolution is applied in windowed mode.

92. Verify the packaged build with at least one mixed `auto`/numeric resolution configuration.

93. Confirm that the mixed configuration:

    * is rejected;
    * falls back to detected current-screen resolution;
    * preserves the valid configured fullscreen value;
    * produces the exact required `Default`-mode project log entry.

94. Verify the packaged build with at least one malformed, zero, or negative resolution value.

95. Confirm that the invalid configuration:

    * is rejected;
    * falls back to detected current-screen resolution;
    * does not intentionally terminate the application;
    * produces the exact required `Default`-mode project log entry.

96. Where the test environment permits deterministic simulation or reproduction of an unavailable or recoverably failed explicit resolution, verify that:

    * the requested resolution is rejected;
    * automatic screen-resolution fallback is selected;
    * the resolved fullscreen value is preserved;
    * the exact required `Default`-mode project log entry is produced.

# Acceptance Criteria

1. The canonical Lord Simulator settings state contains `Width`, `Height`, and `Fullscreen`.

2. Their defaults are exactly:

    * `Width=auto`;
    * `Height=auto`;
    * `Fullscreen=1`.

3. `Width` and `Height` accept either the exact value `auto` or a positive integer.

4. Automatic screen-resolution detection is selected when both dimensions are `auto`.

5. `auto`/`auto` resolves to the current screen resolution rather than a hard-coded resolution.

6. Valid numeric/numeric values request the exact explicitly configured resolution.

7. A mixed `auto`/numeric configuration is rejected and falls back to automatic current-screen resolution.

8. Malformed, zero, or negative resolution dimensions cause the complete configured resolution to be rejected and fall back to automatic current-screen resolution.

9. `Fullscreen=1` resolves to fullscreen mode.

10. `Fullscreen=0` resolves to windowed mode.

11. An invalid `Fullscreen` value falls back to `Fullscreen=1` without invalidating an otherwise valid resolution.

12. A valid resolved fullscreen value is preserved when resolution fallback occurs.

13. Missing display settings use their explicitly defined defaults.

14. An explicit numeric resolution determined to be unavailable or unusable is rejected where that condition can be detected.

15. A recoverable explicit-resolution application failure triggers automatic current-screen resolution fallback.

16. Invalid or unavailable display resolution configuration does not intentionally terminate or crash the application.

17. Every configured-resolution rejection for which Lord Simulator can execute project logging produces exactly one `Default`-mode project log entry with the exact message:

    `Configured display resolution '{Width}x{Height}' is invalid or unavailable. Falling back to automatic screen resolution.`

18. Valid accepted resolutions and fullscreen-only validation failures do not produce the resolution-rejection project log entry.

19. The three settings participate in the existing complete Lord Simulator settings state and persistence lifecycle.

20. No graphical settings UI, new display mode, new settings framework, new settings file format, external dependency, new logging framework, or crash-handling subsystem is introduced.

21. Existing settings behavior and functionality outside this specification remain unchanged.

22. Required automated coverage passes and all previously existing Lord Simulator automation tests continue to pass.

23. The standard `LordSimulatorEditor` Win64 Development build succeeds.

24. The standard Win64 Shipping packaged build succeeds and respects the resolved resolution and fullscreen configuration.

25. `PROJECT_STANDARD.md` is updated to define the resulting display-settings behavior and new project log entry.

26. Any other standard made inaccurate by this implementation is updated, while unaffected standards remain unchanged.
