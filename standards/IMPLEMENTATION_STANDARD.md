# Implementation Standard

## 1. Specification Scope

The implementation agent MUST implement only the functionality
explicitly described in the `Requirements` section of the specification.

The implementation agent MUST NOT implement functionality, features,
improvements, refactoring, or other changes that are not required by the
specification.

If the specification contains an inconsistency, contradiction, missing
information required for implementation, or another issue that prevents
unambiguous implementation, the implementation agent MUST stop
implementation and report the problem.

The implementation agent MUST NOT resolve specification inconsistencies
by inventing requirements or making product, game design, visual design,
or other unspecified decisions.

## 2. Project Build Documentation

The implementation agent is responsible for maintaining `README.md` in
the project root.

`README.md` MUST contain complete instructions for building the project
from the repository and producing an installation file that can be
installed.

Whenever an implementation changes the build, packaging, dependencies,
prerequisites, tooling, or any other step required to produce the
installation file, the implementation agent MUST update `README.md` as
part of the same work.

## 3. Git Branches

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
