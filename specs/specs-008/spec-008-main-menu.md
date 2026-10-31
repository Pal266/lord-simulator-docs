# Title

Main Menu

# Type

feature

# Description

Implement the first production Lord Simulator main menu using the existing screen-space UI framework and the approved main-menu visual assets.

The menu is the initial player-facing screen after UI startup. It displays the approved northern-development background and four vertically stacked buttons on the left: `NEW GAME`, `LOAD GAME`, `SETTINGS`, and `QUIT`. Only `QUIT` is enabled in this specification. The other three buttons are intentionally visible but unavailable until future features implement their functionality.

This specification does not implement game creation, save loading, settings UI, menu music, additional screens, or other gameplay systems.

# Requirements

## Approved production assets

1. Use these exact approved visual source assets from the documentation repository as the production inputs for the main menu:

   - background: `visuals/approved/main-menu/main-menu-background-northern-development.png`;
   - normal button: `visuals/approved/main-menu/main-menu-button-normal.png`;
   - hover/focus button: `visuals/approved/main-menu/main-menu-button-hover.png`;
   - pressed button: `visuals/approved/main-menu/main-menu-button-pressed.png`;
   - disabled button: `visuals/approved/main-menu/main-menu-button-disabled.png`.

2. The approved source assets MUST NOT be visually redesigned, repainted, recolored, cropped, stretched non-uniformly, regenerated, or replaced during implementation.

3. Import the approved background into the game as an Unreal texture at exactly:

   `/Game/UI/Textures/MainMenu/T_MainMenuBackground`

4. Import the four approved button textures into the game at exactly:

   - `/Game/UI/Textures/MainMenu/T_MainMenuButtonNormal`;
   - `/Game/UI/Textures/MainMenu/T_MainMenuButtonHover`;
   - `/Game/UI/Textures/MainMenu/T_MainMenuButtonPressed`;
   - `/Game/UI/Textures/MainMenu/T_MainMenuButtonDisabled`.

5. Preserve the source image dimensions and alpha data where present. The imported textures MUST use normal Unreal UI-texture handling suitable for screen-space UMG, including sRGB color and UI-oriented texture/compression settings. Button transparency MUST remain intact.

6. The main-menu background MUST use the approved visual direction in `visuals/style/main-menu/main-menu-background-direction.md` only as style guidance. The exact production image required by this specification is the approved background identified in requirement 1.

## Main-menu widget and UI-framework integration

7. Implement a C++ main-menu widget class named exactly:

   `ULordSimulatorMainMenuWidget`

8. `ULordSimulatorMainMenuWidget` MUST derive from the existing `ULordSimulatorActivatableWidget` base and MUST use the existing Lord Simulator `Menu` layer rather than creating another viewport root, UI manager, or independent menu stack.

9. Create the production Widget Blueprint at exactly:

   `/Game/UI/Screens/MainMenu/WBP_MainMenu`

10. `WBP_MainMenu` MUST derive from `ULordSimulatorMainMenuWidget`.

11. C++ MUST own the technical menu behavior, activation behavior, and quit command. The Widget Blueprint MUST own the production layout and references to the supplied visual assets.

12. The main menu MUST fill the complete local-player viewport through the existing primary UI root.

13. When the Lord Simulator UI root becomes available after localization startup has completed, the application MUST push exactly one `WBP_MainMenu` instance onto the canonical `Menu` layer as the initial production screen.

14. Repeated or duplicate UI/startup initialization MUST NOT create multiple main-menu instances or leave duplicate `WBP_MainMenu` widgets in the `Menu` stack.

15. Failure to create or push the main menu MUST fail safely without intentionally crashing the application. Unreal technical diagnostics MAY be used. This specification MUST NOT add a new Lord Simulator project log entry for main-menu initialization.

16. Activating or displaying the main menu MUST NOT pause, unpause, slow, accelerate, or otherwise change simulation/game time.

17. The main menu MUST use the existing CommonUI/menu-oriented input routing and focus behavior. It MUST NOT introduce a parallel custom focus stack or another input-routing framework.

## Background presentation

18. Display `T_MainMenuBackground` behind all main-menu controls.

19. The background MUST fill the visible viewport without letterboxing and without non-uniform distortion.

20. When the viewport aspect ratio differs from the source image aspect ratio, the implementation MUST preserve the image aspect ratio and MAY crop excess image area as required to fill the viewport.

21. Background cropping MUST remain centered and MUST NOT reposition the image separately for individual resolutions.

22. The background MUST NOT contain or receive additional button art, labels, heraldry, logos, overlays, gradients, decorative frames, color tints, or other production visual additions in this specification.

## Menu layout

