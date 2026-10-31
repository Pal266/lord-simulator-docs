# Spec 006 — Localization Framework (Clarification Update)

This update resolves the ambiguity between requirements 69 and 71 in
`spec-006-localization-framework.md`.

All requirements and acceptance criteria not explicitly replaced below remain
unchanged from the existing Spec 006.

## Replacement requirements

### 68

After localization framework initialization has succeeded, a runtime
language-change request must validate the requested culture against Lord
Simulator-supported cultures before attempting to apply it. If localization
framework initialization failed, requirement 69 takes precedence and the
request is rejected before this validation is performed.

### 69

If localization framework initialization failed, any runtime language-change
request is rejected before the normal runtime request validation described in
requirements 68 and 71. Initialization failure takes precedence even when the
requested culture would otherwise be unsupported. The request:

- is rejected;
- is not validated or logged as an unsupported-culture request under
  requirement 71;
- does not attempt an Unreal culture change through the Lord Simulator
  framework;
- leaves configured and active state unchanged;
- returns failure;
- uses the applicable runtime application-failure log from requirements 74 or
  75.

### 70

Successful framework initialization followed by failure to establish an active
language does not disable later runtime language-change requests. A later
supported request may attempt application normally.

### 71

If localization framework initialization succeeded and a runtime request uses
an unsupported culture:

- do not call Unreal to apply it;
- do not change configured or active language;
- return failure;
- if an active language exists, log exactly:
  `Language '<requested>' is not supported. Language '<active>' will remain active.`
- if active language is unavailable, log exactly:
  `Language '<requested>' is not supported. No language is currently active.`

## Required precedence

Runtime language-change processing must follow this precedence:

1. If localization framework initialization failed, apply requirement 69 and
   then the applicable log behavior from requirement 74 or 75. Do not apply
   requirement 71.
2. If localization framework initialization succeeded, validate the requested
   culture.
3. If the culture is unsupported, apply requirement 71.
4. If the culture is supported, continue with the existing no-op/application
   behavior in requirements 72–75.

This means a request that is both made after initialization failure and names an
unsupported culture produces only the applicable requirement 74/75
`could not be applied` log, not an additional requirement 71
`is not supported` log.
