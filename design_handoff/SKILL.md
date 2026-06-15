---
name: indcric-design
description: Use this skill to generate well-branded interfaces and assets for IndCric — the Indian Cricket Ghent (ICG) cricket-club management app. Contains essential design guidelines, colors, type (Inter), fonts, sport assets (bat / ball / cricket-ball glyph), and a React UI kit for the web app. Use it for production code AND for throwaway prototypes, slides, WhatsApp share cards, member microsites — anything that needs to look like IndCric.
user-invocable: true
---

Read `README.md` first — it covers the brand, voice, visual foundations,
iconography, and an index of every file in the system.

Then explore the rest:

- `colors_and_type.css` — every token (pitch green ramp, stone neutrals,
  amber accent, type scale, spacing, radii, shadows, motion) as CSS vars.
- `assets/` — the bat and ball PNGs.
- `preview/` — small reference cards for each foundation and component.
- `ui_kits/indcric_web/` — working React + Babel-in-browser recreation of
  the web app (login, dashboard, session, profile, payments). See its own
  `README.md` for the component map.

## When invoked

If you are creating **visual artifacts** (slides, mocks, one-off
prototypes), copy the assets you need out of `assets/` and the JSX files
out of `ui_kits/indcric_web/`, then build static HTML files for the user
to view. The Babel-in-browser setup in `ui_kits/indcric_web/index.html` is
the simplest way to bootstrap.

If you are working on **production code** (the actual Indcric Django app),
read the rules here to become an expert in the brand, then write changes
directly against `templates/base.html` and the existing Tailwind utilities
in that repo (<https://github.com/Bhanu-py/Indcric>) — those already
encode the same tokens.

If the user invokes the skill **without further guidance**, ask them what
they want to build or design (a new screen? a poll-share image for
WhatsApp? a member-onboarding microsite? a captain's-pick announcement
card?), ask a couple of follow-up questions about audience and surface,
and then act as an expert designer who outputs either polished HTML
artifacts or production code.
