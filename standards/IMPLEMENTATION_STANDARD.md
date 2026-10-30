# Implementation Standard

## 1. Specification Scope

The implementation agent MUST implement only the functionality
explicitly described in the `Requirements` section of the specification.

The implementation agent MUST NOT implement functionality, features,
improvements, or other behavioral changes that are not required by the
specification.

If the specification contains an inconsistency, contradiction, missing
information required for implementation, or another issue that prevents
unambiguous implementation, the implementation agent MUST stop
implementation and report the problem.

The implementation agent MUST NOT resolve specification inconsistencies
by inventing requirements or making product, game design, visual design,
or other unspecified decisions.

## 2. Behavior Preservation and Refactoring

The implementation agent MUST NOT change existing project behavior
unless that behavior change is explicitly required by the specification.

Functionality and behavior outside the scope of the specification MUST
remain unchanged.

The implementation agent MAY perform refactoring without explicit
authorization when the refactoring is useful for implementing the
specification or maintaining the affected code.

Refactoring performed without an explicit refactoring requirement MUST
preserve existing externally observable behavior and MUST NOT introduce
new functionality.

The implementation agent MUST NOT use refactoring as justification for
making product, game design, visual design, architectural behavior, or
other functional changes that are not required by the specification.

If a proposed refactoring would require changing existing behavior, the
implementation agent MUST NOT perform that behavioral change unless it
is explicitly required by the specification.

Unrelated refactoring SHOULD NOT be performed.

## 3. Dependency Management

The implementation agent MUST NOT introduce a new third-party library,
framework, package, plugin, SDK, or other external dependency unless
that dependency is explicitly required by the specification.

Libraries, modules, APIs, tools, and functionality already part of the
project's established engine, language standard library, toolchain, or
existing dependency set are not new external dependencies.

If a new external dependency is necessary but not explicitly required,
the implementation agent MUST stop and report it. If it is optional but
materially useful, the agent MAY stop and propose it, including its
purpose, benefits, risks, maintenance/licensing costs, dependency-free
alternative, and implementation differences. It MUST NOT be introduced
until explicitly authorized by the specification.

## 4. Logging

The implementation agent MUST use the Lord Simulator project logging
framework for specification-required game logging.

Only Lord Simulator game logs use that framework. General Unreal Engine
logs remain separate and MUST NOT be substituted, duplicated,
redirected, or captured as Lord Simulator game logging.

The implementation agent MUST NOT add Lord Simulator log entries not
explicitly defined by the specification. Required entries MUST use the
exact logging mode and exact English message defined by the
specification.

If a log is necessary but unspecified, the implementation agent MUST
stop and report it. The agent MAY propose an additional log, including
exact condition, usefulness, recommended `Default` or `Development`
mode, and exact English message, but MUST NOT implement it until the
specification explicitly requires it.

## 5. Settings

Every setting in the Lord Simulator settings object MUST have a default
value explicitly defined by the specification introducing it.

Every setting represented in the persistent settings file is required.
If a required setting cannot be read or is invalid, the settings system
MUST use its defined default.

Settings MUST be loaded and reloaded from persistent storage as one
complete settings state. Individual settings MUST NOT be independently
reloaded.

Runtime changes to individual settings MUST modify the in-memory
settings object and MUST NOT independently reload the setting from
persistent storage.

The persistent settings file MUST represent the complete persistent
settings object. Whenever it is created or saved, all settings MUST be
written, including settings equal to their defaults.

Adding a setting to the settings object or persistent file MUST be
explicitly required by a specification.

## 6. Localization

Lord Simulator localization MUST use Unreal Engine localization
facilities. The implementation agent MUST NOT introduce a parallel
translation system, custom translation lookup system, or
language-specific translation branches unless explicitly required.

The canonical Lord Simulator Localization Target is `LordSimulator`. The
implementation agent MUST NOT create additional localization targets or
parallel localization resource structures unless explicitly required.

The canonical Lord Simulator String Table is the asset-based table
established by the project specification. The implementation agent MUST
NOT replace it with a C++-registered table, redirect, or alternative
canonical String Table unless explicitly required by a specification.

User-facing localizable text MUST use Unreal Engine localization-aware
text facilities, including `FText`, preserving Unreal's normal
localization behavior.

Localizable text MUST remain localization-aware throughout its UI
lifetime. It MUST NOT be converted or cached as `FString` or other
static non-localized text in a way that prevents properly implemented UI
from reflecting a successful runtime language change.

A custom Lord Simulator localization refresh or language-change event
system MUST NOT be introduced unless explicitly required.

Dynamic localized user-facing text MUST use localization-aware `FText`
formatting. Localization keys MUST NOT be generated from runtime values,
and localizable text MUST NOT be assembled through English-specific
string concatenation or equivalent localization-bypassing logic.

