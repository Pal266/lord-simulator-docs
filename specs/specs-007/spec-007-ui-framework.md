# Title

UI Framework

# Type

feature

# Description

Establish the Lord Simulator screen-space UI framework for future city-builder, management, RPG, menu, and modal interfaces.

The framework uses Unreal Motion Graphics (UMG) as the primary UI authoring system and uses CommonUI selectively where its activation, focus, layered-menu, and input-routing behavior is useful. It establishes one authoritative screen-space UI root, reusable C++ widget bases, UI-layer behavior, event-driven data-flow rules, performance requirements, and automated tests.

This specification establishes technical UI infrastructure only. It does not introduce a production HUD, main menu, settings screen, building panel, inventory, tooltip design, notification design, fonts, icons, textures, animations, sounds, final colors, spacing, or other visual/content design.

# Requirements

## UI technology and project configuration

1. Use Unreal Motion Graphics (UMG) as the primary Lord Simulator screen-space UI authoring system.

2. Enable and use Unreal Engine 5.8 CommonUI for the parts of the Lord Simulator UI that benefit from activatable-widget lifecycle, focus restoration, layered menu/modal presentation, and CommonUI input routing.

3. CommonUI MUST be used selectively. Ordinary gameplay HUD elements, context panels, passive informational elements, and other widgets that do not need CommonUI activation/input-routing semantics MUST NOT be forced to derive from `UCommonActivatableWidget`.

4. Configure the game viewport to use `UCommonGameViewportClient`, or a Lord Simulator subclass of `UCommonGameViewportClient` only if a project-specific subclass is technically required.

5. Add only the Unreal Engine modules required to implement the framework, including UMG/CommonUI/Slate modules where required by the implementation.

6. Do not introduce any third-party UI framework, library, plugin, package, SDK, or dependency.

7. Do not enable or adopt Unreal Engine's Model-View-ViewModel (`ModelViewViewModel` / UMG Viewmodel) plugin as the Lord Simulator UI architecture in this specification.

8. Do not enable or adopt Unreal Engine's Experimental `UIFramework` plugin in this specification.

9. Do not enable or establish CommonUI's Enhanced Input integration, UI Input Actions, UI Input Mapping Contexts, key-remapping UI, or a general input-binding framework in this specification. Future input specifications may introduce those systems explicitly.

10. Do not replace UMG/CommonUI with direct Slate-only implementation for ordinary production game UI. Slate MAY be used internally where required by UMG/CommonUI or for a narrowly justified custom widget implementation.

## Authoritative UI ownership

11. Implement one Lord Simulator UI subsystem per local player using a `ULocalPlayerSubsystem`.

12. Name the subsystem class exactly:

    `ULordSimulatorUISubsystem`

13. `ULordSimulatorUISubsystem` MUST be the authoritative owner/access point for Lord Simulator production screen-space UI associated with its local player.

14. The subsystem MUST maintain at most one active primary UI root for its local player.

15. Production screen-space Lord Simulator widgets MUST be attached through the primary UI root and its defined layers rather than independently calling `AddToViewport` or otherwise creating competing top-level Lord Simulator viewport roots.

16. Engine-owned debug UI, Unreal Editor UI, Unreal development tools, and other non-Lord-Simulator production UI are outside requirement 15.

17. World-space UI rendered through `UWidgetComponent` or another world-space mechanism is outside the screen-space UI framework established by this specification and MUST NOT be routed through CommonUI layer/input behavior merely to reuse the screen-space framework.

18. This specification MUST NOT introduce a second global UI manager, competing viewport UI root, or feature-specific screen-space UI manager.

## Base widget classes

19. Implement a reusable C++ base class named exactly:

    `ULordSimulatorUserWidget`

20. `ULordSimulatorUserWidget` MUST derive from `UCommonUserWidget`.

21. `ULordSimulatorUserWidget` is the default C++ base for Lord Simulator screen-space widgets that do not require activatable lifecycle/input-routing semantics.

