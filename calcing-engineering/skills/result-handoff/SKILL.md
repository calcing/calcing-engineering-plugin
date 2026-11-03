---
name: result-handoff
description: Pass the result of one calcing calculation on as the input of another calcing app (saas.calcing.de connector). Use when the user wants a follow-up calculation from a result they just got, for example "now check the key on this shaft" or "use this bearing result in the next step".
---

# Hand a calcing result on to the next app

The calcing connector has a result hand-off service. Find it in the `services` of the list tool
(`calcing_list_apps`): it names its actions (`dry-run`, `execute`), their tools and their
`required_fields` (`from_app`, `to_app`). Its `body_shape` is `flach`: the fields go at the top
level of the tool's `input` object. Use only the tools the list names.

1. **Source.** The source is a complete calculation result envelope returned by a calcing `solve`
   (or hand-off `execute`) call in this conversation. Pass it as `from_result`, with `from_app` set to
   that app's `registry_key` and `to_app` to the target app's `registry_key`. Do not edit or shorten
   the envelope, and do not build one by hand.
2. **Dry run first.** Call the `dry-run` tool. It prepares the transfer without calculating and
   reports the target's missing required fields. Show the user which values were transferred and which
   are missing.
3. **Missing values.** Ask the user for each missing value with its unit. Do not fill them yourself.
4. **Execute.** Only when nothing required is missing and the user agrees, call the `execute` tool.
   It transfers and calculates, and returns the target's full envelope, which can be the next step's
   `from_result`.
   If the user's missing values cannot be passed in the hand-off call, run the target app through the
   `engineering-calculation` skill instead (schema, validate, solve), starting from the inputs the
   dry run prepared.
5. **Report** the target's result as the `engineering-calculation` skill describes: values with units,
   every warning and note, provenance, no conformity claims beyond what the result says.

If a hand-off call fails, report the `error` code and message and stop. Never substitute an estimated
value for a failed transfer or calculation. `execute` calculates and counts against the user's plan;
`dry-run` is read-only.
