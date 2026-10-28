---
name: ec-setup
description: Reproduce Conforma image validation locally from a log by extracting its snapshot, policy configuration, and verification key.
---

# EC Validation Debugging Setup

Set up a local debugging environment by extracting configuration from a Conforma validation log to reproduce the `ec validate image` command.

## Input

Provide the path to the Conforma validation log. If it is missing, ask the user for it.

The log contains key sections marked by headers (case-insensitive, sometimes followed by ` :-`):
- `STEP-REDUCE` - Contains the snapshot JSON with the application name and component list
- `STEP-SHOW-CONFIG` - Contains the policy configuration as JSON

## Step 1: Read the Log File

Inspect the provided log file.

## Step 2: Extract the Snapshot

Locate the `STEP-REDUCE` section (match case-insensitively, it may appear as `STEP-REDUCE` or `step-reduce :-`). Parse the JSON block that follows — it contains a snapshot with `application` and `components` fields.

Build a snapshot JSON containing only the top-level image references. Each component needs only `name` and `containerImage`. Do **not** include architecture-specific images — the `ec` command expands image indexes into those automatically.

Example snapshot format:
```json
{
  "application": "my-app",
  "components": [
    {
      "name": "component-a",
      "containerImage": "quay.io/org/image-a@sha256:abc..."
    },
    {
      "name": "component-b",
      "containerImage": "quay.io/org/image-b@sha256:def..."
    }
  ]
}
```

## Step 3: Create Output Directory

Create the output directory under the user's current project or task directory, not alongside the installed skill. Use this naming convention:
```
<policy-source-name>-<application-name>
```

Derive the components from:
- **policy-source-name**: The `name` field from the first source in `STEP-SHOW-CONFIG` (e.g., "release-policies"), slugified to lowercase with hyphens
- **application-name**: The `application` field from the snapshot in `STEP-REDUCE`, slugified to lowercase with hyphens

If `STEP-SHOW-CONFIG` is not present, use just `<application-name>` as the directory name.

## Step 4: Save the Snapshot

Save the snapshot JSON (from Step 2) as `snapshot.json` in the output directory.

## Step 5: Extract the Policy Config

Locate the JSON block following `STEP-SHOW-CONFIG`. Extract the `policy` object and convert it to YAML.

1. Extract only the contents of the `policy` key
2. Remove the `publicKey` field
3. Add a top-level `name` field with a descriptive identifier
4. Save as `policy.yaml` in the output directory

If `STEP-SHOW-CONFIG` is not present in the log, skip this step and Steps 6-7. Inform the user that no policy config was found and they will need to provide their own `policy.yaml` and `key.pub`.

## Step 6: Extract the Public Key

From the same `STEP-SHOW-CONFIG` JSON block, extract the `key` field value.

1. Copy the value of the `key` field (the PEM-encoded public key)
2. Convert escaped newlines (`\n`) to actual line breaks
3. Save as `key.pub` in the output directory

## Step 7: Pull Policy Source Code

Check the `sources[].policy` paths in the extracted `policy.yaml`. For each policy source:

1. If it's an OCI reference (starting with `oci::`), pull it using conftest:
   ```bash
   conftest pull --policy . <OCI_URL>
   ```

   **Important**: Pull to the current directory (`.`) not a subdirectory. The OCI bundle already contains a `policy/` directory internally, so this creates `./policy/release/...` structure.

2. Run the conftest pull command from within the output directory to download the policy Rego files.

3. If the pull fails, inform the user of the error but continue with the remaining setup steps.

4. The resulting structure should be:
   ```
   <output-directory>/
   ├── snapshot.json
   ├── policy.yaml
   ├── key.pub
   ├── run.sh
   └── policy/
       └── release/
           ├── tasks/
           ├── trusted_task/
           └── ...
   ```

## Step 8: Construct the Validation Command

Build the `ec validate image` command and save as `run.sh` in the output directory:

```bash
#!/bin/bash
ec validate image \
  --images snapshot.json \
  --policy policy.yaml \
  -k key.pub \
  --ignore-rekor \
  --output text \
  --strict false \
  --info \
  --debug
```

Make the script executable with `chmod +x run.sh`.

## Step 9: Summary

After setup is complete, inform the user:
- The output directory location
- The number of components in the snapshot
- How to run validation: `./run.sh`
- How to debug violations: Use the `ec-debug-violations` skill or ask about specific violations

When the output contains `snapshot.json`, `policy.yaml`, and `policy/release/`, `ec-debug-violations` can discover it automatically when run from the same project/task directory. If several candidates exist or you run it elsewhere, provide this output path with `--setup-dir`. Use `--policy` to supply a policy configuration directly.
