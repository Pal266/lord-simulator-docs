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

Libraries, modules, APIs, tools, and functionality that are already part
of the project's established engine, language standard library,
toolchain, or existing dependency set are not considered new external
dependencies.

If the implementation agent determines that a new external dependency is
necessary to satisfy the specification, but the dependency is not
explicitly required by the specification, the implementation agent MUST
stop implementation and report the dependency requirement.

If a new external dependency is not necessary but the implementation
agent determines that introducing one could materially improve the
project or implementation, the implementation agent MAY stop
implementation and propose the dependency.

The implementation agent MUST NOT introduce the proposed dependency
unless the specification is subsequently updated to explicitly require
it.

When proposing a new external dependency, the implementation agent MUST
report:

-   the exact library, framework, package, plugin, SDK, or dependency
    being proposed;
-   the purpose for which it would be used;
-   why it would improve the project or implementation;
-   the relevant disadvantages, risks, maintenance costs, licensing
    considerations, or additional complexity introduced by the
    dependency;
-   how the specification can be implemented without the dependency,
    when implementation without it is possible;
-   how the implementation would differ if the proposed dependency were
    authorized.

The decision to introduce a new external dependency belongs to the
specification author and MUST NOT be made autonomously by the
implementation agent.

## 4. Logging

The implementation agent MUST use the Lord Simulator project logging
framework for specification-required game logging.

The implementation agent MUST log only Lord Simulator game logs through
the Lord Simulator project logging framework.

The implementation agent MUST NOT substitute, duplicate, redirect, or
capture general Unreal Engine logging as Lord Simulator game logging.

General Unreal Engine logs are outside the Lord Simulator project
logging requirements and MUST remain separate from Lord Simulator game
logs.

The implementation agent MUST NOT add Lord Simulator log entries that
are not explicitly defined by the specification.

For every specification-required log entry, the implementation agent
MUST use the exact logging mode and exact English log message defined by
the specification.

If a log entry is necessary to implement the specification correctly but
is not defined by the specification, the implementation agent MUST stop
implementation and report the missing logging requirement.

If, during implementation, the implementation agent identifies an event,
state change, error condition, diagnostic point, or other location where
an additional Lord Simulator log entry could materially improve
diagnostics, debugging, development, or supportability, but that log
entry is not defined by the specification, the implementation agent MUST
NOT add the log entry.

The implementation agent MAY stop implementation and propose the
additional log entry.

When proposing an additional log entry, the implementation agent MUST
report:

-   the exact location, event, or condition that should be logged;
-   why logging it would be useful;
-   the recommended logging mode: `Default` or `Development`;
-   the proposed exact English log message.

The implementation agent MUST NOT implement the proposed log entry
unless the specification is subsequently updated to explicitly require
it.

## 5. Settings

Every setting in the Lord Simulator settings object MUST have a default
value.

The default value for every setting MUST be explicitly defined by the
specification that introduces that setting.

Every setting represented in the persistent settings file is required.

When loading settings, if a required setting cannot be read or contains
an invalid value, the settings system MUST use that setting's defined
default value.

Settings MUST be loaded and reloaded from persistent storage as a
complete settings state. Individual settings MUST NOT be independently
reloaded from persistent storage.

Reading settings from persistent storage MUST always load all settings
as one complete state.

Runtime changes to individual settings MUST modify the in-memory
settings object and MUST NOT cause an individual setting to be
independently reloaded from persistent storage.

The persistent settings file MUST represent the complete persistent
settings object.

Whenever the persistent settings file is created or saved, all settings
MUST be written, including settings whose current values equal their
defined default values.

Adding a new setting to the settings object or persistent settings file
MUST be explicitly required by a specification.

## 6. Localization

Lord Simulator localization MUST use Unreal Engine localization
facilities. The implementation agent MUST NOT introduce a parallel
translation system, custom translation lookup system, or
language-specific translation branches unless explicitly required by a
specification.

The canonical Lord Simulator localization target is `LordSimulator`. The
implementation agent MUST NOT create additional localization targets or
parallel localization resource structures unless explicitly required by
a specification.

User-facing localizable text MUST use Unreal Engine localization-aware
text facilities, including `FText`, in a way that preserves Unreal
Engine's normal localization behavior.

Localizable text MUST remain localization-aware throughout its UI
lifetime. The implementation agent MUST NOT convert or cache localized
text as `FString` or other static non-localized text in a way that
prevents existing UI from reflecting a successful runtime language
change.

A custom Lord Simulator localization refresh or language-change event
system MUST NOT be introduced unless explicitly required by a
specification.

Dynamic user-facing localized text MUST use Unreal Engine
localization-aware `FText` formatting facilities. Localization keys MUST
NOT be generated from runtime values, and localizable text MUST NOT be
assembled through `FString` concatenation or equivalent logic in a way
that bypasses localization.

User-facing text involving numbers, pluralization, dates, times,
currencies, percentages, or other culture-sensitive values MUST use
Unreal Engine localization-aware formatting facilities where applicable.
The implementation agent MUST NOT introduce English-specific formatting
or grammatical rules unless explicitly required by a specification.

Localized text and translations MUST be stored and managed through
Unreal Engine localization resources. Language-specific translations
MUST NOT be embedded in C++, Blueprints, widgets, or other feature logic
unless explicitly required by a specification.

The implementation agent MUST use localization keys exactly as defined
by the specification. The implementation agent MUST NOT invent
localization keys, native English source text, or translations.

Existing localization keys MUST NOT be renamed, removed, or repurposed
unless explicitly required by a specification. An existing key MAY be
reused only when the new usage represents the same semantic text and
meaning. Identical English wording alone does not establish identical
semantic meaning.

Changing native English source text MUST NOT by itself cause an existing
localization key to be changed when the semantic meaning remains the
same.

The implementation agent MUST NOT invent, automatically rewrite, or
automatically replace translations when native English source text
changes. Existing translations and translation status MUST be handled
through Unreal Engine's localization workflow unless a specification
explicitly supplies replacement translations.

Native English fallback text for localizable user-facing content MUST be
provided through the project's Unreal Engine localization resources. The
implementation agent MUST NOT add duplicated hard-coded English fallback
text in C++, Blueprints, widgets, or other UI logic.

Missing localization entries or invalid localization references MUST NOT
be compensated for with custom fallback text, key-as-player-facing-text
substitution, a parallel fallback dictionary, or a custom translation
lookup system. The implementation MUST rely on Unreal Engine's
localization behavior unless a specification explicitly requires
different behavior.

Project logs, developer diagnostics, internal identifiers, technical
error information, and other non-user-facing development text MUST NOT
use localization resources unless explicitly required by a
specification. Changing the active game language MUST NOT change Lord
Simulator project log messages.

The set of Lord Simulator-supported cultures is project configuration
and MUST be treated as read-only runtime data. Runtime code MUST NOT
add, remove, rename, or otherwise modify supported cultures unless
explicitly required by a specification.

The native Lord Simulator culture is `en`. Runtime feature code MUST NOT
remove or replace this native-culture invariant.

Culture identifiers are technical configuration values. Player-facing
language-selection UI MUST display the corresponding native culture
display name obtained through the Lord Simulator localization framework
rather than exposing the culture identifier, unless explicitly required
by a specification.

Lord Simulator feature code, including C++ and Blueprints, MUST NOT
directly modify Unreal Engine's active language or locale.
Application-wide language and locale changes MUST go through the Lord
Simulator localization framework unless explicitly required by a
specification. Individual features, screens, widgets, and gameplay
systems MUST NOT temporarily override or independently maintain a
competing active culture.

The localization framework MUST remain independent of specific UI
screens, widgets, and gameplay features. UI and gameplay systems MAY
depend on localization functionality, but localization functionality
MUST NOT depend on those systems unless explicitly required by a
specification.

The application MUST maintain one authoritative application-wide
localization state. Individual features MUST NOT create competing
localization managers or independent active-language state.

Runtime localization MUST use resources provided through the project's
Unreal Engine localization and build pipeline. Runtime
localization-resource hot reloading, external translation loading,
localization file watching, or localization-pack importing MUST NOT be
introduced unless explicitly required by a specification.

Systems that create, cache, format, or display localizable user-facing
text MUST NOT perform that work until the application's localization
startup phase has completed. A localization failure MUST NOT by itself
permanently block unrelated application initialization unless a
specification explicitly requires that behavior.

The implementation agent MUST NOT add Blueprint-accessible localization
APIs merely because they may be useful. Blueprint exposure MUST be
explicitly required by a specification.

When localization work changes the gather, compile, cook, packaging,
verification, or other developer workflow required to produce a valid
packaged build, the implementation agent MUST update `README.md` in
accordance with the Project Build Documentation requirements.

## 7. Project Build Documentation

The implementation agent is responsible for maintaining `README.md` in
the project root.

`README.md` MUST contain complete instructions for building the project
from the repository and producing an installation file that can be
installed.

Whenever an implementation changes the build, packaging, dependencies,
prerequisites, tooling, or any other step required to produce the
installation file, the implementation agent MUST update `README.md` as
part of the same work.

## 8. Git Branches

The implementation agent MUST NOT work directly on the `development` or
`master` branches.

Before starting implementation, the implementation agent MUST create and
work on a dedicated branch for the specification.

The branch name MUST follow this pattern:

`type/name`

Where:

-   `type` MUST be taken from the specification's `Type` section.
-   `name` MUST be taken from the specification file name.

The specification prefix and number MUST NOT be included in the branch
name.

Example:

Specification file:

`spec-001-basic-window.md`

Specification type:

`feature`

Branch:

`feature/basic-window`
