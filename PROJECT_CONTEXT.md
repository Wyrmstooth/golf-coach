# Golf Dashboard Project Context

This repository contains an end-to-end golf swing analysis system built around video ingestion, biomechanical feature extraction, fault scoring, ball tracking, and report generation.

## What The System Does

The app accepts a swing video, analyzes it with pose and vision models, scores the motion against learned swing patterns, estimates ball-flight performance, and renders a detailed user-facing report. The report includes phase timing, fault summaries, swing quality, ball trajectory, annotated video playback, and visual snapshots from key swing moments.

## Core Analysis Pipeline

The main analysis flow lives in `analyze_video.py` and the supporting detector and training modules under `models/`, `utils/`, and `training/`.

The pipeline covers:

- swing phase detection
- pose landmark extraction and feature engineering
- fault classification and severity scoring
- ball tracking and trajectory estimation
- performance prediction for carry, distance, and ball speed
- report assembly with plots, screenshots, and video artifacts

## Training And Calibration Work

The project includes a curated swing dataset built from good and bad swings, plus calibration scripts and training pipelines used to tune the system.

Important training and calibration pieces:

- `training/prepare_train_test_split.py` for dataset preparation
- `training/run_pytorch_training_pipeline.py` for model training workflows
- `training/train_pytorch_models.py` for supervised training of the predictive models
- `_good_swing_ranges.py` for calibrating the good-swing feature windows
- `training_data/` for the swing dataset and statistics
- `CaddieSet.csv` and the `good_swings/` / `bad_swings/` video sets as source material for feature extraction

The calibration work was focused on making the fault scoring more realistic for live swings, especially around address, spine angle, armpit position, and lead-leg behavior.

## Output And Reporting Design

The reporting layer originally saved plots and screenshots as files and served them from backend file routes. That created avoidable 404s and made deployment more fragile.

The current direction is to keep the report self-contained by embedding generated plot and screenshot images as data URIs inside the analysis result. That reduces filesystem dependence and makes the frontend render results directly from the analysis response.

## Frontend Experience

The React frontend under `frontend/` renders the analysis experience with:

- upload flow and progress reporting
- animated result cards and phase timelines
- fault breakdowns and performance metrics
- ball trajectory visualization
- annotated video playback
- PDF export of the analysis report

The frontend now prefers inline image data for screenshots and plots, with older file-based URLs kept only as a fallback for legacy reports.

## Backend And Deployment

The FastAPI backend under `backend/` handles authentication, session storage, analysis endpoints, and job history.

Deployment decisions were simplified to keep the system practical on low-cost hosting:

- frontend stays on Render
- backend deploys on Railway
- PostgreSQL is used for persistent application data
- no extra worker service is required in the simplified deployment path

The Railway guide in `DEPLOY_RAILWAY.md` reflects that setup and emphasizes that the frontend API base URL must end with `/api`.

## Authentication And Route Protection

The app includes auth guards for protected features such as live analysis and swing analysis access. The protected routes and backend checks were added to keep expensive or sensitive features behind login.

## Current Status

The project is now structured around a clean user flow:

1. upload a swing video
2. analyze the swing
3. compute phase timing, fault scoring, ball tracking, and performance estimates
4. render the report with inline visual outputs
5. optionally export the result as a PDF

## Notes For Future Work

- Keep the report schema in sync between backend and frontend when adding new output fields.
- Prefer inline data for lightweight generated visuals whenever possible.
- Keep heavy model artifacts and training outputs documented so calibration changes are easy to trace.