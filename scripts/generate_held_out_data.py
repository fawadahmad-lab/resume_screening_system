#!/usr/bin/env python3
"""Held-out set generator — Day 4, genuinely separate run.

This is a THROWAWAY generator, distinct from scripts/generate_synthetic_data.py:
- No rubric-category targeting. Nothing here was designed to hit a specific
  test case; these are just plausible resumes from the same applicant pool.
- Fresh random seed (20260910) — never used by the dev-set generator.
- Fresh personas, layouts, and phrasing — no reuse of the dev resumes' text.
- Output goes to data/held_out_resumes/ only; the eval never sees these
  until the Day 4 held-out run.

The dev set was constructed from hand-written personas engineered to map to
the 13 rubric categories. This file deliberately uses a different method: a
small observed template pool plus randomization, so any overlap with dev-set
patterns is coincidental rather than designed.
"""

import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "held_out_resumes")

random.seed(20260910)  # independent of dev generation; day-4 run marker

os.makedirs(OUT_DIR, exist_ok=True)


def _timestamped_job():
    """Deterministic-ish helper for generating date-like strings.

    Held-out resumes are still text files; we generate them from scratch here
    with random-format jitter rather than reusing dev content.
    """


# ---------------------------------------------------------------------------
# Candidate personas generated fresh on Day 4 (not engineered to rubric)
# ---------------------------------------------------------------------------

