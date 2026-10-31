# Specification Writing Standard

## 1. Purpose

This standard defines how Lord Simulator specifications and Epics MUST be written.

Specifications describe changes to the project. Established project-wide behavior and architecture are defined by `PROJECT_STANDARD.md`, while implementation-agent behavior is defined by `IMPLEMENTATION_STANDARD.md`.

A specification MUST NOT duplicate project-wide requirements that are already defined by the current standards unless the specification intentionally changes those requirements or repetition is necessary to make a requirement unambiguous.

Specification isolation means independence from other specifications. It does not mean independence from the project standards.

## 2. File Format

Every specification MUST be stored as a Markdown (`.md`) file.

## 3. Specification Location and File Naming

Specifications MUST be stored using this structure:

`specs/spec-###/spec-###-short-meaningful-name.md`

The specification number MUST use three digits with leading zeros.

Examples:

- `../specs/specs-001`
- `specs/spec-002/spec-002-logging-framework.md`
- `specs/spec-010/spec-010-language-selection.md`
- `specs/spec-100/spec-100-example.md`

The name MUST be short and meaningful enough to identify the purpose of the specification.

Supporting assets supplied specifically for a specification MAY be stored alongside that specification in its `spec-###` directory.

A specification filename MUST NOT include temporary workflow suffixes such as `-regenerated`, `-final`, `-new`, or version labels unless that wording is genuinely part of the specification's semantic purpose.

## 4. Standards Dependency and Authority

A specification MAY and SHOULD rely on requirements already defined by the current project standards.

An implementation agent is expected to implement a specification together with:

- `SPEC_STANDARD.md`;
- `IMPLEMENTATION_STANDARD.md`;
- `PROJECT_STANDARD.md`.

A specification SHOULD NOT restate established project-wide rules merely to make itself self-contained.

If a specification establishes a new project-wide invariant or intentionally changes an established rule in `PROJECT_STANDARD.md`, the specification MUST explicitly require the corresponding project-standard update.

The required `PROJECT_STANDARD.md` update MAY be completed before implementation when the intended project-wide architecture or behavior is already fully determined. It MAY instead be completed during implementation or after the implementation work when the final authoritative wording depends on technical details established or verified while implementing the specification.

A specification that requires a project-standard update MUST NOT be considered complete until `PROJECT_STANDARD.md` reflects the resulting implemented architecture or behavior and no contradiction remains between the specification, implementation, and project standard.

Until the required project-standard update is completed, the existing `PROJECT_STANDARD.md` remains authoritative for all project-wide behavior that the current specification does not explicitly change. The current specification is authoritative for the project-wide changes it explicitly requires. A temporary mismatch caused only by such an explicit, pending project-standard change is not by itself an inconsistency.

If the intended project-wide change is not defined clearly enough to determine what existing rule is being added, changed, or superseded, or if another unresolved contradiction remains outside the explicitly required change, the specification is inconsistent and implementation MUST stop under `IMPLEMENTATION_STANDARD.md`.

## 5. Specification Isolation

A single specification MUST contain everything specific to the requested change that is necessary to implement the feature, fix the bug, perform the refactoring, create the documentation, or complete the analysis described by that specification.

A specification MUST be isolated from other specifications.

A specification MUST NOT depend on or link to another specification.

An implementation agent MUST be able to complete a specification without reading another specification.

A specification MAY expect functionality that already exists in the codebase or is defined by the project standards. When existing behavior or an existing interface is material to the requested change and is not already sufficiently defined by a project standard, the specification MUST describe the expected behavior or interface needed for the current task without referencing the specification that originally introduced it.

If the required work is too large to be reasonably represented by one isolated specification, the work MUST be represented by an Epic and divided into multiple isolated specifications.

## 6. Implementation Responsibility

The implementation agent is responsible for implementation, not for making game design, visual design, audio design, content, or other creative decisions.

A specification MUST provide all non-code inputs required to implement it, or explicitly identify that those inputs already exist in the project.

Required inputs MAY include, but are not limited to:

- meshes;
- materials;
- textures;
- animations;
- icons;
- illustrations;
- UI assets;
- fonts;
- sounds;
- music;
- custom visual effects assets;
- UI layouts or mockups when visual arrangement matters;
- localization and content text;
- configuration or design data.

