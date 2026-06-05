"""Jinja2 prompt templates for LinguaResume LLM calls."""
from jinja2 import Template

_MIDDLE_TEMPLATE = Template(r"""
<<system_context>
You are an expert resume writer. You rewrite resume middle sections to match job descriptions while maintaining strict factual fidelity to the source material.
</system_context>

<<output_rules>
1. Return ONLY the resume middle sections inside <resume_middle> XML tags.
2. Language: ALL content must be in {{ lang_name }} except proper nouns.
3. Section headings must be exactly: ## {{ profile_heading }}, ## {{ tech_heading }}, ## {{ experience_heading }}.
4. Preserve the EXACT number of bullet points per employer as the master.
5. Do not add technologies not present in the master CV.
6. PRESERVE every technology category from the master CV in the Technical Skills table. You MUST reword, reorder, or merge adjacent categories, but you are FORBIDDEN from deleting any category heading or removing its row from the table. If a category has weak relevance, move it lower in the table and keep the description factual and concise.
7. Do not include Education or Languages sections.
8. For French output, use past participles without auxiliary.
9. No meta-commentary, code fences, or extra XML tags.
</output_rules>

<<job_description>
{{ job_desc }}
</job_description>

<<requirements>
must_haves: {{ must_haves | tojson }}
nice_to_haves: {{ nice_to_haves | tojson }}
soft_skills: {{ soft_skills | tojson }}
job_focus: {{ job_focus }}
</requirements>

{% if retry_block %}
<<retry_feedback>
{{ retry_block }}
</retry_feedback>
{% endif %}

<source_material>
{{ master_mutable }}
</source_material>

<<example_output_format>
## {{ profile_heading }}

[2-3 sentences]

## {{ tech_heading }}

| Category | Technologies |
|----------|-------------|
| ... | ... |

## {{ experience_heading }}

### Company Name, Job Title (MM/YYYY – MM/YYYY)
- [Bullet in {{ lang_name }}]
</example_output_format>

Now generate the tailored resume middle sections.
""")

_TRANSLATE_TEMPLATE = Template(r"""
You are a precise translator.

Translate the following resume sections into {{ target_lang_name }}.

RULES:
- Keep ALL proper nouns exactly as written.
- Translate degree names and table column headers.
- Do NOT change structure or add/remove information.

STATIC SECTIONS TO TRANSLATE:
{{ static_bundle }}

Return ONLY the translated sections, with the same Markdown formatting.
""")

_REQUIREMENTS_TEMPLATE = Template(r"""
Analyze this job description and extract the core requirements in JSON format.

JOB DESCRIPTION:
{{ job_desc }}

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{
  "job_title": "...",
  "company": "...",
  "domain": "devops|webdev|fullstack|other",
  "must_haves": ["..."],
  "nice_to_haves": ["..."],
  "soft_skills": ["..."],
  "job_focus": "one sentence summary",
  "language_tone": "formal|casual|technical"
}
""")

_TITLE_TRANSLATE_TEMPLATE = Template(r"""
Translate this job title into {{ target_lang }}: {{ job_title }}
Return only the translation.
""")


def render_middle_prompt(
    *,
    lang_name: str,
    profile_heading: str,
    tech_heading: str,
    experience_heading: str,
    job_desc: str,
    must_haves: list,
    nice_to_haves: list,
    soft_skills: list,
    job_focus: str,
    retry_block: str,
    master_mutable: str,
) -> str:
    return _MIDDLE_TEMPLATE.render(
        lang_name=lang_name,
        profile_heading=profile_heading,
        tech_heading=tech_heading,
        experience_heading=experience_heading,
        job_desc=job_desc,
        must_haves=must_haves,
        nice_to_haves=nice_to_haves,
        soft_skills=soft_skills,
        job_focus=job_focus,
        retry_block=retry_block,
        master_mutable=master_mutable,
    )


def render_translate_prompt(*, target_lang: str, static_bundle: str) -> str:
    lang_names = {"en": "English", "fr": "French", "de": "German"}
    return _TRANSLATE_TEMPLATE.render(
        target_lang=target_lang.upper(),
        target_lang_name=lang_names.get(target_lang, target_lang.upper()),
        static_bundle=static_bundle,
    )


def render_requirements_prompt(*, job_desc: str) -> str:
    return _REQUIREMENTS_TEMPLATE.render(job_desc=job_desc)


def render_title_translate_prompt(*, target_lang: str, job_title: str) -> str:
    return _TITLE_TRANSLATE_TEMPLATE.render(
        target_lang=target_lang,
        job_title=job_title,
    )