22. Implement a reusable C++ base class named exactly:

    `ULordSimulatorActivatableWidget`

23. `ULordSimulatorActivatableWidget` MUST derive from `UCommonActivatableWidget`.

24. `ULordSimulatorActivatableWidget` is the default C++ base for Lord Simulator screens, menus, dialogs, or other widgets that need CommonUI activation/deactivation, focus, back-navigation, or input-routing behavior.

25. Neither base class MUST introduce Tick-based data synchronization.

26. Future subclasses MAY add Tick behavior only when explicitly required by the specification introducing that widget and when the behavior cannot reasonably be event-driven.

27. The base classes MUST NOT contain production-specific colors, fonts, textures, icons, sounds, text, layout dimensions, or other visual design decisions.

## Primary UI root

28. Implement a C++ primary-root base class named exactly:

    `ULordSimulatorPrimaryUILayout`

29. `ULordSimulatorPrimaryUILayout` MUST derive from `ULordSimulatorActivatableWidget`.

30. Create one technical Widget Blueprint asset derived from `ULordSimulatorPrimaryUILayout` at exactly:

    `/Game/UI/Framework/WBP_LordSimulatorPrimaryUILayout`

31. `WBP_LordSimulatorPrimaryUILayout` MUST contain no player-facing text, final art, placeholder production art, decorative styling, production fonts, sounds, or animations.

32. The root layout MUST fill the local player's viewport and act only as the technical container for the Lord Simulator screen-space UI layers established by this specification.

33. `ULordSimulatorUISubsystem` MUST create and attach `WBP_LordSimulatorPrimaryUILayout` for its local player when UI initialization is requested after the prerequisites in this specification are satisfied.

34. Repeated initialization requests while a valid root already exists MUST be idempotent and MUST NOT create a duplicate root.

35. The subsystem MUST expose an unambiguous way for feature code to determine whether the primary UI root is available.

36. The subsystem MUST expose the layer operations required by this specification without requiring feature code to know or manipulate the root's internal widget hierarchy directly.

## Initialization and localization lifecycle

37. Lord Simulator player-facing screen-space UI initialization MUST occur only after the localization startup phase defined by `PROJECT_STANDARD.md` has completed.

38. The UI framework MUST NOT create, cache, format, or display player-facing localizable text before the localization startup phase is complete.

39. UI initialization MAY wait for both the owning local player and its game viewport to be available.

40. Failure to create the primary UI root MUST NOT intentionally crash the application.

41. A failed UI-root creation attempt MUST return or expose failure unambiguously to the caller/subsystem state and MAY use Unreal Engine technical logging for diagnostics.

42. This specification MUST NOT introduce a new Lord Simulator project log entry for UI initialization.

## Screen-space UI layers

43. The primary UI root MUST provide exactly these four canonical screen-space layers, ordered from lowest to highest visual priority:

    1. `Game`
    2. `Menu`
    3. `Modal`
    4. `PassiveOverlay`

44. The canonical layer names in requirement 43 MUST be represented in C++ by one project-owned strongly typed identifier mechanism. An enum is acceptable. Feature code MUST NOT depend on arbitrary string literals to select canonical layers.

45. The `Game` layer MUST support multiple simultaneously visible child widgets.

46. The `Game` layer is intended for persistent or context-sensitive gameplay UI such as future resource bars, time controls, construction controls, selected-building panels, selected-character panels, management panels, and other city-builder/RPG gameplay interface elements.

47. Adding a widget to the `Game` layer MUST NOT by itself globally block normal game/world input.

48. A `Game`-layer widget MAY handle pointer/keyboard input directed to that widget, but unhandled input outside the widget MUST remain available to gameplay according to the game's input system.

49. Opening or closing a `Game`-layer widget MUST NOT automatically pause, unpause, slow, or otherwise modify simulation/game time.

50. The `Menu` layer MUST use a `UCommonActivatableWidgetStack`, or an equivalent CommonUI activatable container whose behavior satisfies all requirements in this section.

