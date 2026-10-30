# Visual Standard

## Purpose

This standard defines how visual assets for Lord Simulator are created, documented, stored, referenced, and prepared for implementation.

The purpose of the standard is to keep visual work consistent, reproducible, implementation-ready, and clearly separated from visual references or experiments. Visual assets may be created with AI-assisted tools. AI generation does not reduce the requirement for deliberate review, technical suitability, or consistency with the established Lord Simulator visual direction.

This standard defines visual-production rules. It does not define the artistic identity of Lord Simulator. Project-wide artistic direction, once established, must be documented separately and treated as authoritative for visual style.

## Asset Repository

1. Visual source assets and visual reference material used by Lord Simulator specifications MUST be stored under the repository root `assets/` directory.

2. Asset subdirectories MUST be created according to actual project needs. Empty category directories MUST NOT be created merely to anticipate future asset types.

3. Appropriate categories MAY include, but are not limited to:
   - `ui/`
   - `textures/`
   - `models/`
   - `materials/`
   - `icons/`
   - `branding/`
   - `references/`

4. Production assets and reference assets MUST be distinguishable by repository location and documentation.

5. `assets/references/` is reserved for concept images, mood references, composition references, style explorations, and other material that is not itself intended to be imported into or shipped with the game.

6. An asset intended for implementation MUST NOT be stored only as a reference asset.

7. The documentation repository is the design/source authority for approved visual assets referenced by specifications. Imported Unreal Engine assets and any engine-specific derivatives belong in the implementation repository.

## Asset Status and Approval

8. A visual asset referenced by an implementation-ready specification MUST be an approved production asset unless the specification explicitly defines visual generation as work to be performed before implementation.

9. Experimental, rejected, draft, or reference visuals MUST NOT be presented as production assets.

10. Replacing an approved asset MUST preserve the semantic purpose expected by specifications that use it, unless those specifications are also intentionally revised.

11. Visual review MUST consider both artistic consistency and technical suitability for the asset's intended use.

## AI-Generated Visual Assets

12. AI-generated visual assets are permitted and are expected to be a normal part of Lord Simulator visual production.

13. AI-generated output MUST be reviewed before it is treated as an approved production asset.

14. AI output MUST NOT be accepted solely because it is visually attractive. It MUST satisfy the functional, technical, and stylistic requirements of its intended use.

15. When an existing approved asset or reference is required to maintain consistency, visual generation SHOULD use that asset or reference directly where the generation workflow supports reference images.

16. Important generated assets MUST retain enough metadata to reproduce their design intent and create consistent related assets later.

17. Generation metadata SHOULD describe the asset's purpose, intended use, dimensions or geometry constraints where applicable, transparency requirements, relevant style/reference material, generation method, and any important implementation notes.

18. Exact generation prompts MAY be retained when useful, but prompt text alone MUST NOT be treated as sufficient asset documentation.

19. AI-generated text embedded inside visual assets MUST NOT be used for normal player-facing UI text.

20. Player-facing text MUST normally be rendered by the game using the established localization system rather than baked into generated images.

21. Exceptions to the no-baked-text rule require an explicit specification requirement and must address localization implications.

## Visual Consistency

22. New visual assets MUST follow the established Lord Simulator visual style when a project visual style has been approved.

23. A new asset MUST NOT introduce a conflicting visual language merely because it was produced by a different model, tool, generation session, or implementation agent.

24. When no authoritative visual direction exists for a new category of asset, the visual direction SHOULD be established and approved before a large family of production assets is generated.

25. Related asset states and variants SHOULD be designed as one coherent family. Examples include normal, hovered, pressed, selected, focused, and disabled UI states.

26. Visual consistency MUST be evaluated across the application rather than only within an individual screen or feature.

## Asset Naming and Organization

27. Asset filenames MUST be descriptive and identify semantic purpose rather than generation order alone.

28. Names such as `image1.png`, `final2.png`, `new-button.png`, or equivalent ambiguous names MUST NOT be used for approved production assets.

29. Variants of the same visual asset MUST use a consistent naming scheme that makes their relationship clear.

30. Assets belonging exclusively to one feature or screen SHOULD be grouped together when doing so improves discoverability.

31. Shared assets SHOULD be stored in a location that makes their shared purpose clear rather than duplicated across feature directories.

32. Duplicate copies of the same approved production asset SHOULD be avoided.

## Asset Metadata

33. Significant production assets SHOULD have adjacent Markdown metadata when the information required to use or reproduce the asset is not self-evident.

34. Asset metadata files SHOULD use the asset filename followed by `.asset.md` where practical. For example:

    `button-default.png`

    `button-default.png.asset.md`

35. Metadata MAY include:
   - asset purpose;
   - production/reference status;
   - intended feature or screen;
   - dimensions;
   - transparency requirements;
   - expected scaling or tiling behavior;
   - source/reference assets;
   - generation information;
   - approved visual-style version or direction;
   - Unreal import or implementation notes;
   - known restrictions.

