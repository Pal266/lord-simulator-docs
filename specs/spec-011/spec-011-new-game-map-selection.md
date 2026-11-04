# Title

New Game Map Selection and Terrain Loading

# Type

feature

# Description

Enable the existing New Game button to open a terrain-based overview of the generated 100 × 100 km southern_coast_range region. The player selects one of sixteen 25 × 25 km plots and enters its real Unreal Landscape with a free-flying camera. This is an end-to-end verification of the offline terrain-generation, import, packaging, selection and loading pipeline; it does not introduce gameplay.

# Requirements

1. **Source and reproducibility.** Use the authoritative region definition and offline generation workflow in the documentation repository at `fictional_map/regions/southern_coast_range/region.json` and `USAGE.md`. The source region is 100 × 100 km, divided into a 4 × 4 grid of 25 × 25 km plots, named `tile_x{col}_y{row}` with columns west-to-east (0–3) and rows north-to-south (0–3). Do not synthesize a replacement landscape, use arbitrary test terrain, or regenerate the scientific world in the running game. Document the exact reproducible offline commands, required source files, resulting cooked game assets, and any conversion/import commands in the game project's root README. Large generated exports may be produced locally and need not be checked into the documentation repository.

2. **Import all sixteen real landscapes.** Generate or obtain the outputs from the documented pipeline, run its available scientific/plot validators, and import each of the sixteen actual `export/tile_x{col}_y{row}/heightmap.png` files into Unreal as a separately loadable landscape level. Each input is 16-bit grayscale, 8129 × 8129 vertices, with height encoding `32768 + elevation_metres × 12.8`. Use Unreal X/Y scale 307.574 and Z scale 1000, following the documented region workflow. Preserve each plot's correct orientation and elevation; do not independently rescale heights to fit the plot. Each selected level may use its own local origin. The level must be cooked and loadable in a packaged Windows build without requiring Python, the documentation repository, or external heightmap files at runtime.

3. **Minimal terrain presentation.** Show the actual landscape geometry with one simple neutral, non-decorative engine-generated material or an existing suitable engine material; no imported artistic texture, biome shading, foliage, rivers, lakes, roads, structures, NPCs, lighting effects selected for art direction, or other world content is required. Provide only the basic lighting necessary to see the relief. No Water plugin integration is part of this specification. Do not introduce new third-party dependencies or approved visual assets.

4. **New Game navigation.** Make the existing main-menu New Game action selectable and functional. Activating it replaces the main-menu content with a region-selection screen inside the existing application window (not a new operating-system window). Preserve the application's established resolution, fullscreen, localization and lifecycle behavior. Provide a Back action on the selection screen that returns to the main menu.

5. **Overview.** The selection screen must display a top-down, terrain-derived overview of the complete 100 × 100 km region. Derive this overview deterministically from the actual generated elevation data (for example a downsampled height representation); do not use a hand-painted map or substitute unrelated imagery. Show visible 4 × 4 boundaries in correct geographic order, with west at left and north at top. The sixteen squares are individually clickable. Indicate the square under the pointer using a simple outline. Each square maps exactly to its corresponding `tile_x{col}_y{row}` landscape. The overview must be available in the packaged build and must not depend on external files at runtime.

6. **Selection and loading.** A single click on a square opens only the corresponding plot's level and displays its real terrain. Do not load all sixteen full-resolution landscapes simultaneously. Prevent duplicate load requests while a level transition is in progress. A load failure must not present an unrelated or empty landscape as a successful result; it must return to the selection screen with a clearly visible failure message. The user must be able to select and enter any of the sixteen plots in a packaged build.

7. **Free camera.** After a successful load, place a free-flying, non-colliding spectator camera above the centre of the selected plot, facing diagonally downward so that terrain is visible. Use W/A/S/D for horizontal movement relative to camera heading, Q/E for down/up, hold the right mouse button and move the mouse to rotate, and mouse wheel to adjust movement speed. Default movement speed is 100 m/s, bounded to 10–1000 m/s; default camera height is 500 m above the terrain at the plot centre. Camera movement is frame-time based and works while the game is not simulating time. The camera must not be attached to a player character and must not introduce a player pawn with gameplay capabilities.

8. **Time and gameplay scope.** No in-game time progression, simulation ticks for economy/population/AI, building placement, resource processing, saving/loading a game, RPG mechanics or world interaction are introduced. Engine rendering and input continue normally. Existing application systems remain functional and unchanged except where explicitly required here.

9. **User-facing text.** Reuse the existing localized `MainMenu.NewGame` entry for the existing button. Add the following entries to the canonical Lord Simulator localization resources, preserving the existing supported cultures (`en`, `cs`, `uk`):
   - `NewGame.RegionSelection.Title`: en `Select a region`; cs `Vyberte oblast`; uk `Виберіть регіон`.
   - `NewGame.RegionSelection.Back`: en `Back`; cs `Zpět`; uk `Назад`.
   - `NewGame.RegionSelection.LoadFailed`: en `Unable to load the selected region.`; cs `Vybranou oblast se nepodařilo načíst.`; uk `Не вдалося завантажити вибраний регіон.`.
   The tile identifiers are technical identifiers, not translated names. Do not add other player-facing strings or tooltips.

10. **Verification.** Add deterministic Unreal automation coverage for the sixteen overview-cell-to-level mappings and for missing/unavailable landscape handling. Verify in Unreal Editor and in a packaged Win64 Shipping build that New Game opens the overview, Back returns to the main menu, representative western/mountain and eastern/plain plots load with visibly different actual relief, the camera responds to the specified controls, and all sixteen levels are included in cooked content. Perform or document an objective comparison of representative terrain heights against the generated heightmap data within one 16-bit height step (~0.078 m) and check plot orientation. Record any practical engine limitation encountered during the 8129-vertex landscape import or cooking rather than silently substituting a smaller or fake map.

# Acceptance Criteria

1. The existing New Game button opens the selection screen, and Back returns to the main menu without changing existing startup, settings or localization behavior.
2. The selection screen displays a real-data-derived overview of the 100 × 100 km region with sixteen correctly ordered and individually selectable 25 × 25 km cells.
3. Selecting each cell loads the matching separately cooked Unreal Landscape level; the running packaged game does not require external generation scripts or data files.
4. Loaded terrain preserves the documented resolution, horizontal dimensions, elevation scale and orientation; representative height checks pass within the stated quantization tolerance.
5. Only the selected high-resolution landscape is loaded, with simple neutral presentation and no water, foliage, structures or gameplay content.
6. The free camera starts above visible terrain and responds to W/A/S/D, Q/E, right-mouse rotation and mouse-wheel speed adjustment.
7. No game-time progression, economic simulation, RPG systems or game-saving functionality is introduced.
8. Duplicate load requests are prevented and failed loads show the defined localized error rather than a misleading successful world.
9. All required localized entries are available in English, Czech and Ukrainian, using the established localization framework.
10. The defined automated checks pass, and the documented Editor and packaged Win64 Shipping verification steps are completed. The game-project README contains a reproducible generation/import/cook/build workflow.
