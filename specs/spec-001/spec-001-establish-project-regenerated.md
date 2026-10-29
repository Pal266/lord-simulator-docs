# Establish Lord Simulator Project

## Type

feature

## Description

Establish the initial `Lord Simulator` project and its build, packaging, and installation pipeline. This specification creates the technical baseline required for future development. It does not introduce gameplay functionality.

## Requirements

1. Create a C++ Unreal Engine project using Unreal Engine 5.8.4.
2. Use `Lord Simulator` as the human-facing product and application display name.
3. Use `LordSimulator` as the Unreal project name.
4. Use `LordSimulator` as the primary C++ module name.
5. Use `LordSimulator` and `LordSimulatorEditor` as the Unreal target names where the corresponding game and editor targets are required.
6. Use `lord-simulator` as the repository name.
7. Use `Lord Simulator` as the installation folder name.
8. The packaged game executable MUST be named `LordSimulator.exe`.
9. The Inno Setup installer output MUST be named `LordSimulatorSetup.exe`.
10. Configure the project to use C++20.
11. Configure the project to target 64-bit Windows.
12. The project MUST compile successfully from source.
13. The compiled project MUST launch successfully.
14. Provide only the minimum startup content and configuration required to verify that the Unreal Engine project launches successfully. No gameplay systems, game-specific UI, art, or other game functionality MUST be introduced by this specification.
15. Configure the project so that a Windows x64 packaged build can be produced successfully.
16. Add an Inno Setup installer configuration that packages the Windows x64 packaged build into the installable `LordSimulatorSetup.exe` installer.
17. `LordSimulatorSetup.exe` MUST install `Lord Simulator` on a 64-bit Windows system.
18. The installed copy of `Lord Simulator` MUST launch successfully after installation.
19. Create or update `README.md` in the project root.
20. `README.md` MUST contain complete instructions for producing `LordSimulatorSetup.exe` from the repository, including required software and prerequisites, required versions where applicable, building the Unreal Engine C++ project, producing the Windows x64 packaged build, and using Inno Setup to produce the final installer.
21. The implementation MUST comply with the project implementation standard, including performing the work on the branch `feature/establish-project`.

## Acceptance Criteria

1. The Unreal project is named `LordSimulator` and can be opened with Unreal Engine 5.8.4.
2. The human-facing product/application name is `Lord Simulator`.
3. The primary C++ module is named `LordSimulator`.
4. The project uses the required `LordSimulator` and `LordSimulatorEditor` target names.
5. The repository is named `lord-simulator`.
6. The project is configured to use C++20.
7. The project builds successfully for 64-bit Windows.
8. Launching the compiled project starts `Lord Simulator` successfully.
9. A Windows x64 packaged build can be produced successfully and contains `LordSimulator.exe`.
10. The Inno Setup configuration successfully produces `LordSimulatorSetup.exe`.
11. Running `LordSimulatorSetup.exe` on a 64-bit Windows system installs the application into an installation folder named `Lord Simulator`.
12. Launching the installed `LordSimulator.exe` starts `Lord Simulator` successfully.
13. A `README.md` exists in the project root and contains sufficient instructions to reproduce the complete build, packaging, and installer creation process from the repository.
14. No gameplay systems, game-specific UI, art, or other game functionality has been added as part of this specification.
15. The implementation is performed on the branch `feature/establish-project`.
