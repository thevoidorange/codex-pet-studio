# Security and Privacy Policy

## Supported version

Security fixes are applied to the current default branch. Older snapshots and exported pet projects may not receive updates.

## Report a vulnerability privately

Use GitHub private vulnerability reporting or a private security advisory for this repository when available.

If private reporting is not enabled, open a minimal issue asking a maintainer to establish a private channel. Do not disclose exploit details, personal inspiration, screenshots, credentials, or identifying paths in the public issue.

Include, when safe:

- the affected revision;
- the smallest reproducible description;
- expected and actual behavior;
- potential impact;
- a suggested mitigation, if known.

## Relevant security issues

Examples include:

- unintended upload or disclosure of local inspiration;
- secrets written into generated files, logs, previews, or packages;
- path traversal or unsafe archive extraction;
- arbitrary command execution from project metadata;
- unsafe handling of untrusted images or package files;
- cross-site scripting or local-file access in the Previewer;
- installation that modifies files outside its declared destination;
- dependency or supply-chain compromise.

Visual defects and ordinary package-validation failures may be reported publicly unless they expose private material.

## Privacy boundary

The core workflow is local-first.

- A separate OpenAI API key is not required.
- Personal inspiration must not be uploaded without explicit user permission.
- Private inputs must not be committed to the repository.
- Logs and bug reports should use synthetic or neutral examples.
- Remove EXIF and other identifying metadata before publishing assets.
- Never ask a user to paste a secret into chat, a template, or a tracked file.

## Coordinated disclosure

Please allow maintainers a reasonable opportunity to investigate and prepare a fix before public disclosure. Maintainers will credit reporters who request attribution and whose reports materially improve the project.
