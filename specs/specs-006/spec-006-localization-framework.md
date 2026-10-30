# Title

Localization Framework

# Type

feature

# Description

Establish the Lord Simulator localization framework using Unreal Engine
5.8 localization facilities.

The framework provides one application-wide source of truth for
localization policy and language state while Unreal Engine remains
responsible for localized text resolution through `FText`, String
Tables, culture handling, and compiled localization resources.

The project uses a canonical Unreal Localization Target named
`LordSimulator` and a canonical Unreal String Table with String Table ID
`LordSimulator`. These are distinct Unreal localization concepts that
intentionally share the same canonical project identifier. The canonical
String Table asset is located at `/Game/Localization/ST_LordSimulator`.

English (`en`) is the native/source culture, authoritative fallback
culture, and default configured language. Initially, `en` is the only
supported culture.

The persistent `Language` setting determines both the Unreal language
and locale. The framework distinguishes the configured language stored
in settings from the language successfully active during the current
runtime session. Active language may be unavailable when no culture has
been successfully applied during the session.

This specification establishes localization infrastructure and automated
localization tests. It does not introduce placeholder user-facing
localization entries, additional production-supported cultures, a
language-selection UI, custom translation lookup, Blueprint localization
APIs, or runtime localization-resource reloading.

# Requirements

## Localization infrastructure

1.  Use Unreal Engine 5.8 localization facilities. Do not implement a
    custom translation parser, custom localization file format, custom
    translation lookup system, or parallel translation engine.

2.  Configure one canonical Unreal Localization Target named exactly
    `LordSimulator`.

3.  Configure the `LordSimulator` Localization Target with:

    -   native/source culture `en`;
    -   initial supported cultures containing only `en`;
    -   Game loading policy;
    -   standard Unreal localization configuration and generated
        localization resources.

4. Create one canonical asset-based Unreal String Table at
    `/Game/Localization/ST_LordSimulator`. References to this table must use
    the identifier Unreal assigns to the asset-based String Table; do not
    introduce a second C++-registered table or redirect merely to force a
    custom Table ID.

5.  The canonical Localization Target named `LordSimulator` and
    canonical String Table ID `LordSimulator` are distinct Unreal
    localization concepts that intentionally use the same canonical
    project identifier.

6.  The canonical String Table is the default location for future Lord
    Simulator localizable text unless a future specification explicitly
    requires another table.

7.  Do not add placeholder localization entries merely to populate or
    test the String Table.

8.  Localization resources must use Unreal Engine's standard
    localization target/resource structure and compiled localization
    resources. Do not introduce a separate Lord Simulator
    translation-resource format.

9.  `en` is a required localization invariant. Successful localization
    initialization requires the native culture to be `en` and `en` to be
    a Lord Simulator-supported culture.

## Supported cultures and metadata

10. Lord Simulator's explicit Unreal project localization configuration is
    the authoritative source of cultures supported by the application. The
    supported-culture set must be stored in Unreal project configuration in a
    runtime-readable form usable by the Lord Simulator localization framework
    and the project's localization/build workflow.

11. The implementation must not derive Lord Simulator-supported cultures from
    `.locmeta`, `.locres` discovery, installed operating-system cultures,
    Unreal localization-resource discovery, String Table contents, or a
    separate hard-coded C++ culture registry. A culture having localization
    resources discoverable by Unreal does not by itself make that culture Lord
    Simulator-supported.

12. Supported cultures are read-only runtime configuration. The canonical
    `LordSimulator` Localization Target/resources must be consistent with the
    authoritative supported-culture project configuration. Every configured
    supported culture must be represented by the target as required by Unreal's
    localization workflow, and the target must not define an additional Lord
    Simulator-supported culture outside the authoritative configuration. A
    structural mismatch is a localization initialization failure.

13. Supported-culture identifiers and `Language` values are validated by
    Lord Simulator using exact, case-sensitive matching against cultures
    explicitly configured as supported. Lord Simulator must not
    normalize, truncate, case-convert, automatically map, or use
    parent-culture matching to convert an unsupported requested
    identifier into a supported `Language` value.

