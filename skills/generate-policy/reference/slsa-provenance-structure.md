# SLSA Provenance Attestation Structure Reference

This document describes the exact structure of SLSA Provenance v1.0 and v0.2 attestations to enable traversal and policy rule development.

## IMPORTANT: Accessing SLSA Provenance Attestations

SLSA provenance attestations are in-toto statements embedded in the attestation list. The Conforma policy framework provides library functions that handle version detection and filtering automatically.

### Use the Library Functions

**Always use the library helpers** from `data.lib` to access provenance attestations rather than iterating `input.attestations` directly:

```rego
import data.lib

# All SLSA provenance attestations (both v1.0 and v0.2)
some att in lib.slsa_provenance_attestations

# PipelineRun attestations only (latest per version, filtered by buildType)
some att in lib.pipelinerun_attestations

# Materials (resolvedDependencies for v1.0, materials for v0.2)
materials := lib.attestation_materials(att)
```

### Why This Matters

- `lib.pipelinerun_attestations` automatically selects the latest attestation per version when multiples exist (by `buildFinishedOn` timestamp)
- `lib.attestation_materials(att)` abstracts the v1.0 vs v0.2 structural difference for materials/dependencies
- `lib.slsa_provenance_attestations` filters by predicate type, not build type — use when you need all provenance regardless of build system
- Direct iteration over `input.attestations` bypasses version detection, timestamp filtering, and build type validation

---

## Required Inputs for SLSA Provenance Rules

When generating SLSA provenance validation rules, prompt the user for required configuration:

### Builder ID Validation

When the user requests a rule to validate the build service (e.g., "verify images were built by Tekton"):

**Required**: `allowed_builder_ids` — List of accepted builder identifiers

**Prompt**: "What builder IDs should be accepted? These identify the build service that produced the attestation."

**Example values**:
- `["https://tekton.dev/chains/v2"]` — Tekton Chains v2
- `["https://tekton.dev/chains/v2", "https://tekton.dev/chains/v3"]` — multiple versions

**Usage in policy config** (`ruleData`):
```yaml
ruleData:
  allowed_builder_ids:
    - "https://tekton.dev/chains/v2"
```

**Usage in Rego rule**:
```rego
allowed_builder_ids := rule_data.get("allowed_builder_ids")
builder_id := _builder_id(att)
not builder_id in allowed_builder_ids
```

### Attestation Type Validation

When the user requests predicate type validation (e.g., "verify attestation format is known"):

**Required**: `known_attestation_types` — List of accepted in-toto statement types

**Example values**:
- `["https://in-toto.io/Statement/v0.1", "https://in-toto.io/Statement/v1"]`

**Usage in policy config** (`ruleData`):
```yaml
ruleData:
  known_attestation_types:
    - "https://in-toto.io/Statement/v0.1"
    - "https://in-toto.io/Statement/v1"
```

### Build Type Validation

When the user requests build type validation (e.g., "verify the build system type"):

**Required**: `allowed_provenance_build_types` — List of accepted build type identifiers

**Example values**:
- `["tekton.dev/v1/PipelineRun", "https://tekton.dev/chains/v2/slsa-tekton"]`

**Usage in policy config** (`ruleData`):
```yaml
ruleData:
  allowed_provenance_build_types:
    - "tekton.dev/v1/PipelineRun"
    - "https://tekton.dev/chains/v2/slsa-tekton"
```

### Source Correlation

When the user requests source code verification (e.g., "verify source repo matches attestation"):

**Required**: `supported_vcs` and `supported_digests` — Version control system types and digest algorithms

**Prompt**: "What version control systems and digest algorithms should be supported for source correlation?"

**Example values**:
- `supported_vcs`: `["git"]`
- `supported_digests`: `["sha1", "gitCommit", "sha256"]`

**Usage in policy config** (`ruleData`):
```yaml
ruleData:
  supported_vcs:
    - "git"
  supported_digests:
    - "sha1"
    - "gitCommit"
    - "sha256"
```

**Usage in Rego rule**:
```rego
some material in lib.attestation_materials(att)
some digest_alg in object.keys(material.digest)
some supported_vcs_type in rule_data.get("supported_vcs")
startswith(material.uri, sprintf("%s+", [supported_vcs_type]))
digest_alg in rule_data.get("supported_digests")
```

### Pipeline Run Parameters

When the user requests parameter validation (e.g., "verify pipeline was initialized with expected params"):

**Required**: `pipeline_run_params` — List of expected PipelineRun parameter names

