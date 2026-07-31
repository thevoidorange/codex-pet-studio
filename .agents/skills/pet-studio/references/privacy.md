# Privacy and publication policy

## Default boundary

Treat all user-provided references, exploratory prompts, intermediate boards, review screenshots, local paths, and personal stories as private unless the user explicitly approves publication.

Public source files should contain only:

- generic workflow instructions
- parameterized tools and schemas
- blank templates
- a project-owned or explicitly authorized public example
- intentionally public pack artifacts

## Local project zones

Recommended zones:

| Zone | Purpose | Commit? |
| --- | --- | --- |
| `inputs/` | source images and private inspiration | no |
| `design/` | private decisions, prompts, boards, and motion notes | no |
| `build/` | generated rows, atlases, previews, and debug files | no |
| `pet-studio.json` | generic public project configuration | yes |
| `dist/` | deterministic allowlisted export bundles | no by default; publish intentionally |

Never write absolute source paths into publishable documents. Use neutral input IDs and relative local references.

## Blocked leak patterns

Scan tracked and exported files for:

- home-directory paths such as `/Users/`, `/home/`, and `C:\Users\`
- application container and temporary paths
- clipboard filenames and local file URLs
- usernames and project-specific private terms
- API keys, tokens, private keys, credentials, and signed URLs
- image metadata containing GPS, author, prompt, description, source path, or comments

The deterministic privacy check is a baseline. Manually inspect image content and Git history before publication.

## Images

Do not assume stripped filenames make an image anonymous. Images may reveal:

- people, pets, rooms, screens, documents, or locations
- embedded author or GPS metadata
- prompt or generation parameters
- source-specific visual identity

Prefer new project-owned fixtures for public examples. A user-originated
character may be included only after the user gives explicit, scoped
publication approval for the exact final artifact. Publish only the sanitized
package, a compact public description, and a reviewed rights record. Exclude
raw references, private names, prompts, design history, conversations, local
paths, and identifying metadata.

## Export allowlist

A public pet export may include:

- `pet.json`
- `spritesheet.webp` or `spritesheet.png`
- intentionally public preview images or GIFs
- a compact public description and license notice
- validation summary without local paths

Do not export raw references, prompts, design history, debug atlases, temporary generations, or review conversations by default.

## Git history

Deleting a file in a later commit does not remove it from Git history. Run privacy checks before the first commit and before every public release. If a secret or private image enters history, stop publication and follow GitHub's sensitive-data removal guidance.
