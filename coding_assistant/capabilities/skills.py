from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset


def _load_skill(skill_name: str, skills_dir: str = "skills") -> str:
    """Load a skill's router file (SKILL.md), supporting both
    flat-style (skills/name.md) and folder-style (skills/name/SKILL.md) skills.

    skill_name : str
        The name of the skill to load (e.g. "web-scraping-econ").
        Should be a bare name, not a path.

    Returns
    -------
    str
        The contents of the skill's router file.

    """
    # Defensive: strip any accidental "skills/" prefix or ".md" suffix
    # in case the model passes a path instead of a bare name.
    clean_name = skill_name.removeprefix("skills/").removesuffix(".md")

    folder_path = Path(skills_dir) / clean_name / "SKILL.md"
    flat_path = Path(skills_dir) / f"{clean_name}.md"

    if folder_path.exists():
        file_path = folder_path
    elif flat_path.exists():
        file_path = flat_path
    else:
        msg = f"Skill '{skill_name}' not found in flat or folder format."
        raise FileNotFoundError(msg)

    skill = frontmatter.load(str(file_path))
    return skill.content


def load_skill(skill_name: str) -> str:
    """Load a skill's instructions (default skills folder: "skills")."""
    return _load_skill(skill_name)


@dataclass
class Skills(AbstractCapability[Any]):
    # Folder with the skill files. The coding assistant uses "skills";
    # the research agent uses "skills_research".
    skills_dir: str = "skills"

    def get_instructions(self) -> str:
        result = (
            "You can extend your capabilities by using skills.\n"
             "BEFORE writing any code or answering, check whether any skill below "
            "matches the user's request — even if you feel confident you already "
            "know how to do the task. If a skill matches, you MUST call load_skill "
            "with that skill's name FIRST, and follow its instructions.\n\n"
            "You have the following skills available:"
        )

        skills_dir = Path(self.skills_dir)

        # Flat-style skills: skills/name.md
        flat_files = skills_dir.glob("*.md")

        # Folder-style skills: skills/name/SKILL.md
        folder_files = skills_dir.glob("*/SKILL.md")

        for f in list(flat_files) + list(folder_files):
            skill = frontmatter.load(str(f))

            name = skill.metadata.get("name")
            description = skill.metadata.get("description")

            result += f"\n- {name}: {description}"

        return result

    def get_toolset(self) -> FunctionToolset:
        toolset = FunctionToolset()
        directory = self.skills_dir

        def load_skill(skill_name: str) -> str:
            """Load a skill's instructions by its name.

            skill_name : str
                The name of the skill to load, as listed in your instructions
                (a bare name, not a path).

            Returns
            -------
            str
                The skill's instructions. Follow them.
            """
            return _load_skill(skill_name, directory)

        toolset.add_function(load_skill)

        return toolset
