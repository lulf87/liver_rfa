# liver_rfa

A simulation-led planning study for **perivascular liver radiofrequency ablation (RFA)** using a low-complexity 2D electro-thermal-damage model with **shape-based endpoints**.

## Project goal

This repository develops and documents a reproducible computational workflow for studying how **tumor-vessel gap**, **vessel diameter**, and **power–time protocol** affect:

- tumor coverage ratio (**TCR**)
- margin deficit index (**MDI**)
- vessel-side undercoverage angle (**VUA**)
- target specificity (**PPV_target**)

The project is organized as a sequence of stages, from minimal geometry tests to final frozen simulation results and submission-ready figures.

## Manuscript framing

**Working title**

**A low-complexity planning model for perivascular liver radiofrequency ablation: shape-based assessment of safety-margin deficit and protocol trade-offs**

## Repository structure

```text
liver_rfa/
├── docs/                    # repository-level utilities and notes
├── manuscript/              # normalized figures, tables, manifests, and notes
├── papers/                  # versioned manuscript packages by revision stage
└── simulation/              # stage-wise simulation workflow

The `papers/` directory stores revision-specific manuscript packages (e.g., `V9/`), while `manuscript/` stores repository-level normalized figures, tables, and notes.