23. Display exactly four menu buttons in this top-to-bottom order:

   1. `NEW GAME`;
   2. `LOAD GAME`;
   3. `SETTINGS`;
   4. `QUIT`.

24. The four buttons MUST use one vertical stack anchored to the left side of the viewport and vertically centered as a group.

25. At the `1920x1080` reference viewport before normal Unreal DPI scaling, the button stack MUST use:

   - left offset from the viewport: `80` Slate units;
   - button desired size: `400 x 179` Slate units;
   - vertical space between consecutive button slots: `8` Slate units.

26. The layout MUST use anchors/containers and the existing Unreal DPI-scaling behavior so the stack remains fully visible and usable at minimum at these viewport sizes:

   - `1280x720`;
   - `1920x1080`;
   - `2560x1440`;
   - `3440x1440`;
   - `3840x2160`.

27. This specification MUST NOT introduce a new DPI curve, UI-scale setting, safe-zone policy, or resolution-specific alternate layout.

28. Do not add a game title, logo, version label, copyright text, tooltip, footer, decorative panel behind the button stack, additional controls, or any other player-facing main-menu element.

## Button presentation

29. Use one centralized main-menu button presentation/style configuration so all four buttons use the same approved state artwork rather than duplicating independent visual-state definitions.

30. Map button states to the approved textures exactly as follows:

   - enabled normal state -> `T_MainMenuButtonNormal`;
   - enabled pointer-hover or keyboard-focus state -> `T_MainMenuButtonHover`;
   - enabled pressed state -> `T_MainMenuButtonPressed`;
   - disabled state -> `T_MainMenuButtonDisabled`.

31. The approved button textures MUST be displayed without an additional tint that materially changes their artwork.

32. Button labels MUST be centered horizontally and vertically over the textless button textures.

33. Use Unreal Engine's existing built-in Roboto Regular font for the four button labels. Do not add a new font asset in this specification.

34. At the `1920x1080` reference viewport before normal Unreal DPI scaling, button labels MUST use a font size of `32` Slate units.

35. Button-label colors MUST be:

   - enabled normal: `#E7D9B8`;
   - enabled hover/focus: `#FFF0C7`;
   - enabled pressed: `#D8B56C`;
   - disabled: `#777777`.

36. Do not add a label text shadow, outline, glow, animation, or other additional text effect.

## Localization

37. Add these exact entries to the canonical Lord Simulator String Table and use them for the visible button labels:

   - key `MainMenu.NewGame`, native English source text `NEW GAME`;
   - key `MainMenu.LoadGame`, native English source text `LOAD GAME`;
   - key `MainMenu.Settings`, native English source text `SETTINGS`;
   - key `MainMenu.Quit`, native English source text `QUIT`.

38. The four visible labels MUST remain localization-aware `FText` through their UI lifetime and MUST follow the existing Lord Simulator localization architecture.

39. Do not introduce additional main-menu localization entries, tooltips, explanatory text, status text, accessibility text, or translations in this specification.

## Button availability and behavior

40. `NEW GAME`, `LOAD GAME`, and `SETTINGS` MUST be visible but disabled.

41. The three disabled buttons MUST use the disabled visual state continuously and MUST NOT react visually to pointer hover.

42. The three disabled buttons MUST NOT receive keyboard focus, trigger click/activation behavior, execute commands, open placeholder screens, display placeholder messages, or otherwise simulate unavailable functionality.

43. `QUIT` MUST be the only enabled button.

44. `QUIT` MUST support the normal, hover/focus, and pressed visual states defined in this specification.

45. When the main menu becomes active, keyboard focus MUST initially resolve to `QUIT` because it is the only actionable control.

46. Activating `QUIT` by supported UI activation, including pointer click or keyboard activation while focused, MUST request a normal Unreal application quit through an engine/platform mechanism that permits the existing Lord Simulator shutdown lifecycle to execute.

47. The quit implementation MUST NOT use forced process termination or another mechanism that intentionally bypasses the canonical shutdown log, settings comparison/persistence, or normal application/module shutdown.

48. In a packaged Windows build, activating `QUIT` MUST close the Lord Simulator application.

49. In Unreal Editor PIE, activating `QUIT` MUST end the PIE play session and MUST NOT intentionally terminate the Unreal Editor process.

50. `QUIT` MUST NOT display a confirmation dialog in this specification.

## Scope boundaries

51. Do not implement `NEW GAME` functionality, campaign creation, map selection, character creation, or game-start flow.

52. Do not implement save discovery, save loading, save metadata, or a `LOAD GAME` screen.

53. Do not implement a settings screen or new persistent settings.

54. Do not add music, ambient audio, button sounds, animations, video backgrounds, particle effects, background motion, or other new presentation systems.

55. Do not introduce gamepad-specific navigation data, controller glyphs, input rebinding, or new input mappings.

