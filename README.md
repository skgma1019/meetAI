# meetAI

`meetAI` is a public speaking and interview coaching project built on top of the extracted Korean public speaking dataset in this repository.

## Product Direction

The shortest path to a useful MVP is:

1. Linguistic coaching first
2. Nonverbal coaching second
3. Unified feedback report last

Why this order works:

- The linguistic labels already contain transcripts, fluency signals, speed, voice-quality scores, and expert grades.
- The nonverbal labels contain pose-style keypoints that are strong for gesture and posture detection, but they are better added after the language pipeline is stable.

## Current Scaffold

This repository now includes a preprocessing script that converts the extracted JSON labels into tabular manifests:

- `data/processed/linguistic_manifest.csv`
- `data/processed/nonverbal_manifest.csv`
- `data/processed/dataset_summary.json`

## How To Run

From the repository root:

```powershell
python .\scripts\build_dataset_manifests.py
```

If you use the Windows launcher:

```powershell
py -3 .\scripts\build_dataset_manifests.py
```

## API Quick Start

Run the API server:

```powershell
uvicorn app.main:app --reload
```

Try the endpoints:

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/docs`

Sample request payloads are included here:

- `data/samples/language_request.json`
- `data/samples/nonverbal_request.json`
- `data/samples/full_request.json`

You can send all sample requests with:

```powershell
.\scripts\run_sample_requests.ps1
```

If PowerShell encoding is inconvenient, use CMD:

```cmd
scripts\run_sample_requests.cmd
```

Optional arguments:

```powershell
python .\scripts\build_dataset_manifests.py --repo-root G:\meetAI --output-dir G:\meetAI\data\processed
```

## What The Script Produces

The linguistic manifest includes fields such as:

- speaker metadata
- presentation metadata
- transcript counts
- disfluency tag counts
- averaged expert scores for repeat, filler words, pause, wrong words, voice quality, and speaking speed

The nonverbal manifest includes fields such as:

- clip metadata
- duration and resolution
- annotation segment counts
- average keypoint counts
- average frame counts
- inferred nonverbal label codes

## Language Baseline

Build the manifest first, then prepare language features, then train the baseline model:

```powershell
python .\scripts\build_dataset_manifests.py
python .\scripts\prepare_language_features.py
python .\scripts\train_language_baseline.py
```

Generated files:

- `data/processed/language_features.csv`
- `data/processed/language_features_summary.json`
- `outputs/checkpoints/language_baseline.json`

The baseline checkpoint now includes train and validation metrics for:

- `MAE`
- `RMSE`
- `R²`
- `within_0_5_ratio` for predictions within `±0.5` grade points
- `grade_match_rate` based on the nearest canonical expert-grade bucket

## Recommended MVP

Build the first version of the coach in two passes:

1. Audio or transcript input
2. Coaching report generation

First model targets:

- filler-word severity
- repetition severity
- speaking-speed band
- pronunciation or wrong-word risk
- overall expert-grade regression or classification

Then add a video model for:

- head movement
- posture stability
- distracting hand movement
- gesture frequency

## Suggested System Design

- `preprocess`: build manifests from raw JSON
- `train/linguistic`: train a tabular or text-plus-feature model
- `train/nonverbal`: train a pose or sequence model
- `app/api`: expose scoring endpoints
- `app/report`: generate human-readable coaching feedback

## Immediate Next Step

The next sensible move is to run the preprocessing script and inspect the generated manifests. After that, we can build:

1. a baseline linguistic score predictor, or
2. a FastAPI scoring service that turns transcript and video features into coaching feedback