14. Regional or otherwise specific Unreal culture identifiers are
    permitted when explicitly configured as supported. For Lord
    Simulator supported-language validation, `pt-BR` and `pt` are
    distinct values; supporting one does not make the other a supported
    `Language` value.

15. The exact-match policy applies to Lord Simulator supported-culture
    validation and configured language state. It must not disable,
    replace, or interfere with Unreal Engine's normal
    localization-resource resolution and fallback behavior after a
    supported culture has been selected.

16. Expose all Lord Simulator-supported cultures without duplicates.

17. Obtain each supported culture's native display name from Unreal
    Engine internationalization/culture facilities. Do not maintain a
    separate project-owned culture-display-name translation table.

18. Initially the supported-language metadata is:

-   culture identifier: `en`;
-   native display name expected from Unreal: `English`.

19. If required supported-culture information cannot be reliably
    discovered during initialization, supported-culture discovery is
    considered failed. Do not substitute a hard-coded supported-culture
    list.

## Application-wide localization state

20. Maintain one authoritative application-wide Lord Simulator
    localization state.

21. The localization framework must expose, without requiring exact C++
    class or function names:

-   supported languages and their native display names;
-   configured language;
-   active language, including an unambiguous indication when no
    language is successfully active;
-   validation of whether a culture is supported;
-   an application-wide language-change operation;
-   unambiguous success/failure from a language-change request.

22. Supported-language entries contain stable culture metadata only.
    Configured/active flags must not be stored as duplicate mutable
    state inside each supported-language entry.

23. Configured language means the `Language` value in the complete
    in-memory settings object.

24. Active language represents the culture successfully applied by the
    Lord Simulator localization framework for the current runtime
    session. Active language may be unavailable when no culture has been
    successfully applied by the framework during the current session.

25. When no language is successfully active, the framework must
    represent active language as unavailable state rather than using a
    synthetic culture identifier such as `none`, `unknown`, `invalid`,
    or `unavailable`.

26. Active language is runtime-only state and must not be persisted.

27. The localization framework manages language policy and culture state
    only. Actual localized text lookup/resolution must use Unreal Engine
    `FText` and the canonical String Table/localization resources
    directly. Do not add a Lord Simulator translation-lookup API.

28. Do not require Blueprint-callable localization APIs in this
    specification.

## Language setting and settings integration

29. Add a persistent setting named exactly `Language`.

30. `Language` is case-sensitive.

31. The default `Language` value is exactly `en`.

32. `Language` is the only localization-related player setting
    introduced by this specification. Do not add separate
    native-language, fallback-language, or locale settings.

33. A `Language` value is valid when:

-   it is exactly `en`; or
-   supported-culture discovery succeeded and the value exactly matches
    a culture explicitly configured as supported by Lord Simulator.

34. If supported-culture discovery fails, `en` remains valid because it
    is the fixed native/default invariant. Any other `Language` value
    cannot be verified as supported and is invalid.

35. If localization initialization fails after supported-culture
    discovery succeeded, discovered supported cultures remain valid
    configuration values even though they cannot be applied during that
    session.

36. If `Language` is missing while loading settings:

-   use `en` in the complete in-memory settings object;
-   log in Default mode exactly:
    `Setting 'Language' is missing. Default value 'en' will be used.`

37. If `Language` has an invalid value while loading settings:

-   use `en` in the complete in-memory settings object;
-   log in Default mode exactly:
    `Setting 'Language' has an invalid value. Default value 'en' will be used.`

38. `Language` must participate in the existing complete settings state
    in the same manner as other persistent settings. The required
    integration contract is:

-   persistent settings are loaded as one complete settings state rather
    than loading `Language` independently;
-   duplicate `Language` entries are handled by the existing settings
    framework's duplicate-setting behavior;
-   a missing or invalid `Language` value is replaced in the complete
    in-memory settings state with its defined default `en`;
-   runtime changes to `Language` modify the complete in-memory settings
    state and do not independently reload settings from persistent
    storage;
-   saving settings writes the complete persistent settings state,
    including `Language` even when its value is `en`;
-   settings are compared using the existing complete-state comparison
    behavior used to determine whether persistence is required;
-   do not introduce a separate localization settings file, independent
    `Language` persistence mechanism, or special immediate-save path.

