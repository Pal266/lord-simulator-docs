# Visual Work Standard

## 1. Purpose

This standard defines how AI agents and other contributors MUST create, organize, review, approve, and preserve visual work for Lord Simulator.

The visual workflow separates exploratory work, approved visual direction, and production assets so that implementation specifications can identify exactly which visual material is safe to use in the game.

## 2. Canonical Visual Directories

All visual-development material stored in the documentation repository MUST be organized under:

`visuals/`

The canonical root directories are:

- `visuals/research/`
- `visuals/style/`
- `visuals/approved/`

These directories have different authority and usage rules.

### 2.1 Research

`visuals/research/` contains visual work that is exploratory, provisional, rejected, undecided, or otherwise not approved for direct production use.

It MAY contain, for example:

- visual research;
- reference collections;
- moodboards;
- prototypes;
- mockups;
- experiments;
- AI-generated variants;
- prompt experiments;
- rejected directions;
- comparison material;
- work-in-progress visual concepts.

Material in `visuals/research/` is NOT approved for direct use in the game.

An implementation specification MUST NOT instruct the implementation agent to import or use a visual asset from `visuals/research/` as a production game asset.

A specification whose purpose is visual research, comparison, prototyping, or design exploration MAY reference material in `visuals/research/` when that material is used only as research or design input and not as a production asset.

### 2.2 Style

`visuals/style/` contains approved visual direction and reusable visual rules.

It MAY contain, for example:

- approved style guides;
- approved visual principles;
- approved palette direction;
- approved iconography rules;
- approved UI presentation rules;
- approved character/environment art direction;
- approved examples that illustrate a style rule.

Material in `visuals/style/` describes how future visual work should look or behave. It does not automatically become a production game asset merely because it is stored in the style directory.

Implementation specifications MAY reference style material as authoritative visual guidance when relevant.

A concrete visual file that must be imported into or directly used by the game MUST still come from `visuals/approved/`.

### 2.3 Approved

`visuals/approved/` contains only visual assets explicitly approved for direct production use in Lord Simulator.

An asset MUST NOT be placed in `visuals/approved/` merely because an AI agent considers it complete, technically suitable, visually strong, or consistent with an approved style.

An asset becomes approved only after the user explicitly accepts it for production use.

An AI agent MUST NOT infer production approval from silence, lack of criticism, or general positive feedback when explicit production approval has not been given.

Approved assets are the only visual assets that implementation specifications may identify for direct import or use in the game.

Research files, rejected variants, exploratory references, prompt history, temporary mockups, and other non-production material MUST NOT be stored in `visuals/approved/`.

## 3. Approved Asset Preservation

Approved assets are immutable by default.

An AI agent or implementation agent MUST NOT, without an explicit specification authorizing the change:

- delete an approved asset;
- overwrite an approved asset;
- replace an approved asset;
- rename an approved asset;
- move an approved asset;
- crop an approved asset;
- resize an approved asset;
- recolor an approved asset;
- repaint or redraw an approved asset;
- retouch an approved asset;
- alter transparency or alpha data;
- recompress an approved asset;
- convert an approved asset to another file format;
- make any other content-changing or identity-changing modification to an approved asset.

A specification that changes an approved asset MUST identify the exact approved asset affected and define the required change unambiguously.

If a new variant or replacement is being explored, the new work MUST remain outside `visuals/approved/` until the user explicitly approves it for production use.

An existing approved asset MUST remain unchanged while a replacement is being researched unless the specification explicitly requires otherwise.

The existence of a newer experiment does not revoke approval of an existing approved asset.

## 4. Promotion to Approved

Moving or copying an asset into `visuals/approved/` is a production-approval action.

An AI agent MUST NOT promote an asset into `visuals/approved/` without explicit user approval for production use.

When the user approves a production asset, the agent MAY place the approved asset in `visuals/approved/` using its final semantic name.

If the asset already exists elsewhere in the repository as research material, the approved copy or move MUST preserve the exact visual content that the user approved unless the user explicitly requests an additional modification.

An agent MUST NOT silently improve, clean up, resize, recolor, regenerate, or otherwise modify an asset while promoting it to `visuals/approved/`.

## 5. Semantic Naming

Visual directories and files MUST use semantic names.

A semantic name describes the asset's purpose, subject, role, state, or variant in terms meaningful to the project.

Names SHOULD be understandable without opening the file.

Examples of semantic names include:

- `ui-button-primary-default.png`
- `ui-button-primary-hover.png`
- `icon-resource-wood.png`
- `icon-resource-stone.png`
- `panel-building-details-background.png`
- `building-house-tier1-exterior.png`

Names such as the following MUST NOT be used as final production asset names:

- `final.png`
- `final2.png`
- `new-final.png`
- `image1.png`
- `test.png`
- `output.png`
- `generated-12345.png`

Temporary research material MAY retain generator-specific names when needed during active exploration, but any material promoted into `visuals/style/` or `visuals/approved/` MUST receive a semantic project name.

Semantic names SHOULD use lowercase kebab-case unless a file format, external tool, or established project convention requires another form.

A filename MUST NOT encode approval state with words such as `approved`, `final`, or `production`; the directory location is the source of truth for approval state.

When multiple approved variants intentionally coexist, their names MUST describe the meaningful variant rather than use arbitrary numeric suffixes.

## 6. Visual Agent Behavior

An AI agent working with Lord Simulator visuals MUST treat the three visual directories as workflow states, not interchangeable storage locations.

The agent MAY freely propose new visual directions in `visuals/research/` when the task authorizes visual exploration.

The agent MUST preserve user-approved style direction stored in `visuals/style/` and MUST NOT silently replace an approved style decision with a different direction.

When a task conflicts with an approved style rule, the agent MUST identify the conflict rather than silently ignoring the established style.

The agent MUST NOT use an unapproved research asset as a substitute when a specification requires an approved production asset that is missing.

The agent MUST NOT create a replacement asset during implementation merely to avoid reporting that an approved required asset is unavailable.

If a required approved asset cannot be found at the specified path, the agent MUST report the missing asset instead of selecting a visually similar research file.

## 7. Specification Relationship

`SPEC_STANDARD.md` defines what implementation specifications may reference.

For visual assets intended to be imported into or directly used by the game, a specification MUST reference an exact path under `visuals/approved/`.

A specification MAY reference `visuals/style/` for authoritative visual guidance.

A visual-research or visual-design specification MAY reference `visuals/research/` for comparison, inspiration, experimentation, or prototype work, but MUST NOT present such material as an approved production asset.

An implementation specification MUST NOT depend on the implementation agent choosing among multiple visual candidates. The required approved production asset MUST already be identified unambiguously.

## 8. Scope of This Standard

This standard governs repository workflow and authority for visual material.

It does not define final Lord Simulator art direction, UI style, icon style, character style, environment style, supported image formats, import settings, texture sizes, compression settings, or other asset-specific production rules.

Those rules MAY be established later through approved style documents, project standards, or specifications as the visual direction matures.