Numbers, pluralization, dates, times, currencies, percentages, and other
culture-sensitive user-facing values MUST use Unreal localization-aware
formatting where applicable. English-specific formatting or grammatical
rules MUST NOT be introduced unless explicitly required.

Localized text and translations MUST be stored and managed through
Unreal localization resources and MUST NOT be embedded in C++,
Blueprints, widgets, or feature logic unless explicitly required.

The implementation agent MUST use localization keys exactly as specified
and MUST NOT invent keys, native English source text, or translations.

Existing keys MUST NOT be renamed, removed, or repurposed unless
explicitly required. A key MAY be reused only for the same semantic
meaning. Identical English wording alone does not establish identical
semantics.

Changing native English source wording while preserving semantic meaning
MUST NOT by itself change the localization key. The implementation agent
MUST NOT invent or automatically rewrite translations when English
source text changes.

Native English fallback text MUST be provided through Unreal
localization resources, not duplicated as hard-coded English fallback in
feature/UI logic.

Missing localization entries or invalid references MUST NOT be
compensated for with custom fallback text, key-as-player-facing-text
substitution, a parallel fallback dictionary, or custom lookup system.
Rely on Unreal behavior unless a specification explicitly requires
otherwise.

Project logs, developer diagnostics, internal identifiers, and technical
error information remain non-localized unless explicitly required.
Changing active game language MUST NOT change Lord Simulator project log
messages.

Lord Simulator-supported cultures are read-only project configuration at
runtime. Runtime code MUST NOT add, remove, rename, or otherwise modify
supported cultures unless explicitly required.

The authoritative Lord Simulator supported-culture set MUST come from the
project's explicit runtime-readable Unreal localization configuration. It MUST
NOT be inferred from `.locmeta`, `.locres`, compiled localization-resource
discovery, operating-system cultures, String Table contents, or a hard-coded C++
culture registry.

The canonical `LordSimulator` Localization Target/resources MUST remain
consistent with the authoritative supported-culture configuration. A
specification MAY define stricter validation and failure behavior for
inconsistency.

The native Lord Simulator culture is `en`. Runtime feature code MUST NOT
remove or replace this invariant.

Player-facing language-selection UI MUST display native culture display
names obtained through the Lord Simulator localization framework rather
than culture identifiers unless explicitly required.

Feature code, including C++ and Blueprints, MUST NOT directly modify
Unreal's active language or locale. Application-wide language/locale
changes go through the Lord Simulator localization framework unless
explicitly required. Features MUST NOT maintain competing active
cultures.

The localization framework MUST remain independent of specific UI
screens, widgets, and gameplay features unless explicitly required.

The application MUST maintain one authoritative application-wide
localization state. Individual features MUST NOT create competing
localization managers or independent active-language state.

Runtime localization MUST use resources provided through the project's
Unreal localization/build pipeline. Hot reloading, external translation
loading, file watching, or localization-pack importing MUST NOT be
introduced unless explicitly required.

### Localization startup phase

The application has one localization startup phase. It begins when
localization infrastructure initialization starts and completes only
after: 1. localization infrastructure initialization has reached its
session result; 2. the complete settings state has been loaded and
validated; 3. configured `Language` has been processed according to the
localization framework's startup behavior when localization
infrastructure is available; and 4. the localization framework has
established its resulting runtime localization state for the session,
including any active-language fallback or unavailable-active-language
state.

Localization startup completion does not require localization
initialization or language application to succeed. Failure states are
valid completed startup states.

Systems that create, cache, format, or display localizable user-facing
text MUST NOT perform localization-dependent initialization before the
localization startup phase is complete.

Localization initialization or language-application failure MUST NOT
prevent the localization startup phase from completing or permanently
block unrelated application initialization unless a specification
explicitly requires otherwise.

The implementation agent MUST NOT add Blueprint-accessible localization
APIs merely because they may be useful. Blueprint exposure MUST be
explicitly required.

When localization work changes gather, compile, cook, packaging,
verification, automated-test execution, or another developer workflow
required to produce or verify a valid build, `README.md` MUST be updated
in accordance with Project Build Documentation.

## 7. Project Build Documentation

The implementation agent is responsible for maintaining `README.md` in
the project root.

`README.md` MUST contain complete instructions for building the project
from the repository and producing an installation file that can be
installed.

Whenever implementation changes build, packaging, dependencies,
prerequisites, tooling, testing commands required by a specification, or
another step required to produce or verify the installation file, the
implementation agent MUST update `README.md` as part of the same work.

## 8. Git Branches

The implementation agent MUST NOT work directly on `development` or
`master`.

Before starting implementation, the implementation agent MUST create and
work on a dedicated branch for the specification.

The branch name MUST follow `type/name`, where `type` is taken from the
specification's Type section and `name` is taken from the specification
filename without the `spec-###-` prefix.

Example:

-   Specification: `spec-001-basic-window.md`
-   Type: `feature`
-   Branch: `feature/basic-window`