51. Only the top `Menu` widget MUST be displayed/active within the `Menu` stack.

52. Activating a `Menu` widget MUST establish UI/menu-oriented input behavior that prevents normal gameplay/world commands from being processed while that menu is the active routed UI.

53. Deactivating/removing the top `Menu` widget MUST restore the previous active CommonUI/input state according to the remaining UI hierarchy.

54. Opening or closing a `Menu` widget MUST NOT automatically pause, unpause, slow, or otherwise modify simulation/game time. A future feature specification MAY explicitly couple a particular menu to simulation time.

55. The `Modal` layer MUST use a `UCommonActivatableWidgetStack`, or an equivalent CommonUI activatable container whose behavior satisfies all requirements in this section.

56. The `Modal` layer MUST render above `Menu` and `Game`.

57. Only the top `Modal` widget MUST be displayed/active within the `Modal` stack.

58. While a `Modal` widget is active, it MUST receive routed UI interaction ahead of lower layers and lower-layer Lord Simulator UI MUST NOT be interactable through it.

59. While a `Modal` widget is active, normal gameplay/world commands MUST be blocked.

60. Removing/deactivating the top modal MUST restore interaction to the next valid underlying modal/menu/game state through the CommonUI hierarchy rather than manually reconstructing unrelated widgets.

61. Opening or closing a modal MUST NOT automatically pause, unpause, slow, or otherwise modify simulation/game time unless the specification introducing that modal explicitly requires it.

62. The `PassiveOverlay` layer MUST render above `Modal`, `Menu`, and `Game`.

63. The `PassiveOverlay` layer MUST support multiple simultaneous child widgets.

64. The `PassiveOverlay` layer MUST be hit-test/input transparent for itself and its children.

65. `PassiveOverlay` is intended only for future non-interactive transient visual UI such as passive notifications, visual indicators, or similar overlays.

66. An interactive notification, dialog, tooltip interaction, or other input-receiving UI MUST NOT be placed in `PassiveOverlay`; it must use an appropriate interactive layer.

67. Tooltips MUST NOT be implemented as activatable widgets solely to display temporary hover information.

## Layer API and widget lifecycle

68. `ULordSimulatorUISubsystem` MUST expose operations, without prescribing exact public function names, that allow feature code to:

    - add a widget to `Game`;
    - remove a widget from `Game`;
    - push an activatable widget onto `Menu`;
    - remove/pop the active `Menu` widget;
    - push an activatable widget onto `Modal`;
    - remove/pop the active `Modal` widget;
    - add a widget to `PassiveOverlay`;
    - remove a widget from `PassiveOverlay`.

69. The layer API MUST return created widget references or an equivalent usable result when creation succeeds.

70. Layer operations MUST fail safely and unambiguously when the root does not exist, the requested class is incompatible with the target layer, creation fails, or another required prerequisite is unavailable.

71. `Menu` and `Modal` push operations MUST accept only classes compatible with `ULordSimulatorActivatableWidget`.

72. `Game` and `PassiveOverlay` operations MUST accept classes compatible with `ULordSimulatorUserWidget`, including compatible activatable subclasses when a future feature has an explicit reason to use one.

73. Removing a widget through the subsystem MUST clean up the framework's ownership/reference to that widget and MUST NOT leave stale framework references.

74. The framework MUST NOT assume that a gameplay feature has only one context panel, one HUD element, or one passive overlay at a time.

## Input-routing policy

75. The primary UI root MUST provide a baseline CommonUI input configuration compatible with simultaneous gameplay and UI interaction when no `Menu` or `Modal` screen is active.

76. The baseline configuration MUST permit future city-builder/RPG gameplay to use mouse-driven screen-space UI without forcing the entire application into UI-only mode.

77. `Menu` and `Modal` activatable widgets MUST be able to override the baseline input configuration through CommonUI activation.

