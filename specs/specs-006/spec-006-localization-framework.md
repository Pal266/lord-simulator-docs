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
`LordSimulator` and a canonical Unreal String Table asset with the
identity `LordSimulator`.

English (`en`) is the native/source culture, authoritative fallback
culture, and default configured language. Initially, `en` is the only
supported culture.

The persistent `Language` setting determines both the Unreal language
and locale. The framework distinguishes the configured language stored
in settings from the language successfully active during the current
runtime session.

This specification establishes localization infrastructure only. It does
not introduce placeholder user-facing localization entries, additional
supported cultures, a language-selection UI, custom translation lookup,
Blueprint localization APIs, runtime localization-resource reloading, or
automated localization tests.

# Requirements

## Localization infrastructure

1.  Use Unreal Engine 5.8 localization facilities. Do not implement a
    custom translation parser, custom localization file format, custom
    translation lookup system, or parallel translation engine.

2.  Configure one canonical Unreal Localization Target named
    `LordSimulator`.

3.  Configure the `LordSimulator` Localization Target with:

    -   native/source culture `en`;
    -   initial supported cultures containing only `en`;
    -   Game loading policy;
    -   standard Unreal localization configuration and generated
        localization resources.

4.  Create one canonical Unreal String Table asset with the identity
    `LordSimulator`.

5.  The canonical String Table is the default location for future Lord
    Simulator localizable text unless a future specification explicitly
    requires another table.

6.  Do not add placeholder localization entries merely to populate or
    test the String Table.

7.  Localization resources must use Unreal Engine's standard
    localization target/resource structure and compiled localization
    resources. Do not introduce a separate Lord Simulator
    translation-resource format.

8.  `en` is a required localization invariant. Successful localization
    initialization requires the native culture to be `en` and `en` to be
    a Lord Simulator-supported culture.

## Supported cultures and metadata

9.  The Lord Simulator Localization Target/configuration is the
    authoritative source of supported cultures. Do not maintain a second
    hard-coded supported-culture registry.

10. Supported cultures are read-only runtime configuration.

11. Supported-culture identifiers are exact and case-sensitive. Do not
    normalize, truncate, case-convert, or automatically map requested
    identifiers.

12. Regional or otherwise specific Unreal culture identifiers are
    permitted when explicitly configured by a future specification. For
    example, `pt-BR` and `pt` are distinct supported-culture values
    unless both are explicitly configured.

13. Expose supported cultures through the Lord Simulator localization
    framework in deterministic project-configuration order. Do not sort
    them independently by culture identifier or display name.

14. Obtain each supported culture's native display name from Unreal
    Engine internationalization/culture facilities. Do not maintain a
    separate project-owned culture-display-name translation table.

15. Initially the supported-language metadata is:

-   culture identifier: `en`;
-   native display name expected from Unreal: `English`.

16. If required supported-culture information cannot be reliably
    discovered during initialization, supported-culture discovery is
    considered failed. Do not substitute a hard-coded supported-culture
    list.

## Application-wide localization state

17. Maintain one authoritative application-wide Lord Simulator
    localization state.

18. The localization framework must expose, without requiring exact C++
    class or function names:

-   supported languages and their native display names;
-   configured language;
-   active language;
-   validation of whether a culture is supported;
-   an application-wide language-change operation;
-   unambiguous success/failure from a language-change request.

19. Supported-language entries contain stable culture metadata only.
    Configured/active flags must not be stored as duplicate mutable
    state inside each supported-language entry.

20. Configured language means the value in the complete in-memory
    settings object.

21. Active language means the culture successfully applied by the Lord
    Simulator localization framework for the current runtime session.

22. Active language is runtime-only state and must not be persisted.

23. The localization framework manages language policy and culture state
    only. Actual localized text lookup/resolution must use Unreal Engine
    `FText` and the canonical String Table/localization resources
    directly. Do not add a Lord Simulator translation-lookup API.

24. Do not require Blueprint-callable localization APIs in this
    specification.

## Language setting

25. Add a persistent setting named exactly `Language`.

26. `Language` is case-sensitive.

27. The default `Language` value is exactly `en`.

28. `Language` is the only localization-related player setting
    introduced by this specification. Do not add separate
    native-language, fallback-language, or locale settings.