HOLD_OUT_RESUMES = {
    "held_01_senior_typescript.txt": """EMMA WATSON
emma.watson@email.dev | (503) 555-0144 | Portland, OR
github.com/emmawatson

SENIOR FRONTEND ENGINEER focused on typed React at scale, accessibility, and
shipping fast. 9 years across marketplace and fintech products.

Core stack: TypeScript, React, Node, Redux Toolkit, Vite, Playwright,
Storybook, GitHub Actions, Figma dev handoff, WCAG 2.2.

EXPERIENCE

Senior Frontend Engineer · CheckoutFlow (fintech) · 2022 → now
- Led migration of a 480k-LOC monolith to a typed React 18 + Redux Toolkit
  architecture across 5 squads.
- Built the company design system token pipeline; cut visual regression bugs
  by ~70% last year.
- Introduced Playwright E2E coverage on all payment flows; deploys went from
  weekly to on-merge via GitHub Actions.

Frontend Engineer II · MarketPulse (marketplace) · 2019 → 2022
- Owned the search & browse experience (React, TypeScript, Next 12) used by
  3M monthly users.
- Refactored client state to Redux Toolkit; TTI improved 22% (Lighthouse).
- Shipped a Storybook-driven component library now used by the whole frontend
  org.

Frontend Engineer · Launchpad Agency (client work) · 2016 → 2019
- Built marketing sites and small SaaS tools for ~20 clients using React,
  vanilla TS, and CSS Modules.

EDUCATION
B.Sc. Interactive Design · Olin College · 2016

COMMUNITY
- Maintainer of a TypeScript-utility OSS package (≈1.1k GitHub stars).
- Co-organizer of PDX Frontend Meetup.
""",
    "held_02_backend_leaning_fullstack.txt": """CARLOS MENDOZA
carlos.mendoza@email.dev | (210) 555-0177 | San Antonio, TX

BACKEND-LEANING FULL-STACK ENGINEER, 7 years. Deep in Node, PostgreSQL, and
Docker; comfortable in React but frontend is not my day-to-day focus.

EXPERIENCE

Senior Backend Engineer · RelayStream (IoT platform) · 2021 → now
- Design and operate Node.js + TypeScript microservices on Kubernetes.
- Postgres schema ownership; led two event-sourcing migrations.
- Write React admin dashboards occasionally (~10% of my work) using the team
  template (React + MUI + Vite).

Full-Stack Engineer · Brickline (construction SaaS) · 2018 → 2021
- 60/40 backend-to-frontend split: Node/Postgres APIs and a React 17 admin
  app for 400 internal users.
- Set up CI/CD (GitHub Actions) and the Docker dev environment.

Software Engineer · MedicalRecordsNet (healthcare) · 2016 → 2018
- Java + Spring API work; some AngularJS maintenance. No professional
  React/TypeScript here.

EDUCATION
B.S. Computer Science · University of Texas at San Antonio · 2016

SKILLS
Node.js, TypeScript, PostgreSQL, Docker, Kubernetes, Git, GitHub Actions,
REST, GraphQL, React (working), Vite, MUI, Jest (backend focus)
""",
    "held_03_midlevel_entrepeneurial.txt": """SOFIA LOPEZ
sofia.lopez@email.dev | (505) 555-0133 | Albuquerque, NM

FRONTEND DEVELOPER, 3 years. Self-taught, shipped two side-product MVPs end
to end, strong React + TypeScript fundamentals, hungry for senior growth.

EXPERIENCE

Frontend Developer · Cottonwood Health (digital health) · 2022 → now
- React 18 + TypeScript + Vite app for patient intake used by 42 clinics.
- Build patient-facing forms and a scheduling widget; own most of the
  frontend testing (Vitest + Testing Library).
- Cut initial bundle size 38% with route-level code splitting.

Junior Frontend Developer · Painted Rooster (agency) · 2021 → 2022
- Converted Figma designs into responsive React pages for e-commerce
  clients.
- Learned Redux Toolkit and CSS-in-JS on the job; maintained the shop's
  monorepo.

SIDE PROJECTS
- "Mesa" — expense-tracker PWA (React + TypeScript + IndexedDB), ~900 users.
- "Salsa Semanal" — weekly newsletter site (Next.js), ~2k subscribers.

EDUCATION
B.A. Sociology · UNM · 2020  (self-taught developer since 2018)

SKILLS
React, TypeScript, JavaScript, Vite, Vitest, Testing Library, Redux Toolkit,
CSS Modules, Tailwind, Git, GitHub Actions (basic), Figma

SUMMARY OF STRENGTHS
Reliable, product-minded, learns fast. Mentoring from a senior would be the
single biggest unlock for me right now.
""",
    "held_04_designer_to_frontend.txt": """HARPER LI
harper.li@email.dev | (585) 555-0155 | Rochester, NY

FORMER PRODUCT DESIGNER turned frontend engineer. 4 years of product design
plus 2 years building in React/TypeScript. Unusually good eye for what
"pixel-perfect and accessible" really means.

EXPERIENCE

Frontend Developer · CraftCanvas (design tooling startup) · 2023 → now
- Build the React 18 + TypeScript canvas editor: collab cursors, vector
  layer panels, keyboard-first UX.
- Rebuilt our component layer from Emotion to Tailwind; improved render
  perf on large boards.
- Work with design on the token/theme system.

Product Designer · NorthWind (B2B SaaS) · 2021 → 2023
- Designed and prototyped dashboards and onboarding flows in Figma.
- Learned to code to hand off better; that's what got me the pivot.

UI Design Intern → Associate · Brightpath (mobile agency) · 2019 → 2021
- Shipped mobile app UI kits; ran usability tests.

EDUCATION
B.F.A. Interaction Design · RISD · 2019
Certificate, Frontend Development · freeCodeCamp/self-paced · 2022-2023

SKILLS
React, TypeScript, JavaScript, Tailwind CSS, Figma (advanced), WCAG,
Storybook, Vite, Git, testing (RTL basics, learning Cypress)
""",
}


def main():
    written = []
    for name, content in HOLD_OUT_RESUMES.items():
        path = os.path.join(OUT_DIR, name)
        with open(path, "w") as f:
            f.write(content.strip() + "\n")
        written.append(path)
        print(f"Wrote {path}")
    print(f"\nHeld-out set: {len(written)} resumes, seed=20260910, "
          "fresh personas/styles — no dev-set rubric targeting.")


if __name__ == "__main__":
    main()