78. The framework MUST rely on CommonUI input routing/focus restoration for activatable menu/modal hierarchy rather than creating a parallel custom focus stack.

79. This specification MUST NOT implement gamepad-specific cardinal navigation rules, controller glyphs, key rebinding, input-action prompts, or a complete keyboard shortcut framework.

80. The framework architecture MUST NOT prevent those capabilities from being added later through CommonUI or Unreal's input systems.

## UI data flow and authoritative state

81. Gameplay/simulation systems remain authoritative for gameplay state displayed by UI.

82. UI widgets MUST NOT become an independent authoritative copy of simulation state merely because that state is displayed.

83. UI-local ephemeral presentation state MAY remain owned by widgets when appropriate, including examples such as scroll position, currently selected visual tab, expanded/collapsed presentation state, or transient animation state.

84. Production UI data updates MUST be event-driven where practical.

85. Production widgets MUST NOT use raw UMG property/function bindings that poll gameplay values every frame.

86. Production widgets MUST NOT use `Tick`, `NativeTick`, `OnPaint`, or equivalent per-frame work merely to poll whether gameplay data changed.

87. Gameplay/system changes that affect UI SHOULD update UI through explicit events, delegates, notifications, or direct update calls at the time relevant state changes.

88. UI commands that change gameplay state MUST call explicit gameplay/system interfaces or commands rather than directly making the widget the owner of that gameplay rule.

89. The framework MUST NOT introduce a generic reflection-based data-binding layer, custom MVVM framework, or second project-wide event bus in this specification.

90. The framework MUST NOT require a feature widget to search the world every frame to rediscover the objects/data it displays.

## Visual-design separation

91. C++ UI framework code MUST own technical behavior, lifecycle, routing, interfaces, and reusable non-visual logic.

92. Widget Blueprints and supplied UI assets MUST own feature-specific visual layout, art references, animation, and presentation.

93. Production visual values that are intended to be shared across multiple widgets, such as reusable text styles, button styles, colors, brushes, or other common presentation values, SHOULD be centralized in CommonUI style assets or other explicit Lord Simulator style/data assets rather than duplicated across unrelated widgets.

94. This specification MUST NOT define or invent final production values for:

    - colors;
    - fonts;
    - font sizes;
    - margins/padding;
    - iconography;
    - panel textures;
    - button textures;
    - borders;
    - animations;
    - sounds;
    - visual effects;
    - decorative art.

95. Future specifications that introduce production UI visuals MUST provide or identify every required non-code input according to `SPEC_STANDARD.md`.

96. Future AI-generated visual assets MUST be imported as normal project assets and referenced through the UI/content system. Runtime code MUST NOT generate substitute visual designs merely because a required production asset is absent.

97. Missing required production visual assets MUST NOT be silently replaced with invented Lord Simulator art by the implementation agent.

## Content organization

98. Use `/Game/UI` as the canonical root for Lord Simulator screen-space UI content.

99. Use `/Game/UI/Framework` for technical framework Widget Blueprints or framework-specific UI assets.

100. Future UI content SHOULD use these canonical subdirectories according to asset purpose:

    - `/Game/UI/Screens`
    - `/Game/UI/Widgets`
    - `/Game/UI/Styles`
    - `/Game/UI/Icons`
    - `/Game/UI/Textures`
    - `/Game/UI/Fonts`
    - `/Game/UI/Materials`

101. Empty content directories do not need to be committed merely to satisfy requirement 100.

102. Feature-specific UI MAY create additional subdirectories beneath `/Game/UI` when needed, but MUST NOT establish a competing top-level UI content root without an explicit architectural change.

## Resolution and layout behavior

103. The primary UI root MUST stretch to the complete local-player viewport.

104. The framework MUST support normal Unreal DPI scaling and responsive UMG layout behavior rather than assuming one fixed pixel resolution.

105. Framework and future production widgets MUST be able to use anchors, layout containers, and other responsive UMG mechanisms.

