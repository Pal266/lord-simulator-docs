# Implementation Standard

## 1. Specification Scope

The implementation agent MUST implement only the functionality explicitly described in the `Requirements` section of the specification.

The implementation agent MUST NOT implement functionality, features, improvements, refactoring, or other changes that are not required by the specification.

If the specification contains an inconsistency, contradiction, missing information required for implementation, or another issue that prevents unambiguous implementation, the implementation agent MUST stop implementation and report the problem.

The implementation agent MUST NOT resolve specification inconsistencies by inventing requirements or making product, game design, visual design, or other unspecified decisions.

## 2. Dependency Management

The implementation agent MUST NOT introduce a new third-party library, framework, package, plugin, SDK, or other external dependency unless that dependency is explicitly required by the specification.

Libraries, modules, APIs, tools, and functionality that are already part of the project's established engine, language standard library, toolchain, or existing dependency set are not considered new external dependencies.

If the implementation agent determines that a new external dependency is necessary to satisfy the specification, but the dependency is not explicitly required by the specification, the implementation agent MUST stop implementation and report the dependency requirement.

If a new external dependency is not necessary but the implementation agent determines that introducing one could materially improve the project or implementation, the implementation agent MAY stop implementation and propose the dependency.

The implementation agent MUST NOT introduce the proposed dependency unless the specification is subsequently updated to explicitly require it.

When proposing a new external dependency, the implementation agent MUST report:

* the exact library, framework, package, plugin, SDK, or dependency being proposed;
* the purpose for which it would be used;
* why it would improve the project or implementation;
* the relevant disadvantages, risks, maintenance costs, licensing considerations, or additional complexity introduced by the dependency;
* how the specification can be implemented without the dependency, when implementation without it is possible;
* how the implementation would differ if the proposed dependency were authorized.

The decision to introduce a new external dependency belongs to the specification author and MUST NOT be made autonomously by the implementation agent.

## 3. Project Build Documentation

The implementation agent is responsible for maintaining `README.md` in the project root.

`README.md` MUST contain complete instructions for building the project from the repository and producing an installation file that can be installed.

Whenever an implementation changes the build, packaging, dependencies, prerequisites, tooling, or any other step required to produce the installation file, the implementation agent MUST update `README.md` as part of the same work.

## 4. Git Branches

The implementation agent MUST NOT work directly on the `development` or `master` branches.

Before starting implementation, the implementation agent MUST create and work on a dedicated branch for the specification.

The branch name MUST follow this pattern:

`type/name`

Where:

* `type` MUST be taken from the specification's `Type` section.
* `name` MUST be taken from the specification file name.

The specification prefix and number MUST NOT be included in the branch name.

Example:

Specification file:

`spec-001-basic-window.md`

Specification type:

`feature`

Branch:

`feature/basic-window`