39. The localization framework must not independently read `Language`
    from `settings.ini`. Startup language application must consume the
    validated/defaulted `Language` value from the complete in-memory
    settings object.

40. The localization framework must not independently persist
    `Language`. A successful runtime language change updates `Language`
    through the complete in-memory settings state, and the existing
    settings persistence lifecycle is responsible for writing it.

41. Missing or invalid persisted `Language` state is repaired by the
    normal complete-settings shutdown comparison/save behavior. Do not
    introduce a special immediate write.

42. Do not automatically select the operating-system language. On a
    fresh installation the configured language is `en` regardless of
    Windows language.

43. Before persisted `Language` is applied, Lord Simulator game
    execution must use `en` as the baseline Unreal language and locale,
    independent of the operating-system culture. If localization
    initialization or startup language application cannot establish
    another active culture, the implementation must not intentionally
    fall back to the operating-system culture.

## Startup lifecycle

44. Localization initialization is a single-attempt, idempotent
    application-session lifecycle.

45. The first initialization request performs initialization. After
    successful initialization, later initialization requests are
    successful no-ops and must not recreate state, reset language state,
    or emit another initialization lifecycle log sequence.

46. If the first initialization attempt fails, the framework remains in
    the failed state for the rest of that application session. Do not
    automatically retry initialization.

47. Startup ordering must be performed in this exact sequence:

-   initialize project logging in Default mode;
-   initialize the Lord Simulator localization framework;
-   start settings loading;
-   load and validate the complete settings object, including
    `Language`;
-   apply `LogMode`;
-   if localization initialization succeeded, process configured
    `Language` as both Unreal language and locale, including the
    required native fallback behavior;
-   complete settings loading;
-   establish the resulting runtime localization state;
-   mark the localization startup phase complete;
-   continue application startup.

48. The localization startup phase completes after localization
    initialization has reached its session result, the complete settings
    state has been loaded and validated, configured `Language` has been
    processed when the localization framework is available, and the
    resulting runtime localization state---including fallback or
    unavailable active-language state---has been established.

49. Localization startup completion does not require localization
    initialization or language application to have succeeded. Failure
    states are valid completed startup states.

50. Systems that create, cache, format, or display localizable
    user-facing text must not perform localization-dependent
    initialization before the localization startup phase is complete.

51. Localization initialization or language-application failure must not
    prevent the localization startup phase from completing or
    permanently block unrelated application initialization.

52. On localization initialization start, log in Default mode exactly:
    `Localization initialization started.`

53. Successful localization initialization requires, at minimum:

-   the canonical Lord Simulator localization runtime resources required
    by the framework are available;
-   the canonical String Table asset
    `/Game/Localization/ST_LordSimulator`, registered with String Table
    ID `LordSimulator`, is available;
-   the native culture invariant is `en`;
-   `en` is supported;
-   the supported-culture project configuration can be read and contains
    no duplicates;
-   the supported-culture configuration contains native culture `en`;
-   the canonical `LordSimulator` Localization Target/resources are
    consistent with the authoritative supported-culture configuration.

54. On successful localization initialization, log in Default mode
    exactly: `Localization initialization completed.`

55. On localization initialization failure, log in Default mode exactly:
    `Localization initialization failed. Native language 'en' will be used where available.`

56. Do not log `Localization initialization completed.` when
    initialization failed.

57. If localization initialization fails:

-   continue startup and normal settings loading;
-   retain supported-culture metadata successfully discovered before the
    later failure;
-   do not attempt startup language application through the failed Lord
    Simulator localization framework;
-   do not change a valid configured `Language` solely because
    initialization failed;
-   establish the resulting runtime localization state and complete the
    localization startup phase.

58. Do not initialize or cycle through every supported culture during
    normal startup. Only the configured language and, if required by
    failure, the native `en` fallback are applied.

## Startup language application

59. Applying `Language` must set both Unreal Engine language and locale
    together using Unreal Engine's standard facilities.

60. When the configured language is successfully applied during startup:

-   set active language to that culture;
-   retain the same configured language;
-   log in Default mode exactly: `Language '<culture>' was applied.`

61. If a valid configured language other than `en` cannot be applied
    during startup:

-   retain configured `Language`;
-   explicitly attempt to apply native `en` as both Unreal language and
    locale;