106. The framework MUST NOT hard-code a single fixed monitor resolution or aspect ratio as the only supported UI layout.

107. The technical root layout MUST be verified at minimum with viewport shapes corresponding to:

    - `1280x720`;
    - `1920x1080`;
    - `2560x1440`;
    - `3440x1440`;
    - `3840x2160`.

108. Verification in requirement 107 validates that the root fills the viewport and layers remain correctly ordered; this specification does not require production visual layouts for those resolutions.

109. This specification MUST NOT define a final Lord Simulator DPI curve, UI-scale player setting, minimum font size, or safe-zone policy. Those visual/accessibility decisions require a future specification when production UI is introduced.

## Performance rules

110. UI framework and production UI MUST prefer event-driven state updates over per-frame polling.

111. Reusable UI components SHOULD be implemented as reusable widgets rather than duplicated widget hierarchies when they provide the same behavior.

112. Future large scrolling collections of data, including lists that may contain large numbers of buildings, characters, resources, inventory entries, records, or similar items, MUST use Unreal virtualized collection widgets such as `UListView`, `UTileView`, `UTreeView`, or their suitable CommonUI equivalents unless a specification explicitly requires another implementation.

113. A feature MUST NOT create hundreds or thousands of simultaneously live off-screen entry widgets when a suitable Unreal virtualized list/tree/tile control can represent the content.

114. Global Invalidation, Invalidation Boxes, Retainer Panels, or Volatile widgets MUST NOT be applied mechanically to all Lord Simulator UI by this specification.

115. Invalidation/retainer/volatility optimizations MAY be introduced where profiling or a future specification demonstrates a need and their behavior is appropriate for the affected widget.

116. The implementation MUST remain compatible with Unreal's Widget Reflector, Slate Insights, and other standard Unreal UI profiling/debugging tools.

## Scope exclusions

117. Do not implement a production main menu.

118. Do not implement a production gameplay HUD.

119. Do not implement resource bars, population information, time controls, construction controls, selected-building UI, selected-character UI, inventory, character sheets, diplomacy, quests, map screens, settings UI, save/load UI, tooltips, notifications, tutorials, dialogs, or any other production feature UI.

120. Do not add user-facing localization entries.

121. Do not add production fonts, icons, textures, materials, UI sounds, animations, or other visual/audio assets.

122. Do not add placeholder player-facing UI solely to demonstrate the framework.

123. Do not implement drag/move/resize behavior for gameplay panels.

124. Do not implement a general docking/window-manager system.

125. Do not implement screen-reader support, text-to-speech, UI-scale settings, color-blind modes, or other accessibility features in this specification. The framework MUST NOT intentionally prevent those from being added later.

126. Do not implement CommonUI controller-data assets, controller glyphs, platform-specific prompt art, or gamepad-specific UI navigation in this specification.

## Automated tests

127. Implement Unreal Engine C++ automated tests for the UI framework.

128. Tests MUST use test-only widget classes/fixtures where required and MUST NOT add placeholder production UI assets merely to test the framework.

129. Automated tests MUST deterministically verify that the UI subsystem maintains no more than one primary UI root per local player.

130. Automated tests MUST verify repeated initialization is idempotent while a valid root exists.

131. Automated tests MUST verify the root exposes exactly the canonical `Game`, `Menu`, `Modal`, and `PassiveOverlay` layers.

132. Automated tests MUST verify the canonical visual layer ordering:

    `Game < Menu < Modal < PassiveOverlay`

133. Automated tests MUST verify that multiple `Game`-layer widgets can coexist.

134. Automated tests MUST verify that multiple `PassiveOverlay` widgets can coexist.

135. Automated tests MUST verify that `PassiveOverlay` is input/hit-test transparent.

136. Automated tests MUST verify that `Menu` uses top-of-stack activation/display behavior.

137. Automated tests MUST verify that `Modal` uses top-of-stack activation/display behavior.

138. Automated tests MUST verify modal presentation has higher visual/input priority than menu/game presentation.