**Prompt**: "What PipelineRun parameters should be required? (e.g., git-repo, git-revision, output-image)"

**Example values**:
- `["git-repo", "git-revision", "output-image"]`

**Usage in policy config** (`ruleData`):
```yaml
ruleData:
  pipeline_run_params:
    - "git-repo"
    - "git-revision"
    - "output-image"
```

### Other SLSA Rule Inputs

| Rule Type | Required Input | Description |
|-----------|---------------|-------------|
| Builder ID validation | `allowed_builder_ids` | List of accepted builder identifiers |
| Attestation type validation | `known_attestation_types` | List of accepted in-toto statement types |
| Build type validation | `allowed_provenance_build_types` | List of accepted build type strings |
| Source correlation | `supported_vcs` | List of supported VCS types (e.g., `["git"]`) |
| Source correlation | `supported_digests` | List of supported digest algorithms |
| Pipeline run params | `pipeline_run_params` | List of expected PipelineRun parameter names |

---

## SLSA Provenance v1.0

### Identification
- **Predicate type**: `https://slsa.dev/provenance/v1`
- **Detection**: `att.statement.predicateType == "https://slsa.dev/provenance/v1"`

### Key Structural Areas

#### Build Definition
Contains the build system type, input parameters, and resolved dependencies:
```
att.statement.predicate.buildDefinition
```

- **Build type** — identifies the build system:
  ```
  att.statement.predicate.buildDefinition.buildType
  ```
  Example values: `"https://tekton.dev/chains/v2/slsa-tekton"`, `"tekton.dev/v1/PipelineRun"`

- **External parameters** — pipeline run params, source repo, output image:
  ```
  att.statement.predicate.buildDefinition.externalParameters
  ```
  PipelineRun params are at:
  ```
  att.statement.predicate.buildDefinition.externalParameters.runSpec.params
  ```
  Workspaces are at:
  ```
  att.statement.predicate.buildDefinition.externalParameters.runSpec.workspaces
  ```

- **Resolved dependencies** — tasks, source materials with digests:
  ```
  att.statement.predicate.buildDefinition.resolvedDependencies
  ```
  Each dependency has `uri`, `digest`, and optionally `name` and `content`.

#### Run Details
Contains builder identity and build metadata:
```
att.statement.predicate.runDetails
```

- **Builder ID** — identifies the builder:
  ```
  att.statement.predicate.runDetails.builder.id
  ```
  Example value: `"https://tekton.dev/chains/v2"`

- **Metadata** — build invocation metadata:
  ```
  att.statement.predicate.runDetails.metadata
  ```
  Timestamps at:
  ```
  att.statement.predicate.runDetails.metadata.buildFinishedOn
  att.statement.predicate.runDetails.metadata.finishedOn
  ```