-   do not replace or persist configured `Language` as `en`.

62. If the `en` fallback in requirement 61 succeeds:

-   active language becomes `en`;
-   log in Default mode exactly:
    `Language '<culture>' could not be applied. Native language 'en' will be used for the current session.`
-   do not emit an additional fallback-success Lord Simulator log.

63. If the configured language is `en` and cannot be applied, do not
    attempt `en` a second time as fallback.

64. If configured `en` cannot be applied, or a non-native configured
    language fails and the subsequent `en` fallback also fails:

-   retain configured `Language`;
-   active language is unavailable;
-   continue startup;
-   log in Default mode exactly:
    `Language '<culture>' could not be applied and native language 'en' could not be activated. Localization is unavailable for the current session.`

65. Only one startup language-application failure message from
    requirements 62 or 64 is emitted for a failed configured-language
    application.

66. A valid startup language-application failure is a runtime/resource
    failure, not an invalid-setting condition.

## Runtime language changes

67. Normal runtime feature code, including C++ and Blueprints, must not
    directly modify the in-memory `Language` setting or Unreal Engine's
    active language/locale independently. Runtime application-wide
    language changes must go through the Lord Simulator localization
    framework.

68. A runtime language-change request must validate the requested
    culture against Lord Simulator-supported cultures before attempting
    to apply it.

69. If localization framework initialization failed, any runtime
    language-change request:

-   is rejected;
-   does not attempt an Unreal culture change through the Lord Simulator
    framework;
-   leaves configured and active state unchanged;
-   returns failure;
-   uses the applicable runtime application-failure log from
    requirements 74 or None.

70. Successful framework initialization followed by failure to establish
    an active language does not disable later runtime language-change
    requests. A later supported request may attempt application
    normally.

71. If a runtime request uses an unsupported culture:

-   do not call Unreal to apply it;
-   do not change configured or active language;
-   return failure;
-   if an active language exists, log exactly:
    `Language '<requested>' is not supported. Language '<active>' will remain active.`
-   if active language is unavailable, log exactly:
    `Language '<requested>' is not supported. No language is currently active.`

72. If the requested runtime language is already both configured and
    active:

-   treat the request as a successful no-op;
-   return success;
-   do not call Unreal unnecessarily;
-   do not perform a custom UI refresh;
-   do not emit a localization log.

73. For a supported runtime language change that is not the no-op case:

-   attempt to apply the requested culture as both Unreal language and
    locale;
-   only after successful application update configured `Language`
    through the complete in-memory settings state;
-   set active language to the successfully applied culture;
-   rely on Unreal Engine's standard localization-aware `FText`
    behavior;
-   return success;
-   log in Default mode exactly: `Language '<culture>' was applied.`

74. If a supported runtime language change cannot be applied while an
    active language exists:

-   retain previous configured and active language;
-   do not persist the failed requested language;
-   return failure;
-   log in Default mode exactly:
    `Language '<requested>' could not be applied. Language '<active>' will remain active.`

75. If a supported runtime language change cannot be applied while
    active language is unavailable:

-   retain previous configured language;
-   keep active language unavailable;
-   do not persist the failed requested language;
-   return failure;
-   log in Default mode exactly:
    `Language '<requested>' could not be applied. No language is currently active.`

76. A successful runtime language change from an
    unavailable-active-language state sets the requested culture as both
    configured and active language and follows the normal persistence
    lifecycle.

77. A successful runtime language change modifies the complete in-memory
    settings object but does not immediately write `settings.ini`.
    Normal shutdown comparison/save behavior persists the change.

78. Runtime language changes require no application restart, mandatory
    confirmation dialog, pending-language state, or
    localization-framework-level Apply operation.

79. A successful runtime language change must rely on Unreal Engine's
    standard localization-aware `FText` behavior. The localization
    framework must not introduce a custom Lord Simulator UI-refresh or
    localization-change event system to compensate for UI that does not
    preserve localization-aware text behavior.

## Localization fallback and content behavior

80. Native English (`en`) is the authoritative source/fallback culture.

81. A supported non-native culture is not required to have 100%
    translation coverage unless a future specification explicitly
    requires a coverage level or particular translations.

