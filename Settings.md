# App Settings

## General
### Queue theme
Choose how the job queue is displayed.

### Save Sushi sync logs
Save Sushi sync logs to the app data folder in your Documents library.

### Save Aegisub-CLI resample logs
Save subtitle resample logs to the app data folder in your Documents library.

### Save MKVMerge logs
Save merge logs to the app data folder in your Documents library.


## Subtitle Sync
### Use high quality resampling (better sync accuracy)
Use 24kHz resampling during sync for potentially better timing accuracy.
This can increase processing time.

### Allow advanced Sushi arguments
Enable access to Advanced Sushi Arguments settings from the App Settings menu.


## Merge - Workflow
### Merge automatically on sync completion
Automatically merge completed video sync jobs after sync (requires MKVMerge).

### Resample synced sub before merge
Run subtitle resampling before merge (requires Aegisub-CLI).

### Delete generated subtitle files after merge
Delete generated subtitle outputs after successful merge.


## Merge - Source
### Copy attachments
Copy attachments (fonts, cover art) to output video.


### Copy chapters 
Copy timestamps to output video.

### Copy global tags
Copy global metadata to output video.

### Copy track tags
Copy tags from all tracks to output video.


## Merge - Sync Target
### Copy only selected sync audio track
Copy only the audio track selected for sync from the target file.

### Copy attachments
Copy attachments (fonts, cover art) to output video.

### Copy chapters
Copy all timestamps to output video.

### Copy subtitles
Copy all subtitles from this file to output video. Useful if you want to append the synced subtitle to a list of other subs in the video.

### Copy global tags
Copy global metadata to output video.

### Copy track tags
Copy tags from all tracks to output video.


## Merge - Synced Subtitle
### Set default flag
Set subtitle as default track in output video.

### Set forced flag
Set subtitle as forced in output video. Useful for Signs/Songs subtitles.

### Use custom track name
Set a default track name for all merge processes.

### Default track name
Track name that will be used as default for all merge processes.