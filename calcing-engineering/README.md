# CalcIng Engineering

Mechanical engineering calculations from a conversation with Claude. The plugin connects Claude to
the calculation apps of [saas.calcing.de](https://saas.calcing.de/) and adds two skills that tell
Claude how to use them: find the right app, clarify missing inputs and units with you, let the app
check the inputs, calculate, and report the app's result together with its warnings and provenance.

The numbers come from the calcing apps on our server, not from Claude. If a calculation cannot run
(not signed in, no plan, invalid input, server error), the skills tell Claude to report the
error and not to replace the result with an estimate of its own.

## What is included

- **Connector** `calcing`: the remote MCP server `https://saas.calcing.de/mcp` (Streamable HTTP,
  OAuth 2.1 sign-in with your calcing account).
- **Skill `engineering-calculation`**: guided calculation with any calcing app the connector
  lists. At the time of writing these are shafts and axles (DIN 743), parallel keys (DIN 6885 /
  DIN 6892), interference fits (DIN 7190-1), ISO fits (ISO 286), bolted joints (VDI 2230), rolling
  bearing life (ISO 281) and detailed rolling-bearing analysis (DIN 26281), shaft-bearing systems,
  rolling contacts, planetary gear stages (DIN 3990 Part 21), FKM strength assessment, district-heating
  branches (EN 13941-1), axial fans, horizontal- and vertical-axis wind turbines, plus material lookup.
  The skill reads the current list from the connector instead of relying on a fixed set.
- **Skill `result-handoff`**: passes the result of one app on as the input of the next app
  (dry run first, then execute).

## Setup

**claude.ai and Cowork:** add the plugin, open its **Connectors** tab and connect `calcing`.
**Claude Code:** install the plugin, then run `/mcp`, select `calcing` and authenticate.

### Signing in (what you see)

Connecting opens saas.calcing.de in your browser. Sign in with your calcing account (or register).
A consent page then asks **"Allow access for <platform>?"**, shows the provider, your account and
the list of actions the platform may perform on your behalf (for example "check inputs" or
"calculate" per app), and notes that calculations through the platform use no credits. Select
**Allow** to finish;
you are returned to Claude. Without signing in, the connector offers no tools.

### Who can use it, and what it costs

- Anyone using Claude can install the plugin. Installing it is free.
- Calculations need a calcing account on saas.calcing.de: you sign in when you connect the connector.
- Calculations through Claude **use no credits**. They require a plan, **Basic** or higher; there is
  no separate quota for AI platforms (terms, section 10 (2)). Plans:
  [saas.calcing.de/?plans=1](https://saas.calcing.de/?plans=1).
- New accounts can try the connection while their first sign-in credit is valid and not used up;
  calculations through Claude do not use it. After that, further calculations need a plan.
- Without a valid first sign-in credit or plan, the tool answers with the error `trial_exhausted`
  (with a link to the plan overview) and Claude reports it; nothing is calculated or estimated.

## Example requests

This request contains everything the app needs:

- "Deep groove ball bearing 6206 (C = 21.4 kN, C0 = 11.3 kN), purely radial 5 kN at 1500 rpm,
  reliability 90 %. How long does it last?"

The following start a calculation but **need further inputs**. Claude will ask for them before the
app can calculate, for example the material from the app's material database and the effective
diameter (shaft), chamfers and fit details (key), further joint and thread data (bolt) or tool and
geometry data (planetary stage). With other values than the full worked example, the result differs
from it:

- "Check my key connection: shaft Ø 120 mm of C60+N, key form A 32 × 18 × 125 of C45+C, hub of
  EN-GJL-250 (Ø 200/270 mm), nominal torque 4 kNm, peak torque 15 kNm in both directions, application
  factor 1.5. Does the surface pressure hold?"
- "Strength assessment of a stepped shaft: D = 50 mm, d = 42 mm, fillet radius 5 mm, 34CrMo4 quenched
  and tempered (σB = 1000 N/mm², σS = 800 N/mm²), Rz 5 µm, bending 500 ± 50 N/mm², torsion
  100 ± 30 N/mm². What are the safety factors?"
- "Bolt on a hydraulic cylinder: socket head cap screw M12 × 60, 10.9, screwed into C45, clamped part
  16MnCr5 with 42 mm clamp length, pulsating axial working load up to 24.9 kN, minimum clamp load 1 kN,
  friction coefficients 0.10, tightening factor 1.8. Which tightening torque, which safety factors?"
- "Planetary stage behind a steam turbine: 5000 kW, sun 12 477 rpm, fixed carrier, 3 planets, double
  helical mn = 3.5 mm, β = 31.01°, tooth numbers sun 22, planet 69, ring −161, face width 180 mm,
  application factor 1.25, load sharing 1.25. Tangential force and contact ratios at planet and ring
  gear?"

## Data

The plugin itself contains only instructions and the connector address; it runs no code on your
machine and stores nothing. When Claude calls a calcing tool, the plugin sends the inputs of that call
(for example dimensions, loads, materials) to saas.calcing.de over HTTPS, together with the access
granted at sign-in. The server returns the result, notes and error messages to Claude. Our server
logs each call (time, app, action, result) to charge it to your plan. Details: privacy policy,
section 2.8 ([saas.calcing.de/?legal=privacy](https://saas.calcing.de/?legal=privacy)); terms,
section 10 ([saas.calcing.de/?legal=terms](https://saas.calcing.de/?legal=terms)). Claude processes
your conversation under Anthropic's terms.

You remain responsible for your inputs and for checking every result professionally before use.

## Revoking access

In saas.calcing.de, open **API & Skills → Connected AI platforms → Revoke access**, or disconnect
the connector in Claude.

## Support

- Documentation: [saas.calcing.de/?ki](https://saas.calcing.de/?ki)
- E-mail: info@calcing.de (also for security reports)
- Provider: CalcIng - Müller Engineering Solutions GmbH, Gewerbepark 10a, 36160 Dipperz, Germany
  ([imprint](https://saas.calcing.de/?legal=imprint))

## License

The plugin files (instructions, manifest, connector configuration) are licensed under the
[MIT License](LICENSE). The calcing service on saas.calcing.de is not part of this license; its use
is governed by the terms of saas.calcing.de.

**Trademarks:** the name and logo "CalcIng" / "calcing" (including the plugin icon) are not
licensed under the MIT License. They may not be used to identify other products or services without
written permission of CalcIng - Müller Engineering Solutions GmbH.

---

## Kurzfassung (Deutsch)

Das Plugin verbindet Claude mit den Berechnungs-Apps von saas.calcing.de. Claude ermittelt die
passende App, klärt fehlende Eingaben und Einheiten mit Ihnen, lässt die App prüfen und rechnen und
gibt deren Ergebnis mit Warnungen und Herkunft wieder — ohne eigene Schätzwerte. Anmeldung mit Ihrem
calcing-Konto (OAuth). Installieren kann jeder Claude-Nutzer; gerechnet wird nur mit Anmeldung und Plan
(Testphase mit dem Erstanmeldungs-Guthaben, danach ab Plan Basic); Rechnungen über Claude
verbrauchen keine Credits. Lizenz der Plugin-Dateien:
MIT; Name und Logo „CalcIng“ sind nicht Teil der Lizenz. Widerruf unter
**API & Skills → Verbundene KI-Plattformen**. Datenschutz: Abschnitt 2.8, AGB: § 10. Kontakt:
info@calcing.de.