82. Missing translations in a supported non-native culture must rely on
    Unreal Engine's native/source fallback behavior.

83. Every future Lord Simulator localization entry must have native
    English source text as required by the project standards.

84. Do not manufacture runtime text when the underlying localization
    entry/source/reference is missing.

85. Do not substitute localization keys themselves as player-facing
    fallback text.

86. Do not add project logging for every localization lookup or normal
    missing-translation fallback.

87. Project logs and developer diagnostics remain non-localized and must
    not change with the active game language.

## Localization content and key policy

88. Future localizable Lord Simulator text uses the canonical String
    Table ID `LordSimulator` unless explicitly required otherwise.

89. Localization keys are semantic, hierarchical, case-sensitive
    PascalCase segments separated by periods, for example:

-   `MainMenu.NewGame`
-   `Settings.Language`
-   `Building.Farm.Description`

90. Localization keys identify semantic purpose/context rather than
    current English wording, widget classes, source files, or UI
    positions.

91. Localization keys must be unique within the canonical Lord Simulator
    localization resources.

92. An existing key may be reused only for the same semantic
    text/meaning.

93. Existing localization keys must not be renamed, removed, or
    repurposed unless explicitly required by a future specification.

94. Changing native English wording while preserving semantic meaning
    does not by itself require a new key.

95. Feature implementations must not invent localization keys, native
    English source text, translations, tooltips, accessibility text, or
    other user-facing localization content omitted from the implementing
    specification.

96. Dynamic localized user-facing text and culture-sensitive values must
    use Unreal Engine localization-aware `FText` formatting facilities
    rather than runtime-generated keys or English-specific string
    concatenation/formatting.

## Editor behavior and startup timing

97. In packaged or standalone game execution, Lord Simulator controls
    the game's language and locale according to this specification. In
    Unreal Editor workflows, Lord Simulator localization behavior must
    not change the Unreal Editor application's own language or locale.
    PIE/editor validation must use Unreal-supported game-localization
    preview/testing facilities or another Unreal-supported game-scoped
    mechanism.

98. If the module's current `StartupModule()` timing is too early to
    safely initialize localization resources required by this
    specification, the implementation is explicitly authorized to move
    the existing Lord Simulator startup orchestration to the earliest
    appropriate Unreal Engine lifecycle point where the required
    localization resources are safely available. The relative ordering
    required by the Startup lifecycle section must remain unchanged, and
    unrelated startup behavior must not be changed.

## Resource and packaging workflow

99. Establish the standard Unreal Engine 5.8 localization workflow for
    the `LordSimulator` Localization Target:

-   manage the target through Unreal's standard localization
    tooling/configuration;
-   gather localization source data;
-   manage translations through Unreal localization resources;
-   compile localization resources;
-   cook/package required resources for Windows Shipping.

100. Do not add custom localization build scripts, a custom translation
     compiler, or custom command-line localization automation in this
     specification.

101. Localization data/resources must remain editable through the Unreal
     localization workflow without requiring C++ source changes merely
     to change translation wording.

102. Windows Shipping builds must include Lord Simulator localization
     resources, the canonical String Table asset, and internationalization data
     required by native `en` and every culture explicitly configured as
     supported. Use the appropriate verified Unreal cooking/staging mechanism;
     do not require `/Game/Localization` as an always-cook directory unless
     technically necessary.

103. Do not intentionally package Lord Simulator localization resources
     for cultures not configured as supported. Unreal Engine shared
     internationalization data required internally is not prohibited.

104. Localization behavior must work in Editor/PIE and in a packaged
     Windows Shipping build where applicable.

105. The development/package validation workflow must verify every
     configured supported culture can be recognized as supported,
     provide its native display name, be activated as both Unreal
     language and locale, access required packaged localization
     resources, use native English fallback for untranslated entries,
     and return to `en` successfully.

106. Localization validation must detect
     structural/resource/configuration failures supported by Unreal's
     standard localization tooling. Incomplete translation coverage for
     a supported non-native culture is permitted unless explicitly
     prohibited by a future specification.

## Automated localization tests

107. Implement automated C++ tests for the Lord Simulator localization
     framework using Unreal Engine's built-in automation testing
     facilities. Do not introduce an external test framework or testing
     dependency.

