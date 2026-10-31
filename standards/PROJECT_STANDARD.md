# Lord Simulator Project Standard

## 1. Purpose

This standard defines the established project-wide technical architecture, canonical identifiers, runtime contracts, lifecycle rules, and persistent system behavior of Lord Simulator.

Specifications MAY rely on this standard without repeating its requirements.

A specification that intentionally changes an invariant in this file MUST require the project standard to be updated so the repository has one authoritative description of the resulting project behavior.

## 2. Technical Baseline

The established Lord Simulator technical baseline is:

| Item | Canonical value |
|---|---|
| Human-facing product/application name | `Lord Simulator` |
| Game repository name | `lord-simulator` |
| Unreal Engine version | `5.8.4` |
| C++ language standard | `C++20` |
| Supported target platform | 64-bit Windows / `Win64` |
| Unreal project name | `LordSimulator` |
| Primary C++ module | `LordSimulator` |
| Game target | `LordSimulator` |
| Editor target | `LordSimulatorEditor` |
| Packaged game executable | `LordSimulator.exe` |
| Installer technology | Inno Setup |
| Installer output | `LordSimulatorSetup.exe` |
| Installation folder name | `Lord Simulator` |

The standard build-validation targets are:

- `LordSimulatorEditor` — Platform `Win64`, Configuration `Development`;
- `LordSimulator` — Platform `Win64`, Configuration `Shipping`.

Project source, include configuration, build configuration, packaging, and tooling MUST NOT depend on machine-specific absolute filesystem paths.

The project MUST remain buildable from source and capable of producing a Windows x64 packaged build and an installable `LordSimulatorSetup.exe`.

The installed application MUST launch successfully on supported 64-bit Windows systems.

## 3. Canonical User-Data Root

The canonical Lord Simulator user-data root is:

`Documents\Lord Simulator\`

where `Documents` means the current Windows user's Documents known folder resolved through the appropriate Windows/platform mechanism rather than a hard-coded filesystem path.

The installer MUST create the `Lord Simulator` directory under the current Windows user's Documents known folder.

Runtime systems that require this directory MUST ensure it exists when they initialize and MUST attempt to create it if it is missing.

Unless a specification explicitly establishes another project-wide storage location, persistent Lord Simulator user data stored outside Unreal-managed save facilities SHOULD use this canonical root.

Current canonical files under this root are:

- project log: `Documents\Lord Simulator\log.log`
- persistent settings: `Documents\Lord Simulator\settings.ini`

## 4. Logging Framework

### 4.1 Scope

Lord Simulator has a project-specific logging framework separate from general Unreal Engine logging.

The framework captures Lord Simulator project log entries only.

General Unreal Engine log output MUST NOT be copied, redirected, duplicated, or captured into the Lord Simulator project log.

The logging framework MUST operate:

- during development through Unreal Editor/PIE where applicable;
- in packaged Windows application execution.

All Lord Simulator project log messages are English and non-localized.

Changing active game language MUST NOT change Lord Simulator project log messages.

### 4.2 Logging Modes

The logging framework supports exactly these project logging modes:

- `Default`
- `Development`

`Default` is the initial active logging mode at the start of application startup before settings are loaded.

A log entry designated for `Default` MUST be written in both `Default` and `Development` modes.

A log entry designated specifically for `Development` MUST be written only while `Development` mode is active.

`Development` mode is intended for additional diagnostic or development information and Development-only logging MAY be performance-heavy.

### 4.3 Initialization and File Behavior

The logging framework MUST initialize as early as reasonably possible in Lord Simulator startup and before other Lord Simulator systems that may produce project log entries.

The canonical log file is:

`Documents\Lord Simulator\log.log`

At every application startup:

1. the logging framework MUST ensure the canonical user-data directory exists;
2. if `log.log` does not exist, it MUST be created;
3. if `log.log` already exists, its previous contents MUST be removed;
4. the resulting file represents the current application session only.

Log preservation, rotation, or archival is not part of the established logging architecture.

`log.log` MUST use UTF-8 encoding.

### 4.4 Entry Format

Every Lord Simulator project log entry MUST contain a local system timestamp in this format:

`YYYY-MM-DD HH:MM:SS`

Every log entry MUST use this basic format:

`[YYYY-MM-DD HH:MM:SS] Message`

Example:

`[2026-10-29 15:20:31] New log file was created.`

### 4.5 Required Existing Lifecycle Logs

After the log file has been successfully created or an existing file has been successfully cleared for the current application session, the logging framework MUST write in `Default` mode:

`New log file was created.`

When Lord Simulator begins normal application/module shutdown, before settings persistence and before the logging framework is shut down, the application MUST write in `Default` mode:

`Application shutdown started.`

### 4.6 Failure Behavior

Failure to:

- create the canonical user-data directory;
- create or clear `log.log`;
- initialize file logging;
- write a project log entry;

MUST NOT intentionally terminate, crash, or permanently block normal application startup or shutdown.

## 5. Settings Framework

### 5.1 Canonical Settings State

Lord Simulator has one complete in-memory settings object representing the current settings state.

Persistent settings are stored in:

`Documents\Lord Simulator\settings.ini`

The persistent file uses INI format.

Persistent Lord Simulator settings are stored in a section named exactly:

`[Settings]`

Every persistent setting has a defined default value.

The persistent file represents the complete persistent settings object.

Whenever the file is created or saved, all persistent settings MUST be written, including settings whose values equal their defaults.

Settings MUST be loaded and reloaded from persistent storage as one complete state.

Individual settings MUST NOT be independently loaded or reloaded from persistent storage.

Reading settings from disk MUST construct a complete candidate settings state before replacing the current in-memory settings state.

Runtime changes to individual settings modify the in-memory settings object and MUST NOT independently reload that setting from persistent storage.

### 5.2 INI Parsing Contract

The `[Settings]` section name is case-sensitive.

Leading and trailing whitespace surrounding the complete section-header line is ignored.

Whitespace inside the section header is not ignored.

Only exact `[Settings]` identifies the Lord Simulator settings section.

Examples:

Recognized:

- `[Settings]`
- `   [Settings]`
- `[Settings]   `

Not recognized:

- `[settings]`
- `[SETTINGS]`
- `[ Settings ]`

When determining whether a line begins a section, leading and trailing whitespace surrounding the complete line is first ignored.

Any resulting line that begins with `[` ends the current `[Settings]` section.

Settings after that line MUST NOT be treated as belonging to `[Settings]` unless another exact valid `[Settings]` section is encountered.

Multiple exact `[Settings]` sections are treated as parts of one logical settings section for validation.

A persistent setting appearing more than once across one or more exact `[Settings]` sections is a duplicate and is invalid.

Setting keys and defined setting values are case-sensitive.

Leading and trailing whitespace surrounding setting keys and values is ignored when reading them.

Blank lines and lines beginning with `;` or `#` MAY be ignored.

A setting outside an exact `[Settings]` section does not satisfy the requirement for that setting.

### 5.3 File Creation and Read Failure

If `settings.ini` does not exist during startup:

- create it;
- write the complete settings object using defined default values;
- continue startup using those values.

If the settings file cannot be read, the complete settings object MUST use defined default values.

If a required setting is missing, duplicated, or invalid, that setting MUST use its defined default value.

Invalid or incomplete persistent state MUST NOT prevent construction of a complete in-memory settings state.

### 5.4 Existing Settings

#### `LogMode`

`LogMode` is a persistent setting.

Valid case-sensitive values are exactly:

- `Default`
- `Development`

Default:

`Default`

A missing `LogMode` uses `Default`.

An invalid or duplicate `LogMode` uses `Default`.

#### `Language`

`Language` is a persistent setting.

Default:

`en`

`Language` is case-sensitive.

Its validity and runtime behavior are defined by the Localization Framework section of this standard.

### 5.5 Settings Loading Logs

All settings-framework log entries in this section use `Default` mode.

When settings loading begins:

`Settings loading started.`

When settings loading completes:

`Settings loading completed.`

When `settings.ini` does not exist during startup:

`Settings file does not exist. A new settings file will be created.`

When a new settings file is successfully created:

`Settings file was created.`

When a new settings file cannot be created:

`Settings file could not be created. Default settings will be used.`

When an existing settings file cannot be read during loading:

`Settings file could not be read. Default settings will be used.`

When `LogMode` is missing:

`Setting 'LogMode' is missing. Default value 'Default' will be used.`

When `LogMode` is invalid, including duplicate occurrence:

`Setting 'LogMode' has an invalid value. Default value 'Default' will be used.`

When `Language` is missing:

`Setting 'Language' is missing. Default value 'en' will be used.`

When `Language` is invalid:

`Setting 'Language' has an invalid value. Default value 'en' will be used.`

### 5.6 Applying Settings at Startup

Project logging begins in `Default` mode.

The complete settings object is loaded and validated.

After settings are loaded sufficiently to establish the complete in-memory state, the loaded `LogMode` is applied to the logging framework.

The localization framework consumes the validated/defaulted `Language` value from the complete in-memory settings object.

The localization framework MUST NOT independently read `Language` from `settings.ini`.

### 5.7 Runtime Changes

Runtime modification of a setting changes the complete in-memory settings object.

A runtime setting change MUST NOT independently reload persistent storage.

A setting-specific subsystem MUST NOT independently persist one setting unless the architecture is explicitly changed by a specification.

For `Language`, successful application-wide runtime language changes are performed through the localization framework, which updates the complete in-memory settings state only after successful language application.

### 5.8 Shutdown Comparison and Persistence

During normal application shutdown, after the existing application-shutdown log entry and before the logging framework is shut down:

1. read the actual persistent settings file for comparison;
2. construct its complete persistent state without replacing the active in-memory settings object;
3. compare that persistent state with the current complete in-memory settings object;
4. if they are equivalent, do not rewrite the settings file;
5. if they differ, overwrite the persistent settings file with the complete in-memory settings object;
6. keep logging active until settings persistence and settings-system shutdown are complete.

Anything that prevents the persistent settings file from producing a complete state equivalent to the in-memory settings object is treated as a difference.

This includes:

- file missing;
- file unreadable;
- missing exact `[Settings]` section;
- missing required setting;
- duplicate required setting;
- invalid required setting.

External changes made to `settings.ini` while the application is running do not override the current in-memory settings state during shutdown comparison.

When a shutdown save is required, the complete in-memory settings state overwrites the persistent file.

Shutdown comparison MUST NOT load the persistent file into the active in-memory settings object.

When changed settings are successfully saved, log in `Default` mode:

`Settings were saved.`

When settings that require saving cannot be saved, log in `Default` mode:

`Settings could not be saved.`

Failure to save settings MUST NOT intentionally crash the application or prevent shutdown from continuing.

## 6. Localization Framework

### 6.1 Core Architecture

Lord Simulator localization uses Unreal Engine 5.8 localization facilities.

The project MUST NOT use a parallel translation engine, custom translation parser, custom translation file format, or custom feature-level translation lookup system.

The canonical Unreal Localization Target is named exactly:

`LordSimulator`

The target uses:

- native/source culture `en`;
- Game loading policy;
- standard Unreal localization configuration;
- standard generated localization resources.

The authoritative native culture is `en`.

`en` is a required project invariant and MUST be a supported Lord Simulator culture.

The initial production-supported culture set is exactly:

- `en`

The canonical asset-based Unreal String Table is:

`/Game/Localization/ST_LordSimulator`

The canonical String Table uses the Lord Simulator project identity `LordSimulator` as its expected String Table ID as established by the asset. References MUST use the identifier Unreal assigns to the asset-based table rather than introducing a parallel C++ registration or redirect to manufacture an identifier.

The canonical Localization Target and the canonical String Table are distinct Unreal localization concepts even though they share the `LordSimulator` project identity.

References to the canonical asset-based String Table MUST use the identifier Unreal assigns to the asset-based table.

The project MUST NOT create a second C++-registered canonical String Table or redirect merely to force another Table ID.

The canonical String Table is the default location for future Lord Simulator localizable text unless a specification explicitly requires another table.

Placeholder production localization entries MUST NOT be added merely to populate or test the String Table.

Localization resources MUST use Unreal Engine's standard localization target/resource structure and compiled localization resources.

### 6.2 Authoritative Supported Cultures

The Lord Simulator-supported culture set MUST come from explicit Unreal project localization configuration stored in runtime-readable form.

The supported-culture set MUST NOT be inferred from:

- `.locmeta`;
- `.locres` discovery;
- installed operating-system cultures;
- Unreal localization-resource discovery;
- String Table contents;
- a separate hard-coded C++ culture registry.

A culture having discoverable Unreal localization resources does not by itself make that culture Lord Simulator-supported.

Supported-culture configuration is read-only at runtime.

Runtime code MUST NOT add, remove, rename, or otherwise mutate the Lord Simulator-supported culture set.

The canonical `LordSimulator` Localization Target/resources MUST remain consistent with the authoritative supported-culture configuration.

Every configured supported culture MUST be represented by the target as required by Unreal's localization workflow.

The target MUST NOT define an additional Lord Simulator-supported culture outside the authoritative configuration.

A structural mismatch between authoritative supported-culture configuration and the canonical target/resources is a localization initialization failure.

If required supported-culture information cannot be reliably discovered during initialization, supported-culture discovery fails.

The framework MUST NOT substitute a hard-coded supported-culture list after discovery failure.

### 6.3 Culture Identifier Policy

Lord Simulator validates supported-culture identifiers using exact, case-sensitive matching.

The project MUST NOT normalize, truncate, case-convert, automatically map, or use parent-culture matching to turn an unsupported requested identifier into a supported `Language` value.

Regional or otherwise specific Unreal culture identifiers are valid when explicitly configured as supported.

For example:

- `pt-BR`
- `pt`

are distinct Lord Simulator supported-language identifiers.

Supporting one does not support the other.

This exact-match policy applies to Lord Simulator configuration and validation only.

It MUST NOT disable, replace, or interfere with Unreal Engine's normal localization-resource resolution and fallback behavior after a supported culture has been selected.

Supported cultures MUST be exposed without duplicates.

Each supported culture's native display name MUST be obtained from Unreal Engine internationalization/culture facilities.

Player-facing language-selection UI MUST display native culture display names obtained through the Lord Simulator localization framework rather than raw culture identifiers unless a specification explicitly requires otherwise.

The project MUST NOT maintain a separate project-owned culture-display-name translation table.

For the initial culture:

- culture identifier: `en`
- expected native display name: `English`

### 6.4 Application-Wide Localization State

Lord Simulator maintains one authoritative application-wide localization state.

Individual features MUST NOT create competing localization managers or independent active-language state.

The localization framework MUST remain independent of specific UI screens, widgets, and gameplay features unless a specification explicitly changes that architecture.

The framework exposes, without requiring particular C++ class or function names:

- supported cultures and native display names;
- configured language;
- active language;
- an unambiguous unavailable-active-language state;
- validation of whether a culture is supported;
- an application-wide language-change operation;
- unambiguous success/failure from language-change requests.

Supported-language entries contain stable culture metadata only.

Configured/active flags MUST NOT be stored as duplicated mutable state inside every supported-language entry.

Configured language means the `Language` value in the complete in-memory settings object.

Active language means the culture successfully applied by the Lord Simulator localization framework for the current application session.

Active language MAY be unavailable when no culture has been successfully applied during the session.

Unavailable active language MUST be represented as an unavailable/optional state, not with a synthetic culture identifier such as:

- `none`
- `unknown`
- `invalid`
- `unavailable`

Active language is runtime-only state and MUST NOT be persisted.

### 6.5 Localization-Aware Text

Actual localized text lookup and resolution use Unreal Engine `FText`, the canonical String Table, and Unreal localization resources directly.

The Lord Simulator localization framework manages localization policy and culture state; it MUST NOT become a feature-level translation lookup API.

User-facing localizable text MUST remain localization-aware throughout its UI lifetime.

Localizable text MUST NOT be converted or cached as `FString` or another static non-localized representation when doing so prevents successful runtime language changes from being reflected.

Dynamic localized text MUST use localization-aware `FText` formatting.

Localization keys MUST NOT be generated from runtime values.

Localizable text MUST NOT be assembled through English-specific string concatenation or equivalent localization-bypassing logic.

Numbers, pluralization, dates, times, currencies, percentages, and other culture-sensitive player-facing values MUST use Unreal localization-aware formatting where applicable.

Localized text and translations MUST be managed through Unreal localization resources rather than embedded in feature logic unless explicitly required.

A custom Lord Simulator UI-refresh or localization-change event system MUST NOT be introduced merely to compensate for UI that failed to preserve localization-aware `FText`.

### 6.6 Localization Content and Key Policy

Future Lord Simulator localization entries use the canonical asset-based String Table `/Game/Localization/ST_LordSimulator` unless explicitly required otherwise.

Localization keys are case-sensitive semantic hierarchical names composed of PascalCase segments separated by periods.

Examples:

- `MainMenu.NewGame`
- `Settings.Language`
- `Building.Farm.Description`

Keys identify semantic purpose/context rather than:

- current English wording;
- widget class;
- source file;
- UI position;
- row number;
- another incidental implementation detail.

Keys MUST be unique within canonical Lord Simulator localization resources.

An existing key MAY be reused only for the same semantic meaning.

Existing keys MUST NOT be renamed, removed, or repurposed unless explicitly required.

Changing native English wording while preserving semantic meaning does not by itself require a new key.

Every Lord Simulator localization entry MUST have native English source text.

Feature implementations MUST NOT invent:

- localization keys;
- native English source text;
- translations;
- tooltips;
- accessibility text;
- other user-facing localization content.

Native English fallback text MUST be provided through Unreal localization resources and MUST NOT be duplicated as hard-coded English fallback in feature or UI logic.

Missing localization entries or invalid references MUST NOT be compensated for with:

- custom fallback text;
- key-as-player-facing-text substitution;
- a parallel fallback dictionary;
- a custom lookup system.

### 6.7 `Language` Setting

`Language` is the only established localization-related persistent player setting.

No separate native-language, fallback-language, or locale setting exists.

The default `Language` value is:

`en`

`Language` is case-sensitive.

A `Language` value is valid when:

- it is exactly `en`; or
- supported-culture discovery succeeded and the value exactly matches a culture explicitly configured as Lord Simulator-supported.

If supported-culture discovery fails:

- `en` remains valid because it is the fixed native/default invariant;
- any other `Language` value is invalid because support cannot be verified.

If localization initialization fails after supported-culture discovery succeeded, the discovered supported cultures remain valid configuration values even though they cannot be applied during that session.

A missing `Language` becomes `en` in the complete in-memory settings object.

An invalid `Language` becomes `en` in the complete in-memory settings object.

`Language` participates in the normal complete settings lifecycle:

- complete-state load;
- duplicate handling;
- missing/invalid fallback;
- complete in-memory state;
- runtime modification;
- complete-state comparison;
- complete-state persistence.

The localization framework MUST NOT independently read or persist `Language`.

Missing or invalid persisted `Language` state is repaired through the normal settings shutdown comparison/save lifecycle.

No special immediate persistence path exists for `Language`.

### 6.8 Baseline Game Culture

Lord Simulator MUST NOT automatically choose the operating-system language.

On a fresh installation the configured language is `en` regardless of Windows language.

Before persisted `Language` is applied, Lord Simulator game execution MUST use `en` as the baseline Unreal language and locale independently of the operating-system culture.

If localization initialization or startup language application cannot establish another active culture, the implementation MUST NOT intentionally fall back to the operating-system culture.

### 6.9 Localization Initialization

Localization initialization is a single-attempt application-session lifecycle.

The first initialization request performs initialization.

After successful initialization, later initialization requests are successful no-ops and MUST NOT:

- recreate localization state;
- reset language state;
- emit another initialization lifecycle log sequence.

If the first initialization attempt fails, the framework remains failed for the rest of that application session.

Initialization MUST NOT automatically retry after failure.

On initialization start, log in `Default` mode:

`Localization initialization started.`

Successful localization initialization requires at minimum:

- required canonical Lord Simulator localization runtime resources are available;
- canonical String Table `/Game/Localization/ST_LordSimulator` is available;
- native culture invariant is `en`;
- `en` is supported;
- supported-culture project configuration is readable;
- supported-culture configuration contains no duplicates;
- supported-culture configuration contains `en`;
- canonical target/resources are consistent with the authoritative supported-culture configuration.

On successful initialization, log in `Default` mode:

`Localization initialization completed.`

On localization initialization failure, log in `Default` mode:

`Localization initialization failed. Native language 'en' will be used where available.`

The completed log MUST NOT be emitted when initialization failed.

If localization initialization fails:

- startup continues;
- normal settings loading continues;
- successfully discovered supported-culture metadata is retained;
- startup language application through the failed Lord Simulator localization framework is not attempted;
- a valid configured `Language` is not changed solely because initialization failed;
- the resulting runtime localization state is established;
- the localization startup phase completes.

Normal startup MUST NOT initialize or cycle through every supported culture.

Only configured language and, if required, native `en` fallback are applied.

### 6.10 Startup Language Application

Applying a Lord Simulator language sets both Unreal Engine language and locale together using Unreal Engine standard facilities.

When configured language is successfully applied during startup:

- active language becomes that culture;
- configured language remains that culture;
- log in `Default` mode:
  `Language '<culture>' was applied.`

If a valid configured language other than `en` cannot be applied during startup:

- configured `Language` is retained;
- native `en` is explicitly attempted as both Unreal language and locale;
- configured `Language` is not replaced or persisted as `en`.

If that `en` fallback succeeds:

- active language becomes `en`;
- configured language remains unchanged;
- log in `Default` mode:
  `Language '<culture>' could not be applied. Native language 'en' will be used for the current session.`
- no additional fallback-success Lord Simulator log is emitted.

If configured language is `en` and cannot be applied, `en` MUST NOT be attempted a second time as fallback.

If configured `en` cannot be applied, or a non-native configured language fails and subsequent `en` fallback also fails:

- configured `Language` is retained;
- active language becomes unavailable;
- startup continues;
- log in `Default` mode:
  `Language '<culture>' could not be applied and native language 'en' could not be activated. Localization is unavailable for the current session.`

Only one startup language-application failure message is emitted for a failed configured-language application.

A valid startup language-application failure is a runtime/resource failure, not an invalid-setting condition.

### 6.11 Runtime Language Changes

Normal runtime feature code, including C++ and Blueprints, MUST NOT:

- directly modify the in-memory `Language` setting independently;
- directly modify Unreal Engine's active game language independently;
- directly modify Unreal Engine's active game locale independently.

Application-wide runtime language changes go through the Lord Simulator localization framework.

If localization initialization failed, every runtime language-change request is rejected before normal supported-culture validation.

Initialization failure takes precedence even if the requested culture would otherwise be unsupported.

The request:

- is rejected;
- does not attempt Unreal culture application through the Lord Simulator localization framework;
- does not change configured language;
- does not change active language;
- returns failure;
- uses the applicable application-failure log described below;
- does not also emit an unsupported-culture log.

Successful framework initialization followed by failure to establish an active language does not disable later runtime language-change requests.

A later supported request may attempt application normally.

After successful initialization, runtime requests validate the requested culture against Lord Simulator-supported cultures before applying it.

If the requested culture is unsupported:

- Unreal culture application is not attempted;
- configured language is unchanged;
- active language is unchanged;
- return failure;
- if active language exists, log:
  `Language '<requested>' is not supported. Language '<active>' will remain active.`
- if active language is unavailable, log:
  `Language '<requested>' is not supported. No language is currently active.`

If requested runtime language is already both configured and active:

- treat the request as a successful no-op;
- return success;
- do not call Unreal unnecessarily;
- do not perform a custom UI refresh;
- emit no localization log.

For a supported runtime language change that is not the no-op case:

1. attempt to apply requested culture as both Unreal language and locale;
2. only after successful application, update configured `Language` through the complete in-memory settings object;
3. set active language to the successfully applied culture;
4. rely on Unreal standard localization-aware `FText` behavior;
5. return success;
6. log in `Default` mode:
   `Language '<culture>' was applied.`

If a supported runtime language change cannot be applied while an active language exists:

- previous configured language is retained;
- previous active language is retained;
- failed requested language is not persisted;
- return failure;
- log in `Default` mode:
  `Language '<requested>' could not be applied. Language '<active>' will remain active.`

If a supported runtime language change cannot be applied while active language is unavailable:

- previous configured language is retained;
- active language remains unavailable;
- failed requested language is not persisted;
- return failure;
- log in `Default` mode:
  `Language '<requested>' could not be applied. No language is currently active.`

A successful runtime language change from unavailable active-language state sets the requested culture as both configured and active.

A successful runtime language change updates the complete in-memory settings state but does not immediately write `settings.ini`.

Normal settings shutdown comparison/save behavior persists the change.

Runtime language changes require no application restart, mandatory confirmation dialog, pending-language state, or localization-framework-level Apply operation.

Runtime request precedence is:

1. if localization initialization failed, reject as application failure and do not perform unsupported-culture handling;
2. otherwise validate requested culture;
3. if unsupported, reject as unsupported;
4. if supported, continue through no-op/application behavior.

### 6.12 Translation Fallback and Content Behavior

Native English (`en`) is the authoritative source/fallback culture.

A supported non-native culture is not required to have 100% translation coverage unless a specification explicitly requires a coverage level or particular translations.

Missing translations in a supported non-native culture rely on Unreal Engine native/source fallback behavior.

The project MUST NOT manufacture runtime text when an underlying localization entry/source/reference is missing.

Localization keys MUST NOT be substituted as player-facing fallback text.

The project MUST NOT log every localization lookup or normal missing-translation fallback.

Project logs and developer diagnostics remain English/non-localized.

### 6.13 Editor and PIE Behavior

In packaged or standalone game execution, Lord Simulator controls the game's language and locale according to this standard.

In Unreal Editor workflows, Lord Simulator localization behavior MUST NOT change the Unreal Editor application's own language or locale.

PIE/editor validation MUST use Unreal-supported game-localization preview/testing facilities or another Unreal-supported game-scoped mechanism.

If module `StartupModule()` timing is too early to safely initialize required localization resources, startup orchestration MAY move to the earliest appropriate Unreal Engine lifecycle point where the resources are safely available.

Required relative startup ordering MUST remain unchanged.

Unrelated startup behavior MUST remain unchanged.

### 6.14 Localization Resource and Packaging Workflow

The project uses the standard Unreal Engine 5.8 localization workflow for `LordSimulator`:

- manage the Localization Target through Unreal standard localization tooling/configuration;
- gather localization source data;
- manage translations through Unreal localization resources;
- compile localization resources;
- cook/package required localization resources for Windows Shipping.

The project MUST NOT use a custom localization build script, custom translation compiler, or custom command-line localization automation unless explicitly required.

Localization content/resources MUST remain editable through Unreal localization workflows without requiring C++ source changes merely to change translation wording.

Windows Shipping builds MUST include:

- Lord Simulator localization resources;
- the canonical String Table asset;
- internationalization data required by native `en`;
- internationalization/localization data required by every explicitly supported culture.

The implementation MUST use an appropriate verified Unreal cooking/staging mechanism.

`/Game/Localization` MUST NOT be required as an always-cook directory unless technically necessary.

The project MUST NOT intentionally package Lord Simulator localization resources for cultures not configured as supported.

Unreal Engine shared internationalization data required internally is permitted.

Localization behavior MUST work in Editor/PIE and packaged Windows Shipping execution where applicable.

The development/package validation workflow MUST verify every configured supported culture can:

- be recognized as supported;
- provide its native display name;
- be activated as both Unreal language and locale;
- access required packaged localization resources;
- use native English fallback for untranslated entries;
- return to `en` successfully.

Localization validation MUST detect structural/resource/configuration failures supported by Unreal standard localization tooling.

Incomplete translation coverage is permitted unless explicitly prohibited.

### 6.15 Automated Localization Tests

Lord Simulator localization uses Unreal Engine built-in C++ automation testing facilities.

An external testing framework MUST NOT be introduced merely for localization testing.

Automated tests MUST deterministically cover, where applicable:

- supported-culture discovery from authoritative runtime-readable project configuration;
- absence of duplicate supported cultures;
- mismatch detection between supported-culture configuration and canonical target/resources;
- exact case-sensitive culture validation;
- default, missing, and invalid `Language` behavior;
- configured language, active language, and unavailable active-language state;
- successful startup language application;
- non-native startup application failure followed by successful `en` fallback;
- non-native startup application failure followed by failed `en` fallback;
- failed configured `en` without a second `en` attempt;
- initialization single-attempt/idempotent behavior;
- successful runtime language change;
- already-configured-and-active no-op;
- unsupported runtime request;
- runtime application failure with active language;
- runtime application failure with unavailable active language;
- recovery from unavailable active language through a later successful runtime request;
- rejection of runtime requests after localization initialization failure;
- successful runtime language changes update in-memory settings without immediate persistence;
- localization does not independently load or save `Language`;
- localization startup phase completes on success and localization failure;
- exact required Lord Simulator log messages for tested paths.

Environment-dependent localization operations, including Unreal culture application, MUST have an internal test seam sufficient to simulate required success and failure outcomes deterministically.

The testability mechanism MUST NOT create:

- a second production localization implementation;
- a second production supported-culture registry;
- a second production fallback system.

Automated tests MAY create isolated test-only in-memory localization or String Table fixtures to validate localization-aware `FText` behavior across simulated language changes.

Test fixtures:

- MUST NOT be packaged;
- MUST NOT modify production supported-culture configuration;
- MUST NOT modify the canonical production String Table;
- MUST NOT create production localization resources.

Automated tests MUST NOT add fake production-supported cultures, placeholder production localization entries, or production-only test localization resources merely to create test scenarios.

Automated configuration/resource tests MUST verify the actual project configuration where technically testable, including:

- canonical Localization Target `LordSimulator`;
- native culture `en`;
- authoritative production supported-culture configuration;
- consistency between configuration and canonical target/resources;
- canonical String Table asset `/Game/Localization/ST_LordSimulator`;
- absence of placeholder entries introduced solely for testing.

Runtime language-change validation MUST use existing localization content when such content is available.

Automated tests do not replace Windows Shipping packaging verification.

Cooked/package resource inclusion and actual packaged behavior MUST still be verified through the development/package validation workflow.

### 6.16 Localization Documentation and Lifecycle Constraints

`README.md` MUST document the actual Unreal Engine localization workflow sufficiently for a developer to:

- locate/manage the `LordSimulator` Localization Target;
- locate the canonical String Table;
- gather localization data;
- compile localization resources;
- add/manage a supported culture through the established Unreal workflow;
- verify native culture `en`;
- run automated localization tests;
- package required localization resources in Windows Shipping;
- verify a supported culture in a packaged build.

The README is documentation only.

Unreal project localization configuration and assets remain authoritative.

The localization framework has no Lord Simulator-specific shutdown lifecycle or shutdown logs.

Unreal Engine owns localization subsystem lifetime unless a future specification introduces a concrete Lord Simulator-owned resource requiring explicit cleanup.

No Development-mode localization logs are part of the established framework.

## 7. Canonical Application Startup Lifecycle

Lord Simulator has one canonical application startup sequence.

The required relative ordering is:

1. initialize Lord Simulator project logging in `Default` mode;
2. initialize the Lord Simulator localization framework;
3. log that settings loading has started;
4. load and validate the complete settings object, including `LogMode` and `Language`;
5. apply loaded `LogMode` to the logging framework;
6. if localization initialization succeeded, process configured `Language` as both Unreal language and locale, including required native fallback behavior;
7. log that settings loading has completed;
8. establish the resulting runtime localization state;
9. mark the localization startup phase complete;
10. continue unrelated/general application startup.

The localization startup phase begins when localization infrastructure initialization starts.

It completes only after:

1. localization initialization has reached its session result;
2. the complete settings state has been loaded and validated;
3. configured `Language` has been processed according to startup behavior when localization infrastructure is available;
4. the resulting runtime localization state has been established, including fallback or unavailable active-language state.

Localization startup completion does not require localization initialization or language application to succeed.

Failure states are valid completed startup states.

Systems that create, cache, format, or display localizable user-facing text MUST NOT perform localization-dependent initialization before the localization startup phase is complete.

Localization initialization or language-application failure MUST NOT permanently block unrelated application initialization.

A future subsystem that needs a place in global startup ordering MUST define its ordering relative to this lifecycle through a specification and project-standard update.

## 8. Canonical Application Shutdown Lifecycle

Lord Simulator has one canonical normal-shutdown sequence.

The established relative ordering is:

1. application/module normal shutdown begins;
2. while logging is still active, write:
   `Application shutdown started.`
3. perform settings persistent-state comparison;
4. if required, persist the complete in-memory settings state;
5. complete settings-system shutdown/persistence work;
6. shut down the Lord Simulator logging framework;
7. allow remaining unrelated shutdown to continue as appropriate.

The logging framework MUST remain available throughout settings shutdown persistence because settings persistence may emit required project logs.

Settings save failure MUST NOT prevent shutdown from continuing.

A future subsystem requiring explicit shutdown ordering MUST define its relationship to this lifecycle through a specification and project-standard update.

## 9. Build and Project Documentation

The game project root contains `README.md`.

`README.md` MUST contain complete instructions for producing the installable `LordSimulatorSetup.exe` from the repository.

Documentation MUST include, where applicable:

- required software and prerequisites;
- required versions;
- Unreal Engine C++ build steps;
- standard Development Editor build verification;
- Windows x64 Shipping build/package steps;
- localization gather/compile workflow;
- automated-test commands required for project verification;
- localization packaged-resource verification;
- Inno Setup installer creation;
- installation verification;
- installed application launch verification.

When project behavior changes a required build, packaging, testing, localization, tooling, prerequisite, or installer step, the README MUST be updated to describe the actual resulting workflow.

## 10. Change Control

Canonical identifiers, paths, runtime contracts, startup/shutdown ordering, persistent state behavior, localization architecture, and build baseline in this file remain authoritative until intentionally changed.

A future specification MAY change them only when the change is explicit and `PROJECT_STANDARD.md` is updated so the resulting project has one non-contradictory authoritative standard.
