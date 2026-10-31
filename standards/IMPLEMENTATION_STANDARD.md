# Implementation Standard

## 1. Purpose and Applicable Standards

This standard defines how an implementation agent MUST perform Lord Simulator implementation work.

For every specification, the implementation agent MUST comply with:

- the specification being implemented;
- `SPEC_STANDARD.md`;
- `IMPLEMENTATION_STANDARD.md`;
- `PROJECT_STANDARD.md`.

The current project standards are authoritative for established project-wide behavior.

If the specification and the current standards are inconsistent, contradictory, or incomplete in a way that prevents unambiguous implementation, the implementation agent MUST stop implementation and report the problem.

The implementation agent MUST NOT silently choose one conflicting requirement over another.

## 2. Specification Scope

The implementation agent MUST implement only the functionality explicitly described in the `Requirements` section of the specification together with behavior already required by the project standards.

The implementation agent MUST NOT implement functionality, features, improvements, or behavioral changes that are not required by the specification or the standards.

If the specification contains an inconsistency, contradiction, missing information required for implementation, or another issue that prevents unambiguous implementation, the implementation agent MUST stop implementation and report the problem.

The implementation agent MUST NOT resolve specification inconsistencies by inventing requirements or making product, game design, visual design, architecture, content, or other unspecified decisions.

## 3. Behavior Preservation and Refactoring

The implementation agent MUST NOT change existing project behavior unless that behavior change is explicitly required by the specification or by an updated project standard.

Functionality and behavior outside the scope of the specification MUST remain unchanged.

The implementation agent MAY perform refactoring without explicit authorization when the refactoring is useful for implementing the specification or maintaining the affected code.

Refactoring performed without an explicit refactoring requirement MUST preserve existing externally observable behavior and MUST NOT introduce new functionality.

The implementation agent MUST NOT use refactoring as justification for making product, game design, visual design, architectural behavior, or other functional changes that are not required by the specification.

If a proposed refactoring would require changing existing behavior, the implementation agent MUST NOT perform that behavioral change unless it is explicitly required.

Unrelated refactoring SHOULD NOT be performed.

## 4. Dependency Management

The implementation agent MUST NOT introduce a new third-party library, framework, package, plugin, SDK, or other external dependency unless that dependency is explicitly required by the specification.

Libraries, modules, APIs, tools, and functionality already part of the project's established Unreal Engine, C++ standard library, Windows platform facilities, toolchain, or existing dependency set are not new external dependencies.

If a new external dependency is necessary but not explicitly required, the implementation agent MUST stop and report it.

If a new external dependency is optional but materially useful, the implementation agent MAY stop and propose it, including:

- its purpose;
- benefits;
- risks;
- maintenance cost;
- licensing implications;
- dependency-free alternative;
- implementation differences.

The dependency MUST NOT be introduced until it is explicitly authorized.

## 5. Portability and Project Paths

Implementation MUST NOT depend on machine-specific or developer-specific absolute filesystem paths unless a specification explicitly requires such a path for a valid product reason.

Unreal module includes and source/header organization MUST use structures and include paths valid for the project and the Unreal Build Tool.

Local developer directory layout MUST NOT be required for the project to compile, package, test, or run.

User-data filesystem locations MUST use the canonical project paths and platform mechanisms defined by `PROJECT_STANDARD.md`.

## 6. Logging

The implementation agent MUST use the Lord Simulator project logging framework for specification-required Lord Simulator game logging.

Only Lord Simulator game logs use that framework. General Unreal Engine logs remain separate and MUST NOT be substituted, duplicated, redirected, or captured as Lord Simulator game logging.

The implementation agent MUST NOT add Lord Simulator log entries not explicitly defined by the specification or already required by `PROJECT_STANDARD.md`.

New required entries MUST use the exact logging mode and exact English message defined by the specification.

If a new log is necessary for correct implementation but is unspecified, the implementation agent MUST stop and report it.

The implementation agent MAY propose an additional log, including:

- the exact condition;
- its usefulness;
- recommended `Default` or `Development` mode;
- the exact English message.

The proposed log MUST NOT be implemented until explicitly required.

The implementation agent MUST preserve the logging modes, file behavior, formatting, lifecycle, and failure behavior defined by `PROJECT_STANDARD.md`.

## 7. Settings

The implementation agent MUST use the canonical Lord Simulator settings framework defined by `PROJECT_STANDARD.md`.

Every setting in the Lord Simulator settings object MUST have a default value explicitly defined by the specification introducing it or by the project standard if the setting already exists.

Adding a setting to the settings object or persistent settings file MUST be explicitly required by a specification.

A new setting MUST participate in the complete in-memory and persistent settings state unless the specification explicitly changes the architecture and the project standard has been updated accordingly.

The implementation agent MUST NOT create a setting-specific persistence file, independent disk reload, independent save lifecycle, or immediate-save path unless explicitly required.

The implementation agent MUST preserve the complete-state load, validation, comparison, and persistence behavior defined by `PROJECT_STANDARD.md`.

## 8. Localization

The implementation agent MUST use the Lord Simulator localization architecture defined by `PROJECT_STANDARD.md`.

Lord Simulator localization MUST use Unreal Engine localization facilities.

The implementation agent MUST NOT introduce:

- a parallel translation engine;
- a custom translation parser;
- a custom translation file format;
- a custom feature-level translation lookup system;
- an independent active-language state;
- a feature-specific localization manager;
- a custom Lord Simulator localization refresh event system;
- runtime localization hot reload;
- external translation loading;
- localization file watching;
- a new localization target;
- a new canonical String Table;
- Blueprint-accessible localization APIs;

unless explicitly required by a specification and reflected in the project standard where the change is project-wide.

User-facing localizable text MUST use Unreal Engine localization-aware text facilities, including `FText`, preserving Unreal's normal localization behavior.

Localizable text MUST remain localization-aware throughout its UI lifetime. It MUST NOT be converted or cached as `FString` or other static non-localized text in a way that prevents properly implemented UI from reflecting a successful runtime language change.

Dynamic localized user-facing text MUST use localization-aware `FText` formatting.

Localization keys MUST NOT be generated from runtime values.

Localizable text MUST NOT be assembled through English-specific string concatenation or equivalent localization-bypassing logic.

Numbers, pluralization, dates, times, currencies, percentages, and other culture-sensitive user-facing values MUST use Unreal localization-aware formatting where applicable.

Localized text and translations MUST be stored and managed through Unreal localization resources and MUST NOT be embedded in C++, Blueprints, widgets, or feature logic unless explicitly required.

The implementation agent MUST use localization keys exactly as specified and MUST NOT invent keys, native English source text, translations, tooltips, accessibility text, or other player-facing content.

Existing localization keys MUST NOT be renamed, removed, or repurposed unless explicitly required.

A key MAY be reused only for the same semantic meaning. Identical English wording alone does not establish identical semantics.

Changing native English source wording while preserving semantic meaning MUST NOT by itself change the localization key.

The implementation agent MUST NOT invent or automatically rewrite translations when English source text changes.

Project logs, developer diagnostics, internal identifiers, and technical error information remain non-localized unless explicitly required.

Systems that create, cache, format, or display localizable user-facing text MUST respect the localization startup phase defined by `PROJECT_STANDARD.md`.

Feature code, including C++ and Blueprints, MUST NOT directly modify Unreal's active game language or locale. Application-wide language/locale changes go through the Lord Simulator localization framework unless explicitly required otherwise.

## 9. Testing

When a specification requires automated testing, the implementation agent MUST use Unreal Engine's built-in automation testing facilities unless an external testing dependency is explicitly required.

The implementation agent MUST NOT introduce an external test framework merely for convenience.

Automated tests MUST be deterministic where technically practical.

Environment-dependent behavior SHOULD use an internal test seam when deterministic testing requires control over success/failure outcomes.

A test seam MUST NOT:

- create a second production implementation;
- create a second production registry or source of truth;
- alter normal production behavior;
- require a new external mocking dependency unless explicitly required.

Tests MAY use isolated test-only fixtures or in-memory data when required.

Test-only fixtures MUST NOT:

- become production-supported content;
- modify authoritative production configuration;
- modify canonical production assets;
- be packaged as production resources unless explicitly required.

Automated tests do not replace platform, packaging, installer, cooked-resource, or other environment-specific verification that cannot be reliably validated inside the automation test environment.

When a specification affects an existing subsystem with established automated tests, the implementation agent MUST keep those tests passing unless the specification explicitly changes the tested behavior.

## 10. Build and Verification

Implementation MUST preserve the project's ability to build the standard targets defined by `PROJECT_STANDARD.md` unless the specification explicitly changes the supported build baseline.

When a specification affects build configuration, packaging, cooking, localization resources, installer behavior, platform-dependent code, or another build-sensitive area, the implementation agent MUST perform or provide the required verification defined by the specification and project standard.

Build fixes MUST NOT rely on machine-specific absolute include paths, local-only environment assumptions, or developer-specific directory structures.

## 11. Project Build Documentation

The implementation agent is responsible for maintaining `README.md` in the game project root.

`README.md` MUST contain complete instructions for building the project from the repository and producing an installation file that can be installed.

Whenever implementation changes:

- build steps;
- packaging steps;
- dependencies;
- prerequisites;
- tooling;
- localization gather/compile steps;
- automated-test commands required by a specification;
- verification commands required to produce a valid installation;
- installer creation;
- another step required to produce or verify the installation file;

the implementation agent MUST update `README.md` as part of the same work.

Documentation MUST describe the actual implemented workflow rather than an intended or obsolete workflow.

## 12. Project Lifecycle Integration

The implementation agent MUST preserve the canonical startup and shutdown lifecycle defined by `PROJECT_STANDARD.md`.

A subsystem MUST NOT initialize earlier or shut down later than permitted by the project lifecycle merely for implementation convenience.

If a specification introduces a subsystem that requires a new global startup or shutdown ordering relationship, that relationship MUST be explicitly defined by the specification and the project standard MUST be updated before implementation proceeds.

A failure state MUST NOT permanently block unrelated application initialization or shutdown unless the specification explicitly requires that behavior.

## 13. Git Branches

The implementation agent MUST NOT work directly on `development` or `master`.

Before starting implementation, the implementation agent MUST create and work on a dedicated branch for the specification.

The branch name MUST follow:

`type/name`

where:

- `type` is taken from the specification's Type section;
- `name` is taken from the specification filename without the `spec-###-` prefix and without the `.md` extension.

Example:

- Specification: `spec-001-basic-window.md`
- Type: `feature`
- Branch: `feature/basic-window`

The specification SHOULD NOT hard-code the derived branch name.

If the specification filename does not conform to `SPEC_STANDARD.md` and therefore prevents deterministic branch derivation, implementation MUST stop and report the inconsistency.

## 14. No Unrequested Repository or Standards Changes

The implementation agent MUST NOT modify specifications, standards, unrelated documentation, or repository policy merely to make implementation easier unless the task explicitly requires those changes.

If successful implementation requires changing a project standard, that requirement MUST be resolved explicitly before implementation proceeds.