56. Do not introduce a third-party UI, font, audio, image, or other dependency.

57. Do not add any Lord Simulator project log message as part of this feature.

## Project-standard update

58. Update `PROJECT_STANDARD.md` to record the resulting project-wide startup UI invariant that, after localization startup is complete and the primary UI root is successfully available, Lord Simulator presents one main-menu screen on the canonical `Menu` layer as the initial production player-facing screen.

59. The project-standard update MUST preserve the existing localization-before-player-facing-UI ordering and MUST NOT duplicate feature-specific visual values, asset names, button labels, or other presentation details that belong only to this specification.

## Verification and tests

60. Add or update Unreal Automation coverage sufficient to verify deterministic main-menu behavior without terminating the automation process, including at minimum:

   - the main-menu widget is compatible with the canonical `Menu` layer;
   - startup/main-UI initialization does not create more than one main-menu instance;
   - `NEW GAME`, `LOAD GAME`, and `SETTINGS` are disabled and non-focusable;
   - `QUIT` is enabled and focusable;
   - the main-menu widget resolves the four required localization entries;
   - the configured button-state presentation references the required imported main-menu textures.

61. Automated tests MUST NOT actually terminate the editor, test runner, or application process merely to verify quit behavior.

62. Build and verify the standard `LordSimulatorEditor` Win64 Development target after implementation.

63. Keep all existing Lord Simulator automation tests passing.

64. Verify the menu layout in editor or equivalent runtime UI verification at all viewport sizes listed in requirement 26. At each size:

   - the background fills the viewport without visible letterboxing or non-uniform distortion;
   - the complete four-button stack remains visible;
   - button labels remain centered and readable;
   - `NEW GAME`, `LOAD GAME`, and `SETTINGS` are visibly unavailable;
   - `QUIT` remains visibly actionable;
   - no unintended additional UI is displayed.

65. Build/package the standard Win64 Shipping game and verify that all five approved main-menu source visuals have corresponding cooked/imported Unreal assets available at runtime.

66. Launch the packaged Windows build and verify that the main menu appears as the initial player-facing screen and that activating `QUIT` closes the application through the normal Lord Simulator shutdown lifecycle.

# Acceptance Criteria

1. The production main menu is implemented as `WBP_MainMenu` derived from `ULordSimulatorMainMenuWidget` and is presented through the existing canonical `Menu` layer.

2. Startup presents at most one main-menu instance after localization startup and primary UI-root availability, with no competing viewport root or menu manager.

3. The exact approved background and four approved button source assets are imported at the Unreal asset paths required by this specification and no unapproved substitute production artwork is used.

4. The background fills supported viewport shapes without letterboxing or non-uniform distortion, preserving aspect ratio with centered cropping where necessary.

5. The menu displays exactly `NEW GAME`, `LOAD GAME`, `SETTINGS`, and `QUIT` in the required left-side vertical layout and order.

6. The button stack remains fully visible at `1280x720`, `1920x1080`, `2560x1440`, `3440x1440`, and `3840x2160` using the existing Unreal DPI-scaling behavior.

7. Button state artwork uses the exact normal, hover/focus, pressed, and disabled textures specified in the Requirements.

8. Button typography, font size, label colors, alignment, and absence of extra text effects match the Requirements.

9. The canonical String Table contains `MainMenu.NewGame`, `MainMenu.LoadGame`, `MainMenu.Settings`, and `MainMenu.Quit` with the exact native English source text specified, and the visible labels use localization-aware text.

10. `NEW GAME`, `LOAD GAME`, and `SETTINGS` are visible, disabled, non-focusable, do not react to hover, and perform no action.

11. `QUIT` is the only enabled/actionable control, receives initial keyboard focus, and uses the required normal, hover/focus, and pressed presentation states.

12. Activating `QUIT` in the packaged Windows game closes the application through a normal Unreal quit path that preserves the canonical Lord Simulator shutdown lifecycle.

13. Activating `QUIT` in PIE ends the PIE session without intentionally terminating Unreal Editor.

14. No New Game flow, load-game system, settings screen, confirmation dialog, title/logo, additional main-menu control, music, sound effect, animation, new input mapping, new persistent setting, third-party dependency, or new Lord Simulator project log entry is introduced.

15. Required automated main-menu tests pass and all previously existing Lord Simulator automation tests continue to pass.

16. The standard `LordSimulatorEditor` Win64 Development build succeeds after implementation.

17. The standard Win64 Shipping packaged build includes the required main-menu assets, launches successfully, shows the main menu first, and exits successfully through `QUIT`.

18. `PROJECT_STANDARD.md` is updated before the specification is considered complete and accurately records the resulting initial-main-menu startup invariant without duplicating feature-specific presentation details.