36. Metadata MUST NOT contradict the implementing specification. The specification remains authoritative for feature requirements.

## UI Assets

37. UI visual assets MUST be created so that localized text can be rendered separately whenever the asset contains a text-bearing area.

38. UI assets MUST NOT assume that English text length represents the maximum required layout size.

39. UI elements that require multiple interaction states MUST have every required state explicitly supplied or explicitly defined by the implementing specification.

40. The implementation agent MUST NOT invent missing hover, pressed, selected, disabled, focus, icon, panel, decorative, or other visual states.

41. UI assets intended to scale MUST document the expected scaling behavior and, when applicable, which regions may stretch or tile without visual damage.

42. Transparency MUST be used where required by the intended UI composition.

43. Decorative UI imagery MUST NOT be used as the only mechanism for conveying information required to operate the interface.

## Textures, Materials, and 3D Assets

44. Texture, material, and 3D asset requirements MUST define the technical properties necessary for implementation when those properties matter, including dimensions, maps, transparency, tiling, geometry, scale, orientation, or other relevant constraints.

45. A specification requiring a 3D or material asset MUST provide enough information for the implementation agent to import and use it without making artistic decisions omitted from the specification.

46. Production 3D assets MUST use a consistent project scale and orientation suitable for Unreal Engine integration.

47. Required texture maps or material inputs MUST be explicitly identified. The implementation agent MUST NOT infer missing production maps merely from appearance.

48. Optimization requirements such as polygon budgets, texture resolution limits, LODs, collision, or platform-specific constraints MUST be specified when relevant to the asset.

## File Formats and Technical Requirements

49. Asset file format MUST be appropriate for the intended implementation use and preserve required information such as transparency, color fidelity, geometry, or editable source data.

50. Lossy formats MUST NOT be used when their artifacts materially degrade an asset's intended production use.

51. UI raster assets requiring transparency SHOULD use a format that preserves alpha without destructive compression.

52. Editable/source forms SHOULD be retained when they are necessary to reliably revise or regenerate a production asset.

53. Specifications MUST state exact technical constraints when implementation depends on them rather than relying on an implementation agent to choose arbitrary values.

## Specifications and Visual Assets

54. A specification that requires visual assets MUST identify every visual asset required to satisfy its requirements and acceptance criteria.

55. When an approved production asset already exists, the specification SHOULD reference its exact repository path.

56. A requirement such as `create a medieval-looking button`, `add an appropriate icon`, or equivalent open-ended artistic instruction is insufficient for a coding-only implementation agent unless visual creation is explicitly within that agent's assigned scope.

57. A specification MUST NOT require the implementation agent to invent visual design, artwork, visual states, icons, textures, models, or other missing visual content.

58. If a required visual asset has not yet been created or approved, the specification is not implementation-ready unless the specification explicitly assigns visual-asset creation to an appropriate visual workflow or agent.

59. Specifications MUST distinguish reference assets from production assets when both are relevant.

60. User-facing text associated with visual assets MUST follow the project's localization requirements and MUST NOT be silently embedded into images to avoid localization work.

## Implementation

61. The implementation agent MUST use the exact approved production assets required by the specification.

62. The implementation agent MUST NOT replace an approved asset with an approximation, placeholder, engine default, newly generated alternative, or unrelated asset unless the specification explicitly permits that behavior.

63. Importing a source asset into Unreal Engine MAY require engine-specific configuration or conversion. Such work MUST preserve the approved visual result and the technical intent defined by the specification.

64. Engine-generated derivatives and imported Unreal assets do not replace the repository source asset as the design/source reference.

65. If an asset cannot be imported or used as specified, implementation MUST stop for the affected requirement and report the inconsistency rather than silently substituting another visual.

## Repository Size and Binary Asset Management

66. Binary visual assets MUST be managed with awareness of repository growth.

67. Before large quantities of high-resolution textures, large source files, or 3D models are added, the project MUST establish an appropriate binary-asset storage strategy, such as Git LFS or another explicitly approved mechanism.

68. Large binary assets MUST NOT be added repeatedly as uncontrolled versions solely to preserve visual history.

69. Reference material SHOULD be kept only when it has continuing design value.

## Relationship to Future Visual Style Documentation

70. This standard defines process and technical expectations, not the final Lord Simulator artistic style.

71. A separate project visual-style document SHOULD be created once the initial artistic direction has been deliberately explored and approved.

72. The visual-style document SHOULD define the authoritative artistic direction for matters such as visual mood, palette, materials, typography, ornamentation, iconography, UI treatment, environmental presentation, and consistency rules.

73. When the visual-style document exists, production visual assets MUST comply with both this standard and that visual-style document.