139. Automated tests MUST verify the baseline root/input configuration permits combined game and UI interaction rather than UI-only behavior.

140. Automated tests MUST verify menu/modal activatable widgets can establish menu-oriented input behavior through CommonUI.

141. Automated tests MUST verify incompatible widget classes are rejected safely by layer operations.

142. Automated tests MUST verify removing framework-managed widgets does not leave stale framework references.

143. Automated tests MUST verify production UI initialization cannot create player-facing root content before the localization startup prerequisite is satisfied, using an internal test seam if required.

144. Automated tests MUST NOT depend on a production HUD, production menu, production localization entry, or production visual asset.

## Build and packaged verification

145. `LordSimulatorEditor Win64 Development` MUST build successfully after implementation.

146. `LordSimulator Win64 Shipping` MUST build successfully after implementation.

147. The project MUST launch successfully through Unreal Editor/PIE with the UI framework enabled.

148. The packaged Windows Shipping application MUST launch successfully with the UI framework enabled.

149. CommonUI/UMG assets and modules required by the framework MUST be available in the packaged Shipping build.

150. The packaged application MUST create only one Lord Simulator primary screen-space UI root for the primary local player.

151. The technical root MUST not display placeholder production text or art in the packaged build.

## Documentation

152. Update the game-project `README.md` if implementation changes developer setup, plugin enablement, build prerequisites, automated-test execution, or other build/verification workflow.

153. Document the established UI architecture sufficiently for a developer to understand:

    - UMG is the primary UI authoring system;
    - CommonUI is used selectively;
    - the purpose of `ULordSimulatorUISubsystem`;
    - the purpose of `ULordSimulatorUserWidget`;
    - the purpose of `ULordSimulatorActivatableWidget`;
    - the purpose of `ULordSimulatorPrimaryUILayout`;
    - the four canonical UI layers and their interaction behavior;
    - the rule that production screen-space UI enters through the primary root;
    - the event-driven update rule;
    - the prohibition on raw per-frame UMG bindings for production gameplay data;
    - the canonical `/Game/UI` content layout;
    - how to run the UI framework automated tests.

## Project-standard update

154. Update `PROJECT_STANDARD.md` as part of this specification to add an authoritative `UI Framework` section reflecting the project-wide architecture established by this specification.

155. The `PROJECT_STANDARD.md` UI Framework section MUST establish, without unnecessarily duplicating implementation details:

    - UMG as the primary screen-space UI authoring framework;
    - selective CommonUI usage;
    - `ULordSimulatorUISubsystem` as the authoritative per-local-player screen-space UI owner;
    - one primary UI root per local player;
    - the canonical `Game`, `Menu`, `Modal`, and `PassiveOverlay` layers and their ordering;
    - production screen-space UI routing through the primary root;
    - the screen-space/world-space UI boundary;
    - CommonUI activation/input-routing usage for menu/modal UI;
    - event-driven UI data updates;
    - prohibition of raw per-frame gameplay-data bindings;
    - simulation/gameplay systems remaining authoritative for gameplay state;
    - visual behavior/layout being separated from C++ framework behavior;
    - `/Game/UI` as the canonical UI content root;
    - the virtualized-list requirement for large collections;
    - the rule that UI initialization displaying player-facing localizable content occurs only after localization startup completion.

156. The project-standard update MUST NOT state that ModelViewViewModel, Experimental UIFramework, CommonUI Enhanced Input integration, gamepad navigation, or any production visual design is part of the established Lord Simulator architecture.

# Acceptance Criteria

1. The project builds and launches with UMG and CommonUI configured for the Lord Simulator UI framework.

2. The game viewport uses `UCommonGameViewportClient` or a Lord Simulator subclass of it.

3. No third-party UI dependency is introduced.

4. The UMG Viewmodel/MVVM plugin and Experimental UIFramework plugin are not adopted as the Lord Simulator UI architecture.

5. `ULordSimulatorUISubsystem` exists as a `ULocalPlayerSubsystem` and provides the authoritative screen-space UI access point for its local player.

6. No more than one valid primary Lord Simulator UI root exists for a local player.

7. Repeated UI initialization while the root exists does not create duplicate roots.

8. `ULordSimulatorUserWidget` derives from `UCommonUserWidget`.

9. `ULordSimulatorActivatableWidget` derives from `UCommonActivatableWidget`.

10. `ULordSimulatorPrimaryUILayout` derives from `ULordSimulatorActivatableWidget`.

11. `/Game/UI/Framework/WBP_LordSimulatorPrimaryUILayout` exists, derives from the required C++ root class, fills the viewport, and contains no player-facing production content.

12. The root contains exactly the canonical layers `Game`, `Menu`, `Modal`, and `PassiveOverlay`.

13. The root renders the layers in the required order:

    `Game < Menu < Modal < PassiveOverlay`

14. Multiple `Game` widgets can be displayed simultaneously.

15. Adding a `Game` widget does not globally switch the application to UI-only input and does not modify simulation time.

16. `Menu` uses CommonUI stack/activatable behavior in which only the top menu is displayed/active and active menu UI blocks normal gameplay/world commands.

17. `Modal` uses CommonUI stack/activatable behavior in which only the top modal is displayed/active.

18. Active modal UI renders above and prevents interaction with lower Lord Simulator UI and normal gameplay/world commands.

19. Closing the top menu/modal restores the valid underlying CommonUI/input state without reconstructing unrelated UI.

20. `PassiveOverlay` supports multiple child widgets and is hit-test/input transparent.

21. Production screen-space Lord Simulator feature UI can be added/removed/pushed/popped through `ULordSimulatorUISubsystem` without manipulating root internals.

22. Invalid layer operations fail safely and do not crash.

23. Production Lord Simulator screen-space UI does not require feature code to create independent viewport roots.

24. World-space `UWidgetComponent` UI is not forced through the CommonUI screen-space layer system.

25. UI initialization capable of presenting player-facing localizable content does not occur before localization startup completion.

26. The framework contains no raw per-frame UMG property/function binding architecture for gameplay data.

27. The framework contains no Tick-based gameplay-data synchronization.

28. The framework establishes event-driven updates and leaves gameplay/simulation systems authoritative for displayed gameplay state.

29. The framework does not introduce a custom MVVM system, reflection-based data-binding system, or competing project-wide event bus.

30. No final production colors, fonts, textures, icons, animations, sounds, layout design, or other creative UI decisions are invented.

31. No production main menu, HUD, context panel, inventory, settings UI, tooltip design, notification design, or other feature UI is added.

32. No player-facing localization entries or placeholder player-facing UI are introduced.

33. `/Game/UI` is established as the canonical screen-space UI content root and the framework asset is located under `/Game/UI/Framework`.

34. The root/layers behave correctly at the required test viewport sizes, including ultrawide `3440x1440`.

35. Large future collections are governed by the virtualized-list requirement rather than a project pattern of creating large numbers of off-screen widgets.

36. Unreal C++ automated tests exist and pass for root ownership, layer structure/order, stack behavior, passive-overlay input transparency, layer validation, input configuration, localization prerequisite, and cleanup behavior.

37. `LordSimulatorEditor Win64 Development` builds successfully.

38. `LordSimulator Win64 Shipping` builds successfully.

39. Editor/PIE launches successfully with the UI framework.

40. The packaged Windows Shipping build launches successfully with the UI framework and required UMG/CommonUI resources.

41. The packaged build contains only one primary Lord Simulator screen-space UI root for the primary local player.

42. The technical root displays no placeholder production text or art.

43. `README.md` contains the required UI-framework developer documentation when the implementation changes documented setup or verification workflow.

44. `PROJECT_STANDARD.md` contains the authoritative UI Framework section required by this specification and does not claim that excluded experimental/input/visual systems are established project architecture.