### SLSA v1.0 Example JSON

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "predicateType": "https://slsa.dev/provenance/v1",
  "subject": [
    {
      "name": "quay.io/example/image",
      "digest": {
        "sha256": "abc123def456..."
      }
    }
  ],
  "predicate": {
    "buildDefinition": {
      "buildType": "https://tekton.dev/chains/v2/slsa-tekton",
      "externalParameters": {
        "runSpec": {
          "pipelineRef": {
            "name": "docker-build",
            "bundle": "quay.io/konflux-ci/tekton-catalog/pipeline-docker-build:devel"
          },
          "params": [
            {
              "name": "git-repo",
              "value": "https://github.com/example/repo"
            },
            {
              "name": "git-revision",
              "value": "abc123"
            },
            {
              "name": "output-image",
              "value": "quay.io/example/image:tag"
            }
          ],
          "workspaces": [
            {
              "name": "workspace",
              "volumeClaimTemplate": {
                "spec": {
                  "accessModes": ["ReadWriteOnce"],
                  "resources": {
                    "requests": {
                      "storage": "1Gi"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "resolvedDependencies": [
        {
          "name": "pipelineTask",
          "uri": "oci://quay.io/konflux-ci/tekton-catalog/task-git-clone:0.1",
          "digest": {
            "sha256": "task-digest-here..."
          },
          "content": "base64-encoded-task-spec..."
        },
        {
          "uri": "git+https://github.com/example/repo.git",
          "digest": {
            "sha1": "abc123def456789..."
          }
        }
      ]
    },
    "runDetails": {
      "builder": {
        "id": "https://tekton.dev/chains/v2"
      },
      "metadata": {
        "invocationID": "pipelinerun-uid-here",
        "buildStartedOn": "2024-01-15T10:00:00Z",
        "buildFinishedOn": "2024-01-15T10:15:00Z"
      }
    }
  }
}
```

### Key Rego Paths for SLSA v1.0

```rego
# Get build type
build_type := att.statement.predicate.buildDefinition.buildType

# Get builder ID
builder_id := att.statement.predicate.runDetails.builder.id

# Get resolved dependencies (source materials, task refs)
resolved_deps := att.statement.predicate.buildDefinition.resolvedDependencies

# Get external parameters (pipeline run params)
params := att.statement.predicate.buildDefinition.externalParameters.runSpec.params

# Get individual param by name
param_names := {p.name |
  some p in att.statement.predicate.buildDefinition.externalParameters.runSpec.params
  p.value != ""
}

# Get workspaces
workspaces := att.statement.predicate.buildDefinition.externalParameters.runSpec.workspaces

# Get source material from resolved dependencies
some material in att.statement.predicate.buildDefinition.resolvedDependencies
startswith(material.uri, "git+")
some digest_alg in object.keys(material.digest)
source_ref := sprintf("%s@%s:%s", [material.uri, digest_alg, material.digest[digest_alg]])

# Get build timestamps
finished := att.statement.predicate.runDetails.metadata.buildFinishedOn
```

---

## SLSA Provenance v0.2

### Identification
- **Predicate type**: `https://slsa.dev/provenance/v0.2`
- **Detection**: `att.statement.predicateType == "https://slsa.dev/provenance/v0.2"` for general provenance filtering; additionally filtered by `att.statement.predicate.buildType in allowed_build_types` for PipelineRun-specific attestations

### Key Structural Areas

#### Builder
Contains the builder identity:
```
att.statement.predicate.builder
```

- **Builder ID**:
  ```
  att.statement.predicate.builder.id
  ```
  Example value: `"https://tekton.dev/chains/v2"`

#### Build Type
Identifies the build system (top-level in predicate):
```
att.statement.predicate.buildType
```
Example values: `"tekton.dev/v1/PipelineRun"`, `"tekton.dev/v1beta1/TaskRun"`

#### Materials
Source materials with digests:
```
att.statement.predicate.materials
```
Each material has `uri` and `digest` fields, matching the same schema as v1.0 `resolvedDependencies`.

#### Build Config
Task definitions for the build:
```
att.statement.predicate.buildConfig.tasks
```

#### Metadata
Build invocation metadata:
```
att.statement.predicate.metadata
```
Timestamp at:
```
att.statement.predicate.metadata.buildFinishedOn
```

### SLSA v0.2 Example JSON

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "subject": [
    {
      "name": "quay.io/example/image",
      "digest": {
        "sha256": "abc123def456..."
      }
    }
  ],
  "predicate": {
    "builder": {
      "id": "https://tekton.dev/chains/v2"
    },
    "buildType": "tekton.dev/v1/PipelineRun",
    "invocation": {
      "configSource": {},
      "parameters": {}
    },
    "buildConfig": {
      "tasks": [
        {
          "name": "git-clone",
          "ref": {
            "name": "git-clone",
            "bundle": "quay.io/konflux-ci/tekton-catalog/task-git-clone:0.1",
            "kind": "Task"
          },
          "startedOn": "2024-01-15T10:00:00Z",
          "finishedOn": "2024-01-15T10:01:00Z",
          "status": "Succeeded",
          "results": [
            {
              "name": "commit",
              "type": "string",
              "value": "abc123def456789..."
            },
            {
              "name": "url",
              "type": "string",
              "value": "https://github.com/example/repo"
            }
          ]
        }
      ]
    },
    "materials": [
      {
        "uri": "git+https://github.com/example/repo.git",
        "digest": {
          "sha1": "abc123def456789..."
        }
      },
      {
        "uri": "oci://quay.io/konflux-ci/tekton-catalog/task-git-clone:0.1",
        "digest": {
          "sha256": "task-digest-here..."
        }
      }
    ],
    "metadata": {
      "buildStartedOn": "2024-01-15T10:00:00Z",
      "buildFinishedOn": "2024-01-15T10:15:00Z",
      "completeness": {
        "parameters": true,
        "environment": false,
        "materials": true
      },
      "reproducible": false
    }
  }
}
```

### Key Rego Paths for SLSA v0.2

```rego
# Get build type
build_type := att.statement.predicate.buildType

# Get builder ID
builder_id := att.statement.predicate.builder.id

# Get materials (source refs, task refs)
materials := att.statement.predicate.materials

# Get tasks from build config
tasks := att.statement.predicate.buildConfig.tasks

# Get source material from materials
some material in att.statement.predicate.materials
startswith(material.uri, "git+")
some digest_alg in object.keys(material.digest)
source_ref := sprintf("%s@%s:%s", [material.uri, digest_alg, material.digest[digest_alg]])

# Get build timestamps
finished := att.statement.predicate.metadata.buildFinishedOn
```

---

## Summary: Path Comparison

| Data Element | SLSA v1.0 Path | SLSA v0.2 Path |
|-------------|----------------|----------------|
| Predicate type | `https://slsa.dev/provenance/v1` | `https://slsa.dev/provenance/v0.2` |
| Builder ID | `predicate.runDetails.builder.id` | `predicate.builder.id` |
| Build type | `predicate.buildDefinition.buildType` | `predicate.buildType` |
| Source materials | `predicate.buildDefinition.resolvedDependencies` | `predicate.materials` |
| Tasks | `predicate.buildDefinition.resolvedDependencies` (content field) | `predicate.buildConfig.tasks` |
| External params | `predicate.buildDefinition.externalParameters.runSpec.params` | `predicate.invocation.parameters` |
| Workspaces | `predicate.buildDefinition.externalParameters.runSpec.workspaces` | N/A |
| Build finished | `predicate.runDetails.metadata.buildFinishedOn` | `predicate.metadata.buildFinishedOn` |

## Common Rego Patterns

### Access Builder ID (Both Versions)

```rego
# Dual-version builder ID access (from slsa_build_build_service.rego)
_builder_id(att) := builder_id if {
  # slsa v0.2
  builder_id := att.statement.predicate.builder.id
} else := builder_id if {
  # slsa v1.0
  builder_id := att.statement.predicate.runDetails.builder.id
}
```

### Access Materials / Resolved Dependencies (Both Versions)

```rego
# Use lib.attestation_materials for version-agnostic access
some att in lib.pipelinerun_attestations
materials := lib.attestation_materials(att)

# Or manually (from lib/attestations.rego):
attestation_materials(att) := att.statement.predicate.buildDefinition.resolvedDependencies if {
  att.statement.predicateType == "https://slsa.dev/provenance/v1"
} else := att.statement.predicate.materials if {
  att.statement.predicateType == "https://slsa.dev/provenance/v0.2"
}
```

### Validate Builder ID Against Allowed List

```rego
import data.lib
import data.lib.rule_data

deny contains result if {
  allowed_builder_ids := rule_data.get("allowed_builder_ids")
  some att in lib.pipelinerun_attestations
  builder_id := _builder_id(att)
  not builder_id in allowed_builder_ids
  result := metadata.result_helper(rego.metadata.chain(), [builder_id])
}
```

### Correlate Source Code Reference

```rego
import data.lib
import data.lib.rule_data

# Extract source references from materials (both versions)
_source_references contains ref if {
  some att in lib.slsa_provenance_attestations
  some material in lib.attestation_materials(att)
  some digest_alg in object.keys(material.digest)
  some supported_vcs_type in rule_data.get("supported_vcs")

  startswith(material.uri, sprintf("%s+", [supported_vcs_type]))
  digest_alg in rule_data.get("supported_digests")

  ref := sprintf("%s@%s:%s", [material.uri, digest_alg, material.digest[digest_alg]])
}
```

### Validate Pipeline Run Parameters (v1.0 Only)

```rego
import data.lib
import data.lib.rule_data

deny contains result if {
  some provenance in lib.pipelinerun_attestations

  param_names := {p.name |
    some p in provenance.statement.predicate.buildDefinition.externalParameters.runSpec.params
    p.value != ""
  }
  expected_names := {n | some n in rule_data.get("pipeline_run_params")}

  expected_names != param_names
  result := metadata.result_helper(rego.metadata.chain(), [param_names, expected_names])
}
```

### Check for Shared Volumes (v1.0 Only)

```rego
deny contains result if {
  some provenance in lib.pipelinerun_attestations
  shared_workspaces := {w |
    some w in provenance.statement.predicate.buildDefinition.externalParameters.runSpec.workspaces
    w.persistentVolumeClaim
  }
  count(shared_workspaces) > 0
  result := metadata.result_helper(rego.metadata.chain(), [shared_workspaces])
}
```
