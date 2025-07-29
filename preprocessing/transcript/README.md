# Transcript Registration

This module processes transcript CSV files and registers them with the manifest file.
Please note that the actual transcript generation must be performed with an external tool.
There are many open-sources tools that can be used for speech-to-text transformation, such as:

- **noScribe - https://github.com/kaixxx/noScribe** 
- **whisper-standalone-win - https://github.com/Purfview/whisper-standalone-win**

## Input CSV Format

The transcript must be provided as a CSV file with the following required columns:
Many tools such as the ones mentioned above output subtitle files (.srt or .vtt), which you can transform to the required CSV format using the provided scripts `srt2csv.py` and `vtt2csv.py`.

### Required Columns

- **`speaker`** - Identifier for the speaker/participant (must match recording IDs in the manifest)
- **`text`** - Speaker utterance 
- **`start timestamp [sec]`** The start timestamp of the speaker utterance (in seconds)
- **`end timestamp [sec]`** The end timestamp of the speaker utterance (in seconds)

## Usage

```bash
python register_transcript.py --manifest <path_to_manifest.json> --transcript <path_to_transcript.csv> --out_dir <output_directory>
```

### Arguments

- `--manifest` - Path to the reCAPit manifest JSON file
- `--transcript` - Path to the input transcript CSV file
- `--out_dir` - Directory where individual transcript files will be saved

## Output

The script generates:
- Individual transcript CSV files for each recording in `<out_dir>/<recording_id>/transcript.csv`
- Updates the manifest file with transcript artifact references