29. A `Language` value is valid when:

-   it is exactly `en`; or
-   supported-culture discovery succeeded and the value exactly matches
    a culture explicitly configured as supported by Lord Simulator.

30. If supported-culture discovery fails, `en` remains valid because it
    is the fixed native/default invariant. Any other `Language` value
    cannot be verified as supported and is invalid.

31. If localization initialization fails after supported-culture
    discovery succeeded, discovered supported cultures remain valid
    configuration values even though they cannot be applied during that
    session.

32. If `Language` is missing while loading settings:

-   use `en` in the complete in-memory settings object;
-   log in Default mode exactly:
    `Setting 'Language' is missing. Default value 'en' will be used.`

33. If `Language` has an invalid value while loading settings:

-   use `en` in the complete in-memory settings object;
-   log in Default mode exactly:
    `Setting 'Language' has an invalid value. Default value 'en' will be used.`

34. Existing settings-framework parsing, duplicate-setting,
    complete-state loading, comparison, and persistence behavior applies
    to `Language`.

35. When a complete settings file is created or saved, it must include
    `Language` together with all other persistent settings, even when
    `Language=en`.

36. Missing or invalid persisted `Language` state is repaired by the
    normal complete-settings shutdown comparison/save behavior. Do not
    introduce a special immediate write for this setting.

37. Do not automatically select the operating-system language. On a
    fresh installation the configured language is `en` regardless of
    Windows language.

## Startup lifecycle

38. Localization initialization is a single-attempt, idempotent
    application-session lifecycle.

39. The first initialization request performs initialization. After
    successful initialization, later initialization requests are
    successful no-ops and must not recreate state, reset language state,
    or emit another initialization lifecycle log sequence.

40. If the first initialization attempt fails, the framework remains in
    the failed state for the rest of that application session. Do not
    automatically retry initialization.

41. Startup ordering must be:

42. initialize project logging in Default mode;

43. initialize the Lord Simulator localization framework;

44. start settings loading;

45. load the complete settings object;

46. apply `LogMode`;

47. if localization initialization succeeded, apply configured
    `Language` as both Unreal language and locale;

48. complete settings loading;

49. mark the localization startup phase complete;

50. continue application startup.

51. Systems that create, cache, format, or display localizable
    user-facing text must not perform that work before the localization
    startup phase is complete.

52. Localization failure is non-fatal. Once settings loading and the
    applicable localization startup steps are complete, the rest of the
    application may continue.

53. On localization initialization start, log in Default mode exactly:
    `Localization initialization started.`

54. Successful localization initialization requires, at minimum:

-   the canonical Lord Simulator localization runtime resources required
    by the framework are available;
-   the canonical `LordSimulator` String Table is available;
-   the native culture invariant is `en`;
-   `en` is supported;
-   the supported-culture information required by the framework can be
    obtained.

46. On successful localization initialization, log in Default mode
    exactly: `Localization initialization completed.`

47. On localization initialization failure, log in Default mode exactly:
    `Localization initialization failed. Native language 'en' will be used where available.`

48. Do not log `Localization initialization completed.` when
    initialization failed.

49. If localization initialization fails:

-   continue startup;
-   continue normal settings loading;
-   retain any supported-culture metadata that was successfully
    discovered before the later failure;
-   do not attempt the startup language-application operation through
    the Lord Simulator localization framework;
-   do not change a valid configured `Language` solely because
    initialization failed.

50. Do not initialize or cycle through every supported culture during
    normal startup. Only the configured language is applied.

## Startup language application

51. Applying `Language` must set both Unreal Engine language and locale
    together using Unreal Engine's standard facilities.

52. When the configured language is successfully applied during startup:

-   set active language to that culture;
-   retain the same configured language;
-   log in Default mode exactly: `Language '<culture>' was applied.`
    where `<culture>` is the exact applied culture identifier.

53. If a configured language is valid but Unreal cannot apply it during
    startup:

-   retain the configured `Language` in the in-memory settings object;
-   use native `en` for the current runtime session;
-   active language becomes `en` where Unreal/native localization
    remains available;
