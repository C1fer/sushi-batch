<!-- toc -->
# Sections

*Navigate to the main documentation blocks below.*

- [App settings](#app-settings)
- [Advanced Sushi Args](#advanced-sushi-args-settings)
- [Encode settings](#audio-encode-settings)

<!-- app-settings -->
# App Settings

*Corresponds to the main application settings screen.*

## General
### Queue theme
Choose how the job queue is displayed. Supporthed themes are: `Classic`, `Card` and `YAML-Like`.

### Save Sushi Sync Logs
Save logs for each subtitle sync operation.

### Save Merge Logs
Save logs for each merge operation.


## Subtitle Sync
### Use High Quality Resampling (Improved Accuracy)
Use 24 kHz resampling during sync for potentially better timing accuracy. Can increase processing time.

### Allow Advanced Sushi Arguments 
Enables custom Sushi argument overrides for advanced synchronization tuning. [Args Settings](#advanced-sushi-args-settings)


## Merge: Workflow
### Merge Automatically on Sync Completion
Automatically merge completed sync jobs after sync (requires MKVMerge).

### Encode Lossless Audio Before Merging
Re-encode selected lossless tracks to the chosen codec before merging. [Encode Settings](#audio-encode-settings)

### Tracks to Encode Before Merging
Defines which audio tracks to encode before merging when pre-merge audio encoding is enabled.

### Encode Codec
Target lossy codec for re-encoding when pre-merge audio encoding is enabled. Supported codecs are `AAC`, `EAC-3` and `Opus`.

### Resample Synced Sub Before Merge
Resample the synced subtitle to match target video resolution before merging. (Requires Aegisub-CLI)

### Delete Generated Audio/Subtitle Files After Merge
Remove temporary generated subtitle/audio files automatically after merge completes.


## Merge: Source
### Copy Attachments
Copy attachments (fonts, cover art) from the source file into the merged output.

### Copy Chapters 
Copy chapter entries from the source file into the merged output.

### Copy Global Tags
Copy container-level tags from the source file into the merged output.

### Copy Track Tags
Copy per-track metadata tags from the source file into the merged output.


## Merge: Sync Target
### Only Include Track Used for Sync
Exclude all audio tracks from the target file except the one used for sync.

### Copy Attachments
Copy attachments (fonts, cover art) from the target file into the merged output.

### Copy Chapters
Copy chapter entries from the target file into the merged output.

### Copy Subtitles
Copy subtitle tracks from the target file in addition to the synced subtitle.

### Copy Global Tags
Copy container-level tags from the target file into the merged output.

### Copy Track Tags
Copy per-track metadata tags from the target file into the merged output.


## Merge: Synced Subtitle
### Set Default Flag
Mark the merged synced subtitle track as default in the merged output.

### Set forced flag
Mark the merged synced subtitle track as forced in the merged output.

### Override Track Title
Enables overriding the default track title for the merged synced subtitle track.

### Custom Track Title
Custom title for the merged synced subtitle track when override is enabled. (default: `Synced Sub`).



# Advanced Sushi Args Settings 
Used only when **Allow Advanced Sushi Arguments** is enabled. Each value can be set to override its internal default. This menu is accessed by selecting the *Configure Advanced Sushi Arguments* option in the menu. 

- **Window.** Secondary time window (in seconds) used to find matching audio samples.
  - The algorithm first searches for matches within a 1.5-second window in both directions. If no matches are found, it expands the search to this broader window.
- **Max Window.** Largest time window (in seconds) used in the search.
  - If no matches are found within the secondary window and the rewind threshold is triggered, the algorithm performs a final search using this window as a fallback before giving up on finding a match.
- **Rewind Threshold.** Count of consecutive broken search groups before rewinding to the first broken group using the defined max window as a fallback.
- **Smoothing Radius.** Radius of the running median filter used to smooth search group timings.
- **Max Typesetting Duration.** Maximum duration (in seconds) of a line to be considered typesetting.
- **Max Typesetting Distance.** Maximum distance (in seconds) between two adjacent typesetting lines to merge them.


# Audio Encode Settings
Used only when **Encode Lossless Audio Before Merging** is enabled. This menu is accessed by selecting the *Configure Audio Encode Settings* option in the menu.

*Bitrate settings are configured separately for each codec.*

- **Encoder (Opus-exclusive)**. Audio encoder to use for Opus encoding.
  - **libopus**. Default encoder provided by FFmpeg. Suitable for most users.
  - **opusenc**. Official Opus encoder. Recommended for users who want to ensure maximum compatibility with the Opus specification.
- **Mono Bitrate**. Target bitrate for Mono audio tracks.
- **Stereo Bitrate**. Target bitrate for Stereo audio tracks.
- **5.1 Bitrate**. Target bitrate for 5.1 audio tracks
- **7.1 Bitrate**. Target bitrate for 7.1 audio tracks