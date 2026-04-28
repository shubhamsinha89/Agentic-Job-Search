# Scoring Rubric

Each job listing is scored out of 45 points across 5 dimensions.
Adjust weights in `config/search_config.yaml` under `scoring:`.

## Dimensions

| Dimension | Max Score | What it measures |
|---|---|---|
| Location match | 12 | How close the job location is to the candidate's preferred cities |
| Role type match | 15 | How well the job title/type aligns with target roles |
| Industry match | 8 | Whether the company's industry matches the candidate's background |
| Experience fit | 5 | Whether the required experience range suits the candidate |
| Posting freshness | 5 | How recently the job was posted |
| **Total** | **45** | |

## Location Scoring (example — customise in config)

| Location | Score |
|---|---|
| Top priority city | 12 |
| Second priority | 10 |
| Third priority | 8 |
| Fourth priority | 7 |
| Fifth priority | 6 |
| Sixth priority | 5 |
| Any other India | 2 |

## Role Type Scoring (example)

| Role | Score |
|---|---|
| Exact target role | 15 |
| Senior variant of target | 13–14 |
| Related leadership role | 11–12 |
| Partial match | 8–10 |
| Generic HR role | 6–8 |

## Industry Scoring (example)

| Industry | Score |
|---|---|
| Primary industry match | 8 |
| Secondary industry match | 7 |
| Tertiary match | 6 |
| General manufacturing | 5 |
| Non-matching industry | 2 |

## Experience Fit Scoring

| Required range | Score |
|---|---|
| Exactly matches candidate years | 5 |
| ±2 years of candidate | 4 |
| ±4 years of candidate | 3 |
| Wide range including candidate | 2 |
| Not specified | 1 |

## Freshness Scoring

| Posted | Score |
|---|---|
| Today | 5 |
| Last 3 days | 4 |
| Last 7 days | 3 |
| Last 14 days | 2 |
| Older than 14 days | 1 |

## Interpreting Scores

| Score range | Interpretation |
|---|---|
| 38–45 | Excellent match — apply immediately |
| 30–37 | Strong match — worth applying |
| 22–29 | Moderate match — review carefully |
| Below 22 | Weak match — included only if top 20 pool is thin |