108. Automated tests must deterministically cover, where applicable:

-   supported-culture discovery from the authoritative runtime-readable
    project configuration and absence of duplicate cultures;
-   detection of mismatch between supported-culture configuration and the
    canonical Localization Target/resources;
-   exact, case-sensitive Lord Simulator culture validation;
-   default, missing, and invalid `Language` behavior;
-   configured, active, and unavailable-active-language state;
-   successful startup language application;
-   configured non-native language failure followed by successful `en`
    fallback;
-   configured non-native language failure followed by failed `en`
    fallback;
-   failed configured `en` without a second `en` attempt;
-   initialization single-attempt/idempotent behavior;
-   successful runtime language change;
-   already-configured-and-active no-op;
-   unsupported runtime request;
-   runtime application failure with an active language and with active
    language unavailable;
-   recovery from unavailable active language through a later successful
    runtime request;
-   rejection of runtime requests after localization initialization
    failure;
-   successful runtime changes update in-memory settings without
    immediate persistence;
-   localization does not independently load or save `Language`;
-   localization startup phase completes on both success and
    localization failure;
-   exact required Lord Simulator log messages for tested paths.

109. Environment-dependent localization operations, including Unreal
     culture application, must have an internal test seam sufficient for
     automated tests to deterministically simulate required success and
     failure outcomes. The testability mechanism must not create a
     second production localization implementation, supported-culture
     registry, or fallback system. This requirement does not prescribe a
     particular C++ interface, class, mocking library, or implementation
     pattern.

110. Automated tests may create isolated, test-only in-memory
     localization or String Table fixtures when needed to validate
     localization-aware `FText` behavior across a simulated language
     change. Such fixtures must not be packaged, must not modify
     production supported-culture configuration or the canonical
     production String Table, and must not create production
     localization resources.

111. Automated tests must not add fake production-supported cultures,
     placeholder production localization entries, or production-only
     test localization resources merely to create test scenarios.

112. Automated configuration/resource tests must verify the actual
     project configuration where technically testable, including:

-   canonical Localization Target `LordSimulator`;
-   native culture `en`;
-   authoritative production supported-culture configuration initially
    containing only `en`;
-   consistency between that configuration and the canonical `LordSimulator`
    Localization Target/resources;
-   canonical String Table asset `/Game/Localization/ST_LordSimulator`;
-   no placeholder entries introduced by this specification.

113. Runtime language-change validation must use existing localization
     content when such content is available. This specification must not
     introduce placeholder user-facing localization entries solely for
     validation.

114. Automated tests do not replace Windows Shipping packaging
     verification. Cooked/package resource inclusion and actual packaged
     behavior must still be verified through the development/package
     validation workflow.

## Documentation and lifecycle constraints

115. Update the project root `README.md` with the actual Unreal Engine
     5.8 localization workflow established by the implementation.

116. README localization documentation must be sufficient for a
     developer to:

-   locate/manage the `LordSimulator` Localization Target;
-   locate the canonical String Table;
-   gather localization data;
-   compile localization resources;
-   add/manage a supported culture through the established Unreal
    workflow;
-   verify native culture `en`;
-   run the automated localization tests;
-   package required localization resources in the Windows Shipping
    build;
-   verify a supported culture in the packaged build.

117. The README is documentation only. Unreal project localization
     configuration/assets remain authoritative.

118. Do not add localization-specific shutdown lifecycle or shutdown
     logs. Unreal Engine owns the localization subsystem lifetime unless
     a future specification introduces a concrete Lord Simulator-owned
     resource requiring explicit cleanup.

119. Do not add Development-mode localization logs in this
     specification.# Acceptance Criteria

1. The project contains the canonical Unreal Localization Target
     `LordSimulator` with native culture `en`, Game loading policy, and
     only `en` initially configured as supported.

2. The project contains the canonical asset-based Unreal String Table
    `/Game/Localization/ST_LordSimulator`; no second C++-registered canonical
    table or redirect exists merely to force a custom Table ID, and no
    placeholder localization entries are introduced solely by this
    specification.

3. The implementation uses Unreal Engine localization facilities and
     contains no custom translation parser, custom localization file
     format, parallel translation lookup system, or language-specific
     translation branches.

4. A culture is Lord Simulator-supported only when explicitly
     configured as supported for the canonical `LordSimulator`
     Localization Target; merely discoverable Unreal localization
     resources do not make a culture supported.

5. Supported cultures are exposed without duplicates, cannot be
     mutated by normal runtime code, and native display names are
     obtained through Unreal culture facilities.

6. Supported-culture validation uses exact, case-sensitive Lord
     Simulator identifiers. Differently cased, parent, child, or
     otherwise non-identical identifiers are not accepted unless
     explicitly configured as supported.

7. Exact Lord Simulator supported-culture validation does not
     introduce a custom resource fallback mechanism or interfere with
     Unreal's standard localization-resource fallback after a supported
     culture is active.

8. `Language` exists as a persistent, case-sensitive setting with
     default `en`; no separate persistent locale/native/fallback
     language setting is introduced.

9. A fresh settings state results in configured `Language=en`
     regardless of Windows language.

10. Missing `Language` produces configured `en` and exactly:
     `Setting 'Language' is missing. Default value 'en' will be used.`

11. Invalid `Language` produces configured `en` and exactly:
     `Setting 'Language' has an invalid value. Default value 'en' will be used.`

12. If supported-culture discovery fails, `en` remains valid and any
     non-`en` value is invalid because support cannot be verified.

13. If localization initialization fails after supported cultures were
     discovered, those cultures remain valid configuration values and
     are not rewritten solely because initialization failed.

14. `Language` participates in the complete settings state and is not
     independently loaded from or persisted to `settings.ini` by the
     localization framework.

15. Complete settings creation/saving includes `Language`, including
     when its value is default `en`.

16. Startup language application consumes the validated/defaulted
     `Language` from the already-loaded complete in-memory settings
     object after `LogMode` is applied.

17. Localization initialization occurs after project logging
     initialization and before settings loading starts.

18. Successful initialization emits exactly
     `Localization initialization started.` and
     `Localization initialization completed.` in Default mode.

19. Failed initialization emits `Localization initialization started.`
     and
     `Localization initialization failed. Native language 'en' will be used where available.`,
     does not emit the completed log, remains failed for the session,
     and is non-fatal.

20. Re-requesting initialization after success is a successful no-op
     without duplicate lifecycle logs or state reset; re-requesting
     after failure does not retry initialization.

21. Successful startup language application sets both Unreal language
     and locale, retains configured language, sets active language to
     the requested culture, and logs exactly
     `Language '<culture>' was applied.`

22. If a valid configured non-native language cannot be applied, the
     framework explicitly attempts `en` as both language and locale.

23. If that `en` fallback succeeds, configured language remains
     unchanged, active language becomes `en`, startup continues, and
     exactly
     `Language '<culture>' could not be applied. Native language 'en' will be used for the current session.`
     is emitted without an additional fallback-success log.

24. If the configured non-native language and subsequent `en` fallback
     both fail, configured language remains unchanged, active language
     is unavailable, startup continues, and exactly
     `Language '<culture>' could not be applied and native language 'en' could not be activated. Localization is unavailable for the current session.`
     is emitted.

25. If configured `Language=en` cannot be applied, `en` is not
     attempted a second time, configured language remains `en`, active
     language is unavailable, startup continues, and the
     localization-unavailable startup log is emitted.

26. When no culture has been successfully applied during the session,
     active language is exposed as unavailable and no synthetic culture
     identifier represents that state.

27. Configured language and active language are independently queryable
     and active language is never persisted.

28. Localization startup reaches completion after the resulting runtime
     localization state is established on successful startup,
     language-application failure, and localization-initialization
     failure. Failure does not permanently block unrelated application
     initialization.

29. Localization-dependent user-facing initialization does not occur
     before the localization startup phase is complete.

30. An unsupported runtime request is rejected before Unreal culture
     application and leaves state unchanged. With an active language it
     logs
     `Language '<requested>' is not supported. Language '<active>' will remain active.`;
     with unavailable active language it logs
     `Language '<requested>' is not supported. No language is currently active.`

31. Requesting the already configured and active language returns
     success as a no-op, performs no unnecessary culture application or
     custom UI refresh, and emits no localization log.

