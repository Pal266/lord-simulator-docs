# Title

Czech and Ukrainian Localization

# Type

feature

# Description

Add Czech and Ukrainian as production-supported Lord Simulator cultures and provide complete Czech and Ukrainian translations for all player-facing localization entries currently contained in the canonical `LordSimulator` Localization Target.

The resulting production-supported culture set is `en`, `cs`, and `uk`. English remains the native/source culture.

This specification extends the existing Lord Simulator localization content and supported-culture configuration. It does not introduce a language-selection UI, settings screen, new localization architecture, or new player-facing text.

# Requirements

## Supported cultures

1. Add Czech as a production-supported Lord Simulator culture using the exact culture identifier:

   `cs`

2. Add Ukrainian as a production-supported Lord Simulator culture using the exact culture identifier:

   `uk`

3. After implementation, the production-supported Lord Simulator culture set MUST be exactly:

   - `en`;
   - `cs`;
   - `uk`.

4. Update the existing canonical `LordSimulator` Localization Target and authoritative runtime-readable supported-culture configuration so they consistently define exactly `en`, `cs`, and `uk`.

5. Update the standard Unreal localization configuration and generated localization resources as required so `cs` and `uk` are fully supported by the existing Lord Simulator localization workflow.

6. Update the standard Win64 packaging configuration so localization resources for `en`, `cs`, and `uk` are staged in packaged builds.

## Existing localization content

7. Translate every localization entry currently gathered into the canonical `LordSimulator` Localization Target.

8. The currently required translation set consists exactly of these existing entries:

| Localization key | English `en` | Czech `cs` | Ukrainian `uk` |
|---|---|---|---|
| `MainMenu.NewGame` | `NEW GAME` | `NOVÁ HRA` | `НОВА ГРА` |
| `MainMenu.LoadGame` | `LOAD GAME` | `NAČÍST HRU` | `ЗАВАНТАЖИТИ ГРУ` |
| `MainMenu.Settings` | `SETTINGS` | `NASTAVENÍ` | `НАЛАШТУВАННЯ` |
| `MainMenu.Quit` | `QUIT` | `UKONČIT` | `ВИЙТИ` |

9. The exact Czech and Ukrainian translations defined in requirement 8 MUST be used.

10. Existing localization keys and existing native English source text MUST remain unchanged.

11. If implementation begins and the canonical `LordSimulator` Localization Target contains an additional player-facing localization entry that is not defined in requirement 8, implementation MUST stop and report the inconsistency rather than inventing Czech or Ukrainian translation content.

12. Do not add placeholder localization entries, translation-test entries, tooltips, accessibility text, language-selection labels, or other new player-facing strings as part of this specification.

## Runtime and packaged verification

13. A valid configured `Language=cs` MUST activate Czech through the existing Lord Simulator localization framework when the Czech localization resources are available.

14. A valid configured `Language=uk` MUST activate Ukrainian through the existing Lord Simulator localization framework when the Ukrainian localization resources are available.

15. Runtime language changes using the existing localization framework MUST be able to activate `en`, `cs`, and `uk` when their resources are available.

16. With `cs` active, the main menu MUST display:

   - `NOVÁ HRA`;
   - `NAČÍST HRU`;
   - `NASTAVENÍ`;
   - `UKONČIT`.

17. With `uk` active, the main menu MUST display:

   - `НОВА ГРА`;
   - `ЗАВАНТАЖИТИ ГРУ`;
   - `НАЛАШТУВАННЯ`;
   - `ВИЙТИ`.

18. Czech diacritics and Ukrainian Cyrillic characters MUST render correctly using the existing main-menu typography.

19. The translated main-menu labels MUST remain readable, correctly aligned, and fully contained by their existing buttons at each of these viewport sizes:

   - `1280x720`;
   - `1920x1080`;
   - `2560x1440`;
   - `3440x1440`;
   - `3840x2160`.

20. This specification MUST NOT redesign or otherwise change the existing main-menu layout, button artwork, button dimensions, typography values, enabled/disabled states, or button behavior merely to accommodate the translations.

## Generated localization data

21. Regenerate the canonical localization manifest, culture archives, compiled localization resources, localization reports, and other normal Unreal-generated localization output required by the established Lord Simulator workflow after adding `cs`, `uk`, and their translations.

22. The generated localization output MUST contain no unresolved localization conflict caused by this specification.

23. The Czech and Ukrainian localization resources MUST contain translations for every entry defined in requirement 8 and MUST be loadable by Unreal at runtime.

