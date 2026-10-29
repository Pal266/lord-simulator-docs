# Specification Writing Standard

## File Format

Every specification MUST be stored as a Markdown (`.md`) file.

## File Naming

Specification file names MUST follow this pattern:

`spec-001-short-meaningful-name.md`

The specification number MUST use three digits with leading zeros.

Examples:

* `spec-001-...`
* `spec-002-...`
* `spec-010-...`
* `spec-100-...`

The name MUST be short and meaningful enough to identify the purpose of the specification.

## Specification Isolation

A single specification MUST contain everything necessary to implement the feature, fix the bug, perform the refactoring, create the documentation, or complete the analysis described by that specification.

A specification MUST be isolated and self-contained.

A specification MUST NOT depend on or link to another specification.

An implementation agent MUST be able to complete a specification without reading another specification.

A specification MAY expect functionality that already exists in the codebase. When it does, it MUST describe the expected existing behavior or interface as needed for the current task, without referencing the specification that originally introduced that functionality.

If the required work is too large to be reasonably represented by one isolated specification, the work MUST be represented by an Epic and divided into multiple isolated specifications.

## Implementation Responsibility

The implementation agent is responsible for implementation, not for making game design, visual design, audio design, content, or other creative decisions.

A specification MUST provide all non-code inputs required to implement it, or explicitly identify that those inputs already exist in the project.

Required inputs MAY include, but are not limited to:

* meshes;
* materials;
* textures;
* animations;
* icons;
* illustrations;
* UI assets;
* fonts;
* sounds;
* music;
* custom visual effects assets;
* UI layouts or mockups when visual arrangement matters;
* localization and content text;
* configuration or design data.

Assets do not need to be embedded directly in the specification file. They MAY be supplied alongside the specification as part of the implementation package. The specification MUST clearly identify which supplied assets are required and how they are intended to be used when that is not self-evident.

A specification MAY rely on assets that already exist in the project. It MUST identify the expected existing asset or resource clearly enough for the implementation agent to use it without making a creative decision.

If implementation requires an asset, design decision, visual decision, text, value, or other input that has not been provided and cannot be derived unambiguously from the specification or existing project, the implementation agent MUST NOT invent it. The specification is blocked until the missing input is provided or clarified.

The implementation agent MAY create derived technical assets when they are required by the implementation and do not introduce a design or creative decision.

Examples of derived technical assets MAY include:

* generated collision data;
* engine metadata;
* generated serialization data;
* internal lookup data;
* engine-specific derived resources.

## Dependency Management

Any new third-party library, framework, package, plugin, SDK, or other external dependency required to implement a specification MUST be explicitly required by that specification.

A specification that requires a new external dependency MUST identify the dependency clearly enough for the implementation agent to determine exactly which dependency is authorized.

Libraries, modules, APIs, tools, and functionality that are already part of the project's established engine, language standard library, toolchain, or existing dependency set are not considered new external dependencies.

A specification MUST NOT implicitly require the implementation agent to select a new external dependency.

If implementation cannot be completed without introducing a new external dependency that is not explicitly required by the specification, the specification is blocked until the dependency requirement is provided or the specification is clarified.

## Specification Structure

Every specification MUST contain the following sections in this order:

### 1. Title

A short title describing the specification.

### 2. Type

The specification type.

Currently supported types:

* `feature`
* `analyse`
* `bugfix`
* `documentation`
* `refactoring`

Additional types MAY be introduced later.

### 3. Description

A short, human-readable description explaining what the specification is about and why it was created.

The Description is primarily intended for humans and SHOULD NOT be unnecessarily long.

### 4. Requirements

A list of requirements that MUST be completed within the scope of the specification.

### 5. Acceptance Criteria

A list of criteria used to determine whether the specification has been successfully completed.

Acceptance Criteria MUST only validate requirements defined in the `Requirements` section and MUST NOT introduce additional requirements or functionality.

# Epic Standard

## Purpose

An Epic is used when a piece of work is too large to be represented by a single isolated specification.

An Epic divides the work into multiple specifications.

## File Format

Every Epic MUST be stored as a Markdown (`.md`) file.

## File Naming

Epic file names MUST follow this pattern:

`epic-001-short-meaningful-name.md`

The Epic number MUST use three digits with leading zeros.

## Epic Structure

Every Epic MUST contain the following sections in this order:

### 1. Title

A short title describing the Epic.

### 2. Description

A human-readable description explaining the purpose and scope of the Epic.

### 3. Specs

An ordered list of specifications that MUST be implemented to complete the Epic.

The order of specifications is significant.

Specifications MUST be ordered so they can be implemented from top to bottom without being blocked by a specification appearing later in the list.

If one specification introduces functionality required by another specification, the specification introducing that functionality MUST appear earlier in the list.

A later specification MAY assume that functionality introduced earlier in the Epic already exists in the codebase, but it MUST NOT reference or link to the earlier specification.