32. A successful supported runtime language change sets both Unreal
     language and locale, updates configured and active language,
     returns success, and logs exactly
     `Language '<culture>' was applied.`

33. A successful runtime language change updates the complete in-memory
     settings state without immediately writing `settings.ini`; normal
     persistence later writes the changed value.

34. A failed supported runtime change with an active language preserves
     prior state, returns failure, does not persist the failed request,
     and logs exactly
     `Language '<requested>' could not be applied. Language '<active>' will remain active.`

35. A failed supported runtime change with active language unavailable
     preserves configured state and unavailable active state, returns
     failure, does not persist the failed request, and logs exactly
     `Language '<requested>' could not be applied. No language is currently active.`

36. After successful framework initialization but failure to establish
     an active language, a subsequent supported runtime request may
     attempt application normally; on success the requested culture
     becomes both configured and active.

37. A runtime request made after localization framework initialization
     failed is rejected without attempting culture application and
     leaves state unchanged.

38. A localization-aware validation path using `FText` can reflect a
     successful runtime language change without application restart and
     without a custom Lord Simulator UI-refresh or localization-change
     event system.

39. Runtime language-change validation does not introduce placeholder
     production localization content solely for validation.

40. Project logs remain English/non-localized when active game language
     changes.

41. Missing non-native translations use Unreal's native/source
     fallback; no custom fallback dictionary, duplicated hard-coded UI
     fallback, or key-as-player-facing-text substitution is introduced.

42. Future localized content can use the canonical String Table and key
     policy without localization-framework changes.

43. The Unreal localization gather and compile workflow succeeds for
     the `LordSimulator` target with native `en`.

44. A packaged Windows Shipping build contains required `en`
     localization resources and can initialize and apply `en`
     successfully.

45. Editor/PIE and packaged Windows Shipping behavior satisfy
     applicable localization initialization, supported-culture,
     settings, and language-application requirements.

46. Unreal-native C++ automated localization tests exist and pass
     without an external testing dependency.

47. Automated tests deterministically cover the required startup
     success/failure/fallback states, unavailable active-language state,
     runtime success/failure/recovery, unsupported requests,
     initialization failure/idempotence, settings integration, startup
     completion, and exact required log messages without requiring
     additional production-supported cultures.

48. Automated tests use a deterministic internal test seam for
     environment-dependent localization outcomes without creating a
     second production localization implementation, supported-culture
     registry, or fallback system.

49. Automated tests add no fake production-supported cultures,
     placeholder production localization entries, or production-only
     test localization resources.

50. Automated configuration/resource tests verify the canonical target,
     native `en`, initial supported-culture set, canonical String Table
     asset and ID, and absence of placeholder entries where technically
     testable.

51. Windows Shipping packaging/resource inclusion and packaged behavior
     are verified separately from automated framework tests.

52. The implementation introduces no custom localization build scripts,
     runtime localization hot reload, external translation loading,
     localization file watching, language-selection UI, or Blueprint
     localization API.

53. `README.md` documents the actual localization target, canonical
     String Table, gather/compile workflow, supported-culture
     management, automated-test execution, packaging, and packaged-build
     verification workflow.

54. No localization-specific shutdown lifecycle/logs and no
     Development-mode localization logs are added.

55. The authoritative supported-culture set is read from
     runtime-readable Unreal project configuration, not from `.locmeta`,
     `.locres` discovery, OS cultures, resource discovery, String Table
     contents, or a hard-coded C++ registry; production configuration
     initially contains exactly `en`.

56. Localization initialization detects a mismatch between
     authoritative supported-culture configuration and the canonical
     `LordSimulator` Localization Target/resources as a structural
     initialization failure.

57. Before persisted `Language` is applied, game execution has `en` as
     baseline Unreal language and locale independent of the OS culture.

58. Unreal Editor validation does not change the Unreal Editor
     application's own language or locale.

59. If startup orchestration must move later for safe
     localization-resource availability, the required relative startup
     order is preserved and unrelated startup behavior remains
     unchanged.

60. Automated tests may use isolated in-memory localization fixtures to
     validate `FText` language-change behavior without adding production
     cultures, production entries, or packaged test resources.