-   do not replace the configured value with `en`;
-   do not persist `en` merely because application failed;
-   log in Default mode exactly:
    `Language '<culture>' could not be applied. Native language 'en' will be used for the current session.`

54. A valid startup language-application failure is a runtime/resource
    failure, not an invalid-setting condition.

## Runtime language changes

55. Normal runtime feature code, including C++ and Blueprints, must not
    directly modify the in-memory `Language` setting or Unreal Engine's
    active language/locale independently. Runtime application-wide
    language changes must go through the Lord Simulator localization
    framework.

56. A runtime language-change request must validate the requested
    culture against Lord Simulator-supported cultures before attempting
    to apply it.

57. If a runtime request uses an unsupported culture:

-   do not call Unreal to apply it;
-   do not change configured language;
-   do not change active language;
-   return failure;
-   log in Default mode exactly:
    `Language '<requested>' is not supported. Language '<active>' will remain active.`
    where `<requested>` is the exact requested identifier and `<active>`
    is the language actually remaining active.

58. If the requested runtime language is already both configured and
    active:

-   treat the request as a successful no-op;
-   return success;
-   do not call Unreal unnecessarily;
-   do not refresh UI unnecessarily;
-   do not emit `Language '<culture>' was applied.` or another
    localization log.

59. For a supported runtime language change that differs from current
    configured/active state:

-   attempt to apply the requested culture as both Unreal language and
    locale;
-   only after successful application update configured `Language`;
-   set active language to the successfully applied culture;
-   allow Unreal's normal localization-aware `FText` behavior to update
    existing properly implemented localized UI;
-   return success;
-   log in Default mode exactly: `Language '<culture>' was applied.`

60. A successful runtime language change modifies the complete in-memory
    settings object but does not immediately write `settings.ini`.
    Normal shutdown comparison/save behavior persists the change.

61. If a supported runtime language change cannot be applied:

-   reject the requested change;
-   retain the previous configured language;
-   retain the previous successfully active language;
-   do not persist the failed requested language;
-   return failure;
-   log in Default mode exactly:
    `Language '<requested>' could not be applied. Language '<active>' will remain active.`

62. If a runtime language change is requested after localization
    initialization failed:

-   reject the request;
-   do not attempt an Unreal culture change through the Lord Simulator
    framework;
-   retain configured language;
-   retain the language actually active;
-   return failure;
-   use the runtime application-failure log:
    `Language '<requested>' could not be applied. Language '<active>' will remain active.`

63. Runtime language changes require no application restart, mandatory
    confirmation dialog, pending-language state, or
    localization-framework-level Apply operation.

64. Do not introduce a custom Lord Simulator localization refresh/event
    system. Properly implemented localized UI must use Unreal
    localization-aware `FText` behavior.

## Localization fallback and content behavior

65. Native English (`en`) is the authoritative source/fallback culture.

66. A supported non-native culture is not required to have 100%
    translation coverage unless a future specification explicitly
    requires a coverage level or particular translations.

67. Missing translations in a supported non-native culture must rely on
    Unreal Engine's native/source fallback behavior.

68. Every future Lord Simulator localization entry must have native
    English source text as required by the project standards.

69. Do not manufacture runtime text when the underlying localization
    entry/source/reference is missing.

70. Do not substitute localization keys themselves as player-facing
    fallback text.

71. Do not add project logging for every localization lookup or normal
    missing-translation fallback.

72. Project logs and developer diagnostics remain non-localized and must
    not change with the active game language.

## Localization content and key policy

73. Future localizable Lord Simulator text uses the canonical
    `LordSimulator` String Table unless explicitly required otherwise.

74. Localization keys are semantic, hierarchical, case-sensitive
    PascalCase segments separated by periods, for example:

-   `MainMenu.NewGame`
-   `Settings.Language`
-   `Building.Farm.Description`

75. Localization keys identify semantic purpose/context rather than
    current English wording, widget classes, source files, or UI
    positions.

76. Localization keys must be unique within the canonical Lord Simulator
    localization resources.

77. An existing key may be reused only for the same semantic
    text/meaning.

78. Existing localization keys must not be renamed, removed, or
    repurposed unless explicitly required by a future specification.

79. Changing native English wording while preserving semantic meaning
    does not by itself require a new key.

80. Feature implementations must not invent localization keys, native
    English source text, translations, tooltips, accessibility text, or
    other user-facing localization content omitted from the implementing
    specification.

81. Dynamic localized user-facing text and culture-sensitive values must
    use Unreal Engine localization-aware `FText` formatting facilities
    rather than runtime-generated keys or English-specific string
    concatenation/formatting.

## Resource and packaging workflow

82. Establish the standard Unreal Engine 5.8 localization workflow for
    the `LordSimulator` Localization Target:

-   manage the target through Unreal's standard localization
    tooling/configuration;
-   gather localization source data;
-   manage translations through Unreal localization resources;
-   compile localization resources;
-   cook/package required resources for Windows Shipping.

83. Do not add custom localization build scripts, a custom translation
    compiler, or custom command-line localization automation in this
    specification.

84. Localization data/resources must remain editable through the Unreal
    localization workflow without requiring C++ source changes merely to
    change translation wording.

85. Windows Shipping builds must include the Lord Simulator localization
    resources and internationalization data required by:

-   native culture `en`;
-   every culture explicitly configured as supported.

86. Do not intentionally package Lord Simulator localization resources
    for cultures that are not configured as supported. Unreal Engine
    shared internationalization data required internally is not
    prohibited by this requirement.

87. Localization behavior must work in Editor/PIE and in a packaged
    Windows Shipping build where applicable.

88. The development/package validation workflow must verify every
    configured supported culture can:

-   be recognized as supported;
-   provide its native display name;
-   be activated as both Unreal language and locale;
-   access its required packaged localization resources;
-   use native English fallback for untranslated entries;
-   return to `en` successfully.

89. Localization validation must detect
    structural/resource/configuration failures supported by Unreal's
    standard localization tooling. Incomplete translation coverage for a
    supported non-native culture is permitted unless explicitly
    prohibited by a future specification.

90. Do not create a custom automated localization test suite in this
    specification. The required behavior must still be
    manually/verifiably tested against the Acceptance Criteria.

## Documentation

91. Update the project root `README.md` with the actual Unreal Engine
    5.8 localization workflow established by the implementation.

92. The README localization documentation must be sufficient for a
    developer to:

-   locate/manage the `LordSimulator` Localization Target;
-   gather localization data;
-   compile localization resources;
-   add/manage a supported culture through the established Unreal
    workflow;
-   verify native culture `en`;
-   package required localization resources in the Windows Shipping
    build;
-   verify a supported culture in the packaged build.

93. The README is documentation only. Unreal project localization
    configuration/assets remain authoritative.

94. Do not add localization-specific shutdown lifecycle or shutdown
    logs. Unreal Engine owns the localization subsystem lifetime unless
    a future specification introduces a concrete Lord Simulator-owned
    resource requiring explicit cleanup.

95. Do not add Development-mode localization logs in this specification.

# Acceptance Criteria

1.  The project contains a canonical Unreal Localization Target named
    `LordSimulator` with native culture `en`, Game loading policy, and
    only `en` initially configured as supported.

2.  The project contains a canonical Unreal String Table asset with
    identity `LordSimulator` and no placeholder localization entries
    introduced solely by this specification.

3.  The implementation uses Unreal Engine localization facilities and
    contains no custom translation parser, custom localization file
    format, parallel translation lookup system, or language-specific
    translation branches.

4.  Localization initialization occurs after project logging
    initialization and before settings loading starts.

5.  A successful initialization produces exactly the required Default
    lifecycle logs:

    -   `Localization initialization started.`
    -   `Localization initialization completed.`

6.  A failed initialization produces:

    -   `Localization initialization started.`
    -   `Localization initialization failed. Native language 'en' will be used where available.`
        and does not produce `Localization initialization completed.`

7.  Localization initialization failure is non-fatal, settings still
    load, and no startup language-application attempt is made through
    the failed localization framework.

8.  Re-requesting initialization after successful initialization is a
    successful no-op without duplicate initialization lifecycle logs or
    state reset.

9.  Re-requesting initialization after failed initialization does not
    retry initialization during the same application session.

10. Supported cultures are obtained from the Lord Simulator Unreal
    localization configuration rather than a duplicate hard-coded
    registry.

