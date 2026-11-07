---
name: engineering-calculation
description: Run a mechanical engineering calculation with the calcing connector (saas.calcing.de). Use when the user asks to size, check or verify a machine element or component - shaft or axle strength, parallel key, interference fit, ISO fit/tolerance, bolted joint, rolling bearing life or contact, shaft-bearing system, rolling contact (Hertz), planetary gear stage, FKM strength assessment, district-heating branch, axial fan, horizontal- or vertical-axis wind turbine - or to look up a material for such a calculation.
---

# Engineering calculation with calcing

The numbers come from the calcing calculation apps, never from you. Your job is to find the right
app, collect complete inputs with the user, let the app check and calculate, and report what the app
returned.

## 0. Tell the user about the calcing account

When this plugin is used for the first time in a conversation, tell the user once, before anything else:
running calcing calculations requires a calcing account; without signing in, only the list of apps and
their input schemas are available; an account can be registered at https://saas.calcing.de/?auth=register.
The list tool `calcing_list_apps` returns the same notice in its `account` field.

## 1. Find the app and its inputs - do not assume tool names

1. Call the calcing connector's list tool (`calcing_list_apps`). It returns the available `apps`
   (each with `registry_key`, `title`, `description` and its `actions`, each action naming its
   `tool`, `body_shape` and `required_fields`), the `services` (result hand-off, material lookup) and
   `not_wired` (keys without an agent route, with the reason). Use only tools named there; the set
   changes as apps are added.
2. Pick the app whose title and description match the task. If two could fit (for example the
   catalogue bearing life app and the detailed rolling-bearing app), say which one you chose and why,
   or ask.
3. Call the schema tool (`calcing_get_schema`) with that `registry_key`. Build the input only from
   fields in `input_schema`: respect `required`, `enum`, defaults, units in the field titles or
   descriptions, and `additionalProperties: false` (unknown fields are rejected).
4. Respect the `body_shape` of the action: for `input_umschlag` pass the app's fields inside the
   tool's `input` object; for `flach` the action's fields go at the top level of `input`
   (the tool descriptions say the same).

If the list or schema tool is missing or fails, report that and stop. Do not reconstruct a schema
from memory.

## 2. Clarify inputs with the user

- Map what the user gave you to schema fields and list what is still missing. Ask for missing
  required values instead of inventing them. Where the schema has a default, tell the user which
  default will be used so they can override it.
- Confirm units. Convert only with an explicit, stated factor (for example kNm to Nm), and show the
  converted value back to the user.
- Materials: when the app expects a material identity, use the material service from the list
  (`search`, then `resolve`) and let the user choose if the result is ambiguous (the service answers
  409 with candidate IDs). It returns identities only, not property values.
- Do not fill engineering data (load factors, surface roughness, notch geometry, material strengths,
  catalogue ratings) from your own knowledge unless the user explicitly asks you to, and then name the
  value and its source as the user's assumption.

## 3. Check before calculating

If the app's actions include `validate-input`, call that tool first; if they include
`export-input` or `prepare-payload`, you may use it to show the user the normalised or completed
input. These are read-only. Fix reported problems with the user, then call the `solve` (or `study`)
tool once.

Calculating tools count against the user's calcing plan. Do not call them repeatedly to try
variants unless the user asks for that.

## 4. Report the result

- Report the values the app returned, with the units the app uses, and name the governing results
  the user asked for (for example safety factors against their required minimum, if the result
  states one).
- Show every warning, note or message the result carries, in substance and without softening it.
- Show the provenance the result returns (app, version, standard edition, if present).
- Make no statement about standard conformity, verification or approval beyond what the result itself
  says. The user remains responsible for checking the result professionally before using it.
- Do not paste the full raw response unless asked; offer it.

## 5. Errors: report, never replace

When a tool call fails, tell the user what the tool said and stop that calculation. **Never replace a
failed calculation with your own estimate, hand calculation or typical values**, not even as an
approximation.

The connector returns errors as JSON with an `error` code, the HTTP status and a message. Codes
observed or documented for this server:

| Code | Meaning | What to do |
|---|---|---|
| `sign_in_required`, `token_missing`, `token_invalid`, `token_revoked`, `unauthorized` | Not signed in, or the connection was revoked | Ask the user to connect or reconnect the calcing connector (sign in with their calcing account) |
| `trial_exhausted` | The first sign-in credit is used up or expired | Tell the user; pass on the `upgrade_url` from the answer unchanged, if present. Do not promote a plan |
| `credits_exhausted` | The credit balance does not cover a batch run or a report (single calculations use no credits) | Tell the user; do not retry. Pass on the `upgrade_url` unchanged, if present. Do not promote a plan |
| `ai_solve_not_enabled`, `ai_tokens_not_enabled`, `forbidden` | The account's plan does not allow this | Tell the user |
| `scope_missing` | The connection was granted without this action | Ask the user to reconnect and grant the requested access |
| `rate_limited` | Too many requests | Wait `retry_after_seconds` before one retry |
| `input_required` | Input missing or invalid | Use `missing_required` / `invalid_fields` from the answer to ask the user, then validate again |
| `not_found` | Unknown app, bearing designation, material, ... | Tell the user and ask for a correct identifier |
| `internal_error`, `unavailable`, or no code | Server problem | Tell the user; suggest trying later or contacting info@calcing.de |

For a code not in this table, report it verbatim. If the connector itself is unreachable, say so.

## 6. Store a run or create a report - only when the user asks

- If the app's actions include `runs`, the tool named there (for example `calcing_save_run_screw`)
  calculates AND stores the result as a new run in the user's calcing account. Every call adds another
  run. Use it only when the user asks to keep the calculation, call it once, and report the returned
  `run_id`.
- The report tools of the `reports` service create a report: `app-report` for one app (from a
  `run_id` or from an `input`), `collected-report` over several stored runs (`run_ids`, in order).
  In a chat, request `'format': 'ascii'`. PDF, Word, Excel and HTML are too large for a chat; for these
  formats point the user to the app in the calcing interface at saas.calcing.de.
- A report books its price once per calculation from the account's credits; further formats and
  languages of the same calculation cost nothing. Tell the user before creating one. If the answer is
  `credits_exhausted`, follow section 5.

To pass a result on to a second app, follow the `result-handoff` skill.
