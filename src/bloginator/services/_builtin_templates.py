"""Built-in template definitions."""

from bloginator.models.template import PromptTemplate, TemplateType


def get_builtin_templates() -> list[PromptTemplate]:
    """Get all built-in templates.

    Returns:
        List of built-in PromptTemplate objects
    """
    return [
        # Technical writing template
        PromptTemplate(
            id="builtin-technical",
            name="Technical Writing",
            type=TemplateType.OUTLINE,
            description="Formal technical documentation style",
            template="""Create a technical outline for: {{ title }}

Focus on precision, accuracy, and thorough documentation.
Use formal tone, avoid ambiguity, include technical details.

Keywords: {{ keywords }}
{% if thesis %}Thesis: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} main sections
- Technical accuracy
- Clear structure
- Reference relevant technical concepts
""",
            variables=["title", "keywords", "thesis", "num_sections"],
            is_builtin=True,
            tags=["technical", "documentation", "formal"],
        ),
        # Blog post template
        PromptTemplate(
            id="builtin-blog",
            name="Blog Post",
            type=TemplateType.OUTLINE,
            description="Conversational blog post style",
            template="""Create an engaging blog outline for: {{ title }}

Use conversational tone, relatable examples, personal insights.
Make it accessible and engaging for general readers.

Keywords: {{ keywords }}
{% if thesis %}Key message: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} main sections
- Engaging introduction
- Real-world examples
- Actionable takeaways
""",
            variables=["title", "keywords", "thesis", "num_sections"],
            is_builtin=True,
            tags=["blog", "casual", "engaging"],
        ),
        # Executive summary template
        PromptTemplate(
            id="builtin-executive",
            name="Executive Summary",
            type=TemplateType.OUTLINE,
            description="High-level strategic overview",
            template="""Create an executive summary outline for: {{ title }}

Focus on high-level insights, strategic implications, key decisions.
Target executive audience - concise, actionable, business-focused.

Keywords: {{ keywords }}
{% if thesis %}Strategic thesis: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} key points
- Business impact focus
- Data-driven insights
- Actionable recommendations
""",
            variables=["title", "keywords", "thesis", "num_sections"],
            is_builtin=True,
            tags=["executive", "business", "strategic"],
        ),
        # Tutorial template
        PromptTemplate(
            id="builtin-tutorial",
            name="Tutorial/How-To",
            type=TemplateType.OUTLINE,
            description="Step-by-step instructional guide",
            template="""Create a tutorial outline for: {{ title }}

Provide clear step-by-step instructions with examples.
Focus on practical learning and hands-on guidance.

Keywords: {{ keywords }}
{% if thesis %}Learning goal: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} main sections
- Clear prerequisites
- Step-by-step instructions
- Examples and exercises
- Common pitfalls
""",
            variables=["title", "keywords", "thesis", "num_sections"],
            is_builtin=True,
            tags=["tutorial", "how-to", "instructional"],
        ),
    ]