11. Initially the supported-language collection contains only exact
    culture identifier `en`, and its native display name is obtained
    through Unreal culture facilities as `English`.

12. Supported cultures are exposed in deterministic
    project-configuration order and cannot be mutated by normal runtime
    code.

13. `Language` exists as a persistent setting, is case-sensitive,
    defaults to `en`, and no separate persistent Locale/native/fallback
    language setting is introduced.

14. A fresh settings state results in configured `Language=en`
    regardless of Windows language.

15. Missing `Language` produces configured `en` and exactly:
    `Setting 'Language' is missing. Default value 'en' will be used.`

16. Invalid `Language` produces configured `en` and exactly:
    `Setting 'Language' has an invalid value. Default value 'en' will be used.`

17. If supported-culture discovery fails, `en` remains valid and any
    non-`en` Language value is treated as invalid because support cannot
    be verified.

18. If localization initialization fails after supported cultures were
    successfully discovered, those discovered cultures remain valid
    configuration values and are not rewritten merely because runtime
    localization initialization failed.

19. Complete settings creation/saving includes `Language`, including
    when its value is the default `en`.

20. Startup applies the configured valid `Language` as both Unreal
    language and locale only after the complete settings object is
    loaded and `LogMode` has been applied.

21. Successful startup language application sets configured and active
    language to the requested culture and logs exactly:
    `Language '<culture>' was applied.`

22. A valid configured language that cannot be applied at startup
    remains the configured language, active runtime localization falls
    back to native `en` where available, the configured value is not
    replaced/persisted as `en`, and the exact startup failure log is
    emitted.

23. Configured language and active language are independently queryable
    concepts and active language is not persisted.

24. An unsupported runtime language request is rejected before Unreal
    culture application, leaves configured and active language
    unchanged, returns failure, and emits exactly:
    `Language '<requested>' is not supported. Language '<active>' will remain active.`

25. Requesting the already configured and active language returns
    success as a no-op, performs no unnecessary culture application, and
    emits no language-application log.

26. A successful supported runtime language change sets both Unreal
    language and locale, updates configured and active language, returns
    success, and logs exactly: `Language '<culture>' was applied.`

27. A successful runtime language change does not immediately write
    `settings.ini`; normal shutdown settings persistence writes the
    changed configured language.

28. A supported runtime language change that fails leaves the previous
    configured and active languages unchanged, returns failure, does not
    persist the failed request, and emits exactly:
    `Language '<requested>' could not be applied. Language '<active>' will remain active.`

29. A runtime language-change request made while localization
    initialization is failed is rejected, leaves configured and active
    state unchanged, returns failure, and uses the defined runtime
    application-failure log.

30. Properly localization-aware existing `FText` UI can reflect a
    successful runtime culture change without application restart or a
    custom Lord Simulator UI-refresh/localization-event system.

31. Systems that create/cache/format/display localizable user-facing
    text do not perform that work until the localization startup phase
    is complete.

32. Project logs remain English/non-localized when the active game
    language changes.

33. Missing non-native translations use Unreal's native/source fallback
    behavior; no custom fallback dictionary, hard-coded UI fallback
    text, or key-as-player-facing-text substitution is introduced.

34. Localization keys and localized content introduced in future work
    can use the canonical `LordSimulator` String Table and follow the
    project localization standards without requiring changes to the
    localization framework.

35. The Unreal localization gather and compile workflow succeeds for the
    `LordSimulator` target with native `en`.

36. A packaged Windows Shipping build contains the required `en` Lord
    Simulator localization resources and can initialize and apply `en`
    successfully.

37. Editor/PIE and packaged Windows Shipping behavior satisfy the
    applicable localization initialization, supported-culture, settings,
    and language-application requirements.

38. The implementation introduces no custom localization build scripts,
    runtime localization hot reload, external translation loading,
    localization file watching, language-selection UI, Blueprint
    localization API, or custom automated localization test suite.

39. `README.md` documents the actual Unreal Engine 5.8 localization
    target, gather, compile, supported-culture management, packaging,
    and packaged-build verification workflow established by the
    implementation.

40. No localization-specific shutdown lifecycle/logs and no
    Development-mode localization logs are added.
