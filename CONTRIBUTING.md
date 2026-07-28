# Contributing to Codex Pet Studio

Thank you for helping make pet creation more thoughtful, expressive, and reliable.

## What belongs here

Useful contributions include:

- improvements to the phase-gated creative workflow;
- clearer templates and documentation;
- Previewer accessibility, localization, or comparison improvements;
- stronger visual, motion, and pack QA;
- compatibility work for current Codex pet formats;
- neutral, fully licensed examples;
- fixes that make the repository easier for Codex and people to use together.

This project is not a bulk character dump or a gallery of unlicensed fan assets.

## Before opening a pull request

1. Open an issue or discussion for a material workflow change.
2. Explain the user problem before proposing an implementation.
3. Keep the core experience local-first and usable without a separate API key.
4. Preserve phase gates and version comparison.
5. Test the change with a neutral project.
6. Remove personal data, machine-specific paths, and generated secrets.

Run the dependency-free checks before opening a pull request:

```bash
python3 -m unittest discover -s tests -v
python3 .agents/skills/pet-studio/scripts/studio.py doctor
python3 .agents/skills/pet-studio/scripts/studio.py privacy-check
```

## Public language

Repository documentation, filenames, state identifiers, version identifiers, tests, and code comments should be in English.

Codex may collaborate with users in any language. The Previewer may display bilingual user-facing labels, including English and Chinese, while retaining stable English IDs underneath.

## Asset and reference rights

Only contribute material that you created, that is in the public domain, or that you have permission to redistribute under terms compatible with this repository.

For every public visual example:

- identify its creator and source;
- state the license or permission basis;
- include required attribution;
- disclose whether generative tools were used;
- remove identifying metadata;
- avoid third-party characters, logos, and trademarks unless their use is clearly permitted.

Use [`templates/asset-attribution.md`](templates/asset-attribution.md). The MIT License for this repository does not grant rights to external source material.

## Privacy

Do not submit:

- personal pet or family photos without explicit publication consent;
- names, faces, homes, private conversations, or location metadata;
- user prompts or transcripts copied from private sessions;
- API keys, tokens, credentials, or private URLs;
- absolute paths containing a local username.

If a bug report requires private material, follow [SECURITY.md](SECURITY.md) rather than attaching it to a public issue.

## Pull request checklist

- [ ] The change has a clear user-facing reason.
- [ ] Public text and identifiers are in English.
- [ ] The core workflow still works without a hosted service or separate API key.
- [ ] Existing approved-version behavior is preserved.
- [ ] Previewer changes retain version comparison and stable state IDs.
- [ ] Relevant creative, motion, and technical QA was performed.
- [ ] No personal data, secrets, or machine-specific paths are included.
- [ ] New assets have a complete attribution and license record.
- [ ] Documentation reflects the actual behavior.

## Commit and review style

Keep commits focused and describe the behavioral outcome. Reviewers may request a small before/after project, a version comparison, or proof that a packaged pet still validates.

Be direct and kind. Critique the design or implementation, not the person.

## Community standards

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security and privacy issues must be reported through [SECURITY.md](SECURITY.md).