Assets do not need to be embedded directly in the specification file. They MAY be supplied alongside the specification as part of the implementation package. The specification MUST clearly identify which supplied assets are required and how they are intended to be used when that is not self-evident.

A specification MAY rely on assets that already exist in the project. It MUST identify the expected existing asset or resource clearly enough for the implementation agent to use it without making a creative decision.

If implementation requires an asset, design decision, visual decision, text, value, or other input that has not been provided and cannot be derived unambiguously from the specification, project standards, or existing project, the implementation agent MUST NOT invent it. The specification is blocked until the missing input is provided or clarified.

The implementation agent MAY create derived technical assets when required by implementation and when doing so introduces no design or creative decision.

Examples include generated collision data, engine metadata, generated serialization data, internal lookup data, and engine-specific derived resources.

## 7. Specification Structure

Every specification MUST use the following Markdown structure and section order:

```md
# Title

<short specification title>

# Type

<type>

# Description

<human-readable description>

# Requirements

1. <requirement>
2. <requirement>

# Acceptance Criteria

1. <criterion>
2. <criterion>
```

The heading text and order MUST be consistent with this structure.

### 7.1 Title

The Title MUST be short and describe the specification.

### 7.2 Type

The Type MUST identify the kind of work.

Currently supported types are:

- `feature`
- `analyse`
- `bugfix`
- `documentation`
- `refactoring`

Additional types MAY be introduced later by updating this standard.

### 7.3 Description

The Description MUST be a short, human-readable explanation of what the specification is about and why it was created.

The Description is primarily intended for humans and SHOULD NOT be unnecessarily long.

The Description MAY explain important scope boundaries, but binding implementation obligations MUST appear in Requirements.

### 7.4 Requirements

Requirements MUST define the complete specification-specific implementation scope.

Requirements MUST be explicit enough that the implementation agent is not required to invent product behavior, architecture, content, assets, text, values, or creative decisions.

Requirements MUST NOT require functionality that contradicts the current project standards unless the relevant project standard is intentionally updated.

Requirements MAY rely on current standards without repeating them.

A requirement that changes global startup order, shutdown order, a canonical project identifier, a canonical path, a persistent setting contract, a localization invariant, or another project-wide architectural invariant MUST explicitly define the intended new behavior and require the corresponding project-standard update as part of completing the specification.

### 7.5 Acceptance Criteria

Acceptance Criteria MUST determine whether the Requirements were completed successfully.

Acceptance Criteria MUST only validate requirements defined in the Requirements section and MUST NOT introduce additional requirements or functionality.

Acceptance Criteria SHOULD be objectively verifiable where practical.

Acceptance Criteria MAY validate project-standard behavior when that behavior is directly affected by the specification, but they SHOULD NOT redundantly retest unrelated project-wide invariants.

When a specification requires a `PROJECT_STANDARD.md` update, its Acceptance Criteria MUST include verification that the project standard reflects the resulting project-wide architecture or behavior before the specification is considered complete.

## 8. Derived Workflow Information

Specifications SHOULD NOT hard-code information that is deterministically derived from the standards unless the specification intentionally changes the derivation rule.

In particular, a specification SHOULD NOT hard-code its implementation branch name when the branch name is already deterministically defined by `IMPLEMENTATION_STANDARD.md`.

If a specification requires an exception to a derived workflow rule, the applicable standard MUST be updated or the exception MUST be otherwise resolved before implementation begins.

## 9. Logging Requirements

When a specification requires a new Lord Simulator project log entry, it MUST define:

- the exact condition or event that triggers the log;
- the required logging mode;
- the exact English log message.

`Default` mode is for concise operational information that is useful in normal builds and normal application operation.

`Development` mode is for additional diagnostic or development information that is useful while developing or investigating the application but is not required as normal operational output.

A specification MUST NOT leave the implementation agent to choose the logging mode or invent the wording of a required Lord Simulator log message.

A specification MUST NOT require a new log entry merely because logging might be useful. The log entry must serve an explicitly defined project requirement.

Existing logging behavior defined by `PROJECT_STANDARD.md` MUST NOT be restated unless the specification modifies or directly validates it.

## 10. Persistent Settings Requirements

When a specification introduces a new persistent setting, it MUST define:

- the exact setting key;
- whether the key is case-sensitive if it differs from the project-wide settings policy;
- the setting's value type or exact allowed value format;
- all valid values or validation rules;
- the exact default value;
- any setting-specific behavior required when the value is missing or invalid;
- any required Lord Simulator log messages, following the Logging Requirements section;
- any runtime behavior triggered by changing the setting.

A specification introducing a persistent setting MUST integrate it into the complete Lord Simulator settings state defined by `PROJECT_STANDARD.md` unless the specification explicitly changes the settings architecture.

A specification MUST NOT introduce an independent settings file, independent persistence lifecycle, immediate-save path, or separate reload path for one setting unless the specification explicitly changes the project architecture and the relevant project standard is updated.

The implementation agent MUST NOT be required to invent a default value for any setting.

## 11. Localization

A specification that introduces user-facing localizable text MUST explicitly define, for every new localization entry:

- the exact localization key;
- the exact native English source text.

The implementation agent MUST NOT be required to invent localization keys, native English source text, translations, or other localization content.

Localization keys MUST use case-sensitive semantic hierarchical names composed of PascalCase segments separated by periods.

Examples:

- `MainMenu.NewGame`
- `Settings.Language`
- `Building.Farm.Description`

Localization keys MUST describe semantic purpose/context and MUST NOT be based on widget class, source file, UI position, row number, or another incidental implementation detail.

A localization key MAY contain any number of semantic hierarchy levels required to identify its purpose.

The native Lord Simulator culture is `en`. A specification MUST NOT remove or replace native `en` unless it explicitly changes the project's localization architecture and all affected localization requirements, and `PROJECT_STANDARD.md` is updated accordingly.

Adding or removing a supported culture MUST be explicitly required by a specification.

A specification adding a supported culture MUST define the exact culture identifier and provide or identify all localization inputs/resources required to implement it, including the expected native display name when that value is part of acceptance and all required translations or translation assets.

A specification introducing user-facing textual content such as visible UI text, tooltips, accessibility text, messages, descriptions, or other player-facing textual metadata MUST identify which text is localizable and provide the required localization inputs.

A specification MUST NOT require the implementation agent to create additional user-facing localization entries, translations, tooltips, accessibility text, or other textual content that the specification does not explicitly define.

Existing localization architecture, canonical resources, culture behavior, and runtime language state are defined by `PROJECT_STANDARD.md` and SHOULD NOT be duplicated in individual specifications unless directly changed or validated by the specification.

## 12. Testing Requirements in Specifications

A specification SHOULD define required automated tests when the new or changed behavior is sufficiently important, complex, stateful, failure-sensitive, or regression-prone that deterministic automated coverage materially improves confidence.

When a specification requires automated tests, it MUST define the behavior that must be covered, not a needlessly specific test class or mocking implementation unless that exact structure is itself required.

A specification MUST NOT require production-only placeholder content, fake production-supported cultures, or other production data solely to enable testing when isolated test fixtures or test seams can satisfy the requirement.

Packaging, installer, platform, resource-inclusion, and other environment-specific verification MUST be listed separately when automated tests cannot fully validate the behavior.

## 13. Epic Standard

### 13.1 Purpose

An Epic is used when a piece of work is too large to be represented by a single isolated specification.

An Epic divides the work into multiple specifications.

### 13.2 File Format

Every Epic MUST be stored as a Markdown (`.md`) file.

### 13.3 File Naming

Epic file names MUST follow this pattern:

`epic-001-short-meaningful-name.md`

The Epic number MUST use three digits with leading zeros.

### 13.4 Epic Structure

Every Epic MUST contain the following sections in this order:

```md
# Title

<short epic title>

# Description

<human-readable description>

# Specs

1. <specification>
2. <specification>
```

### 13.5 Specs Ordering

The Specs section MUST contain an ordered list of specifications required to complete the Epic.

The order of specifications is significant.

Specifications MUST be ordered so they can be implemented from top to bottom without being blocked by a specification appearing later in the list.

If one specification introduces functionality required by another, the specification introducing that functionality MUST appear earlier in the list.

A later specification MAY assume functionality introduced earlier in the Epic already exists in the codebase, but it MUST NOT reference or link to the earlier specification.

Each specification in an Epic remains subject to the same isolation rules as any other specification.