## Standards update

24. Update `PROJECT_STANDARD.md` before this specification is considered complete.

25. `PROJECT_STANDARD.md` MUST define the resulting production-supported Lord Simulator culture set as exactly:

   - `en`;
   - `cs`;
   - `uk`.

26. Update any existing `PROJECT_STANDARD.md` wording that becomes inaccurate because Czech and Ukrainian are now production-supported cultures.

27. Preserve the existing project-wide localization architecture and policies that are not explicitly changed by this specification.

28. Review `SPEC_STANDARD.md`, `IMPLEMENTATION_STANDARD.md`, and `VISUAL_STANDARD.md` for statements made inaccurate by this change.

29. If another standard becomes inaccurate because of this implementation, update that standard as part of this specification so no contradiction remains between the implementation and the current standards.

30. If `SPEC_STANDARD.md`, `IMPLEMENTATION_STANDARD.md`, or `VISUAL_STANDARD.md` remain accurate after the change, leave them unchanged.

## Scope boundaries

31. Do not implement a language-selection screen or settings screen.

32. Do not enable the existing disabled `SETTINGS` main-menu button.

33. Do not add another supported culture beyond `en`, `cs`, and `uk`.

34. Do not introduce a new font, localization system, translation service, third-party localization dependency, or new Lord Simulator project log entry as part of this specification.

## Verification and tests

35. Add or update deterministic Unreal Automation coverage sufficient to verify at minimum:

   - supported-culture discovery returns exactly `en`, `cs`, and `uk`;
   - `cs` is recognized as supported;
   - `uk` is recognized as supported;
   - Czech can be applied when its localization resources are available;
   - Ukrainian can be applied when its localization resources are available;
   - the four main-menu localization entries resolve to the exact Czech translations defined in requirement 8;
   - the four main-menu localization entries resolve to the exact Ukrainian translations defined in requirement 8.

36. Existing localization tests and all previously existing Lord Simulator automation tests MUST continue to pass.

37. Build and verify the standard `LordSimulatorEditor` Win64 Development target.

38. Build/package the standard Win64 Shipping game.

39. Verify that the packaged build contains usable localization resources for `en`, `cs`, and `uk`.

40. Verify the packaged build with Czech active at all viewport sizes listed in requirement 19. At each size:

   - the exact Czech translations from requirement 8 are displayed;
   - Czech characters render correctly;
   - all translated labels remain readable and fully contained by their existing buttons;
   - existing main-menu behavior remains unchanged.

41. Verify the packaged build with Ukrainian active at all viewport sizes listed in requirement 19. At each size:

   - the exact Ukrainian translations from requirement 8 are displayed;
   - Ukrainian characters render correctly;
   - all translated labels remain readable and fully contained by their existing buttons;
   - existing main-menu behavior remains unchanged.

42. Verify the packaged build with English active and confirm that the existing English main-menu text and behavior remain unchanged.

# Acceptance Criteria

1. Lord Simulator's production-supported culture set is exactly `en`, `cs`, and `uk`.

2. The canonical `LordSimulator` Localization Target and authoritative supported-culture configuration consistently define `en`, `cs`, and `uk`.

3. Standard Win64 packaged builds include usable localization resources for all three supported cultures.

4. All four existing main-menu localization entries have the exact Czech translations defined in the Requirements.

5. All four existing main-menu localization entries have the exact Ukrainian translations defined in the Requirements.

6. Existing localization keys and native English source text remain unchanged.

7. `Language=cs` and `Language=uk` successfully activate their respective cultures through the existing localization framework when their resources are available.

8. Runtime language changes can activate `en`, `cs`, and `uk` through the existing localization framework.

9. Czech and Ukrainian main-menu text renders correctly and remains readable and fully contained at `1280x720`, `1920x1080`, `2560x1440`, `3440x1440`, and `3840x2160`.

10. Existing English main-menu text and behavior remain unchanged.

11. No language-selection UI, settings screen, additional supported culture, new localization system, new font, third-party localization dependency, or new project log entry is introduced.

12. Required localization automation coverage passes and all previously existing Lord Simulator automation tests continue to pass.

13. The standard `LordSimulatorEditor` Win64 Development build succeeds.

14. The standard Win64 Shipping packaged build succeeds with working English, Czech, and Ukrainian localization resources.

15. `PROJECT_STANDARD.md` is updated before the specification is considered complete and accurately reflects the resulting supported-culture set.

16. Any other standard made inaccurate by this implementation is updated, while unaffected standards remain unchanged.
