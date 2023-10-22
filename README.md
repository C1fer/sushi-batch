# Sushi Batch
Batch subtitle synchronization tool based on [FichteFoll](https://github.com/FichteFoll/Sushi)'s fork of [Sushi](https://github.com/tp7/Sushi).

### WARNING
**Sushi is not perfect, an can output subtitles with broken timings.** **You should check if the subtitle was synced correctly on completed tasks with high shift average (10s or greater).**

## Installation

`pip install sushi-batch`

### Required apps
* [FFmpeg](https://ffmpeg.org/download.html)
* [mkvmerge from MKVToolNix](https://mkvtoolnix.download/downloads.html) (Optional)
  
### Windows
Add the required binaries to PATH or install them via a package manager like [Chocolatey](https://chocolatey.org/). You can also copy the executables to the directory from which you run this app (not recommended).

### Linux
Most distros link installed packages to PATH automatically, so just make sure to install the required apps via your distribution's package manager.

## How does Sushi work?
Sushi works by finding the closest similar pattern between a provided source and destination audio track. The obtained shift value is applied to the output subtitle, which will be synced to the destination track.

### Audio-based Sync
You must provide:
* A subtitle file (ASS, SRT, SSA).
* The original audio track for that subtitle.
* A destination audio track to sync the subtitle to.

### Video-based Sync
You only need to provide:
* A source video file which contains a subtitle.
* A destination video file. 

You can select a specific subtitle or audio track from the video files. This allows you to add multi-language subtitles for a specific audio track.

FFmpeg will take care of extracting the audio and subtitle tracks for processing. 

## Usage
This program allows for:
* Batch synchronization of files within selected directories / selected files.
* Queueing of synchronization tasks
* Merging synced subtitles with destination video (more below)

### Folder Structures for Directory Select modes
#### Audio-Sync
<pre>
  <code>
    📂Source Folder
     ┣ 🔊Fullmetal Alchemist - 01 (DVD).flac
     ┣ 📜Fullmetal Alchemist - 01 (DVD).ass
     ┣ 🔊Fullmetal Alchemist - 02 (DVD).flac
     ┣ 📜Fullmetal Alchemist - 02 (DVD).ass
     ┣ 🔊Fullmetal Alchemist - 03 (DVD).flac
     ┗ 📜Fullmetal Alchemist - 03 (DVD).ass
    📂Destination Folder
     ┣ 🔊Fullmetal Alchemist - 01 (BD).flac
     ┣ 🔊Fullmetal Alchemist - 02 (BD).flac
     ┗ 🔊Fullmetal Alchemist - 03 (BD).flac
  </code>
</pre>

#### Video-Sync
<pre>
  <code>
    📂Source Folder
     ┣ 📺Fullmetal Alchemist - 01 (DVD).mkv
     ┣ 📺Fullmetal Alchemist - 02 (DVD).mkv
     ┗ 📺Fullmetal Alchemist - 03 (DVD).mkv
    📂Destination Folder
     ┣ 📺Fullmetal Alchemist - 01 (BD).flac
     ┣ 📺Fullmetal Alchemist - 02 (BD).mkv
     ┗ 📺Fullmetal Alchemist - 03 (BD).mkv
  </code>
</pre>

## Merge synced subs with video
If mkvmerge is installed, the app will automatically merge the synced subtitle to the specified destination video file. The merge can also be started manually inside the *Job Queue* section.

You can customize the arguments used for merging via the app's settings.
