# System Architecture

`meetAI` is designed as a multimodal coaching system with three stages:

1. modality-specific preprocessing
2. modality-specific scoring
3. multimodal report generation

## Planned Flow

1. Input audio, video, or transcript
2. Build linguistic and nonverbal features
3. Run separate scorers
4. Merge outputs into a final coaching report
