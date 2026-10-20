---
name: skill-authoring
description: Load this skill when the user wants to create, write, or edit a skill file for this agent.
---

A skill is a Markdown file in the `skills/` directory that teaches the agent how to do a
specific kind of task. Help the user write one by following these rules.

## File structure

Every skill has two parts:

```
---
name: my-skill
description: Load this skill when ...
---

* instruction one
* instruction two
```

* The block between `---` lines is the frontmatter (YAML metadata).
* Everything after the second `---` is the body (the actual instructions).

## Hard rules (must follow, or the skill will not load)

* `name` MUST exactly match the file name without `.md`. Example: file `data-cleaning.md` -> `name: data-cleaning`.
* Use kebab-case for `name`: lowercase words joined by hyphens, no spaces.
* `description` should start with "Load this skill when ..." and describe the trigger situation, so the agent knows when to use it.
* The body must be concrete, actionable instructions — prefer a bulleted list.

## Two-level (folder) format

Use this format instead of a flat file when a skill covers several 
distinct sub-scenarios that each need their own detailed instructions 
(e.g. different data sources, different test families).

Structure:
skills/my-skill/
├── SKILL.md              # router: frontmatter + high-level guidance
└── references/
├── topic-one.md
└── topic-two.md

* `SKILL.md` MUST have the same frontmatter block as a flat skill 
  (`name` and `description`), even though the file itself is not named 
  after the skill. `name` still matches the *folder* name, not the 
  file name.
* `SKILL.md` stays short and decision-oriented: when to use this skill, 
  and which reference file to load for which situation.
* Detailed instructions, code examples, and edge cases go in `references/`, 
  not in `SKILL.md`.
* Only split into this format when a single flat file would grow too 
  long or cover clearly distinct sub-topics — most skills should stay flat.
## Good practices

* Write the body for a non-programmer scientist: explain steps in plain language, prefer named variables, add short comments.
* Keep each skill focused on ONE topic. Split unrelated concerns into separate skills.
* Tell the agent both *what* to do and *how to communicate* results to the user.

## Workflow when helping the user

1. Ask what task the skill should cover (if unclear).
2. Propose a `name` (kebab-case) and confirm it will be the file name.
3. Draft the frontmatter, then the body.
4. Use write_file to save the file(s) into the sandbox/ directory, 
   preserving the same folder structure the skill will need:
   - Flat skill: sandbox/<name>.md
   - Two-level skill: sandbox/<name>/SKILL.md and 
     sandbox/<name>/references/<topic>.md for each reference file.
   Tell the user the skill has been created in sandbox/ and that they 
   need to move the whole folder (or file) into skills/ themselves, 
   since write_file cannot write outside sandbox/.
5. Remind the user to restart the agent so the new skill is detected 
   after moving it.
