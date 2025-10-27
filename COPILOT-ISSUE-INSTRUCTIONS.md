# Copilot Instructions for Issue Handling

This document provides comprehensive guidelines for using GitHub Copilot to create, manage, and improve issues in the Planted repository. Following these instructions will result in higher quality issues, faster triaging, and better project management.

## Table of Contents

1. [Overview](#overview)
2. [Creating High-Quality Issues](#creating-high-quality-issues)
3. [Managing Issue Relationships](#managing-issue-relationships)
4. [Using Templates and Metadata](#using-templates-and-metadata)
5. [Issue Triage and Prioritization](#issue-triage-and-prioritization)
6. [Best Practices](#best-practices)

## Overview

GitHub Copilot can significantly accelerate issue creation and management. Use it to:
- Draft comprehensive issue descriptions with proper structure
- Identify and document technical details
- Establish relationships between related issues
- Generate actionable acceptance criteria
- Maintain consistency across issue documentation

## Creating High-Quality Issues

### Issue Title Guidelines

**Ask Copilot to:**
- Generate clear, action-oriented titles that start with verbs (Add, Fix, Update, Improve, Refactor)
- Keep titles concise (50-70 characters when possible)
- Include specific component or feature names

**Example Prompt:**
```
Generate 3 alternative issue titles for: [describe the problem or feature]
```

**Good Titles:**
- ✅ "Add plant companion compatibility checking to garden layout"
- ✅ "Fix watering schedule calculation for container gardens"
- ✅ "Improve mobile responsiveness of care schedule view"

**Poor Titles:**
- ❌ "Bug in the app"
- ❌ "Feature request"
- ❌ "Something is broken with plants"

### Issue Description Structure

Use Copilot to generate well-structured issue descriptions with these sections:

#### 1. Overview
A brief 2-3 sentence summary explaining what needs to be done and why.

**Copilot Prompt:**
```
Write a concise overview for an issue about: [your topic]
Include the current state and desired state.
```

#### 2. Background/Context (when relevant)
Explain the context, current behavior, or why this issue exists.

**Copilot Prompt:**
```
Explain the background context for: [your topic]
Include relevant technical details about the Planted codebase.
```

#### 3. Requirements
Clear, numbered list of what needs to be implemented or fixed.

**Copilot Prompt:**
```
List specific requirements for: [your topic]
Format as a numbered list with concrete, testable items.
```

#### 4. Acceptance Criteria
Testable conditions that must be met for the issue to be considered complete.

**Copilot Prompt:**
```
Generate acceptance criteria for: [your topic]
Use "Given-When-Then" format or checkbox lists.
Format as testable conditions.
```

**Example:**
- [ ] User can select multiple plants when creating a garden plot
- [ ] Selected plants display companion compatibility warnings
- [ ] Save button is disabled when incompatible plants are selected
- [ ] UI updates in real-time as plants are added/removed

#### 5. Technical Notes (for implementation details)
Specify affected files, technical constraints, or implementation guidance.

**Copilot Prompt:**
```
Identify relevant files and technical considerations for: [your topic]
Reference the Planted project structure:
- garden_manager/database/ - Database and models
- garden_manager/services/ - External integrations
- garden_manager/utils/ - Utility functions
- garden_manager/web/ - Flask web application
```

#### 6. Out of Scope (when needed)
Clearly state what is NOT included in this issue.

### Complete Issue Template Example

```markdown
## Overview
Add companion planting recommendations to the garden layout interface to help users make 
informed decisions about plant placement and improve garden health.

## Background
The plant database includes companion planting information, but it's only visible in 
individual plant detail views. Users planning their garden layout need this information 
integrated into the planning interface.

## Requirements
1. Display companion compatibility when user hovers over or selects a plant
2. Show visual indicators (colors/icons) for beneficial, neutral, and antagonistic companions
3. Filter plant recommendations based on existing garden selections
4. Provide explanatory tooltips for companion relationships

## Acceptance Criteria
- [ ] Companion indicators appear when plant is selected in layout grid
- [ ] Color coding: green for beneficial, yellow for neutral, red for incompatible
- [ ] Hovering over compatibility icon shows detailed explanation
- [ ] Plant browser filters update based on current garden selections
- [ ] Feature works on mobile and desktop layouts
- [ ] No performance degradation with 20+ plants in layout

## Technical Notes
**Affected Files:**
- `garden_manager/web/templates/garden_layout.html` - UI components
- `garden_manager/database/plant_data.py` - Companion data access
- `garden_manager/web/app.py` - Route logic for compatibility checks
- `garden_manager/web/static/css/style.css` - Visual styling

**Implementation Considerations:**
- Use existing companion_plants field from plant database
- Add AJAX endpoint for real-time compatibility checking
- Leverage Bootstrap color classes for consistency

## Out of Scope
- Advanced permaculture guild planning (future enhancement)
- Historical companion data from previous seasons
- Automatic garden layout optimization
```

## Managing Issue Relationships

### Parent/Child Issue Hierarchy

When breaking down large features, use Copilot to help create clear parent-child relationships:

**Copilot Prompt:**
```
Break down this feature into parent and child issues: [describe feature]
Create 1 parent issue and 3-5 child issues.
Each child should be completable in 1-2 days.
```

#### Parent Issue Guidelines
- Use "Epic" or "Feature" label
- Provide high-level overview and goals
- List all child issues with links
- Track overall progress with checklist

**Parent Issue Template:**
```markdown
## Epic Overview
[High-level description of the feature]

## Goals
- [Goal 1]
- [Goal 2]

## Child Issues
- [ ] #XXX - [Child issue 1 title]
- [ ] #XXX - [Child issue 2 title]
- [ ] #XXX - [Child issue 3 title]

## Success Metrics
[How will we measure success?]
```

#### Child Issue Guidelines
- Reference parent issue in description: "Parent: #XXX"
- Focus on single, specific deliverable
- Can be completed independently when possible
- Include acceptance criteria specific to this piece

### Blocking Dependencies

When issues have dependencies, document them clearly:

**Use GitHub's Task Lists:**
```markdown
## Dependencies
This issue is blocked by:
- [ ] #123 - Must be completed first
- [ ] #124 - Database migration required

This issue blocks:
- #125 - Depends on this feature
- #126 - Needs this API endpoint
```

**Copilot Prompt:**
```
Analyze dependencies for: [your issue]
Identify which existing issues must be completed first.
Consider database changes, API modifications, and UI updates.
```

## Using Templates and Metadata

### Labels

Use labels consistently for organization and filtering:

**Standard Labels for Planted:**
- `bug` - Something isn't working correctly
- `enhancement` - New feature or improvement
- `documentation` - Documentation updates
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority: high/medium/low` - Urgency indicator
- `component: database/ui/api/services` - Area of codebase
- `Epic` - Parent issue for large features

**Copilot Prompt:**
```
Suggest appropriate labels for this issue: [paste issue description]
Choose from: bug, enhancement, documentation, good first issue, help wanted,
priority labels, and component labels.
```

### Milestones

Group related issues into milestones for release planning:

**Copilot Prompt:**
```
Suggest which milestone this issue belongs to: [paste issue]
Consider existing milestones: v1.1, v1.2, or create new milestone name.
```

### Assignees and Reviewers

**Copilot Prompt:**
```
Based on this issue, suggest what skills are needed: [paste issue]
List relevant expertise areas (Python, Flask, Database, Frontend, etc.)
```

## Issue Triage and Prioritization

### Quick Triage with Copilot

**Copilot Prompt:**
```
Triage this issue and suggest:
1. Priority (high/medium/low) with justification
2. Estimated complexity (small/medium/large)
3. Required skills
4. Suggested labels
5. Whether it needs more information

Issue: [paste issue content]
```

### Priority Guidelines

**High Priority:**
- Security vulnerabilities
- Data loss bugs
- Application crashes
- Blocking other work

**Medium Priority:**
- Feature enhancements
- Non-critical bugs
- Performance improvements
- UI improvements

**Low Priority:**
- Nice-to-have features
- Minor UI polish
- Documentation updates
- Refactoring

### Complexity Estimation

**Small (1-2 hours):**
- Bug fixes in single file
- Minor UI adjustments
- Documentation updates

**Medium (2-8 hours):**
- New features in existing modules
- Multi-file refactoring
- Database schema changes

**Large (1-3 days):**
- New major features
- Architecture changes
- Complex integrations

**Copilot Prompt:**
```
Estimate complexity for: [paste issue]
Consider the Planted codebase structure and provide:
- Time estimate
- Number of files affected
- Required testing scope
- Risk level
```

## Best Practices

### 1. Be Specific and Actionable

**Good:**
> Update the plant database to include frost tolerance information for all vegetables. Add a new field `frost_tolerance` with values: 'sensitive', 'tolerant', 'hardy'. Update the database schema, migration script, and UI display.

**Poor:**
> Make the plant database better

### 2. Include Context

Always provide enough context for someone new to understand the issue:
- Link to related issues or PRs
- Reference specific files or code sections
- Include relevant screenshots or error messages
- Explain terminology specific to gardening or the domain

**Copilot Prompt:**
```
Add helpful context to this issue: [paste issue]
Include:
- Links to related code or documentation
- Technical background
- Domain knowledge explanation
```

### 3. Make Issues Discoverable

Use keywords that others might search for:

**Copilot Prompt:**
```
Suggest relevant keywords for this issue: [paste issue]
Consider: feature names, error messages, component names, gardening terms
```

### 4. Keep Issues Focused

One issue = one problem or feature. If an issue grows too large:

**Copilot Prompt:**
```
This issue is too large. Split it into smaller issues: [paste issue]
Create 3-5 focused issues that can be completed independently.
```

### 5. Update Issues as Work Progresses

When working on an issue, keep it updated:
- Add comments for important findings
- Update acceptance criteria if requirements change
- Link to PRs that address the issue
- Close with summary of what was done

**Copilot Prompt:**
```
Generate a closing comment for this issue: [describe what was implemented]
Summarize changes, link to PRs, and mention any follow-up items.
```

### 6. Use Consistent Formatting

**Copilot can help with:**
- Code blocks with syntax highlighting
- Tables for structured data
- Checklists for progress tracking
- Proper markdown formatting

**Copilot Prompt:**
```
Format this issue content properly: [paste unformatted text]
Use markdown: headers, lists, code blocks, tables as appropriate.
```

### 7. Cross-Reference Related Work

Link to:
- Related issues (`#123`)
- Pull requests (`#456`)
- Commits (`abc123`)
- Documentation files
- External resources

**Copilot Prompt:**
```
Find related issues for: [your topic]
Search existing issues in zamays/Planted repository and suggest connections.
```

## Workflow Integration

### Creating an Issue with Copilot

1. **Start with the goal**: Describe what you want to achieve
2. **Ask Copilot to draft**: "Create a GitHub issue for [your goal]"
3. **Refine sections**: Use section-specific prompts to improve each part
4. **Add metadata**: Ask for label and priority suggestions
5. **Review and post**: Check for clarity, completeness, and actionability

### Updating Existing Issues

**Copilot Prompt:**
```
Review and improve this issue: [paste existing issue]
Suggest improvements for:
- Clarity of requirements
- Completeness of acceptance criteria
- Technical detail
- Actionability
```

### Converting Conversations to Issues

After discussing a problem in PR comments or discussions:

**Copilot Prompt:**
```
Convert this discussion into a properly formatted issue: [paste discussion]
Extract: problem statement, requirements, context, and next steps.
```

## Examples for Planted-Specific Scenarios

### Bug Report Example

**Copilot Prompt:**
```
Create a bug report issue for Planted:
Problem: Watering schedule not updating after weather changes
Include: steps to reproduce, expected vs actual behavior, system info
```

### Feature Request Example

**Copilot Prompt:**
```
Create a feature request issue for Planted:
Feature: Add crop rotation planning across growing seasons
Include: user benefit, requirements, acceptance criteria, technical notes
```

### Documentation Issue Example

**Copilot Prompt:**
```
Create a documentation issue for Planted:
Goal: Add tutorial for setting up first garden plot
Include: target audience, content outline, success criteria
```

### Refactoring Issue Example

**Copilot Prompt:**
```
Create a refactoring issue for Planted:
Goal: Extract weather service logic into separate service class
Include: current problems, proposed structure, benefits, affected files
```

## Tips for Maximum Efficiency

1. **Use Copilot Chat**: More interactive and can ask follow-up questions
2. **Iterate**: Refine Copilot's output rather than accepting first draft
3. **Combine with Research**: Use Copilot to draft, then add project-specific details
4. **Save Prompts**: Keep a library of effective prompts for reuse
5. **Review Before Posting**: Copilot helps draft, but you ensure accuracy
6. **Learn from Examples**: Study well-written issues in the repository
7. **Ask for Alternatives**: Request multiple versions and choose the best

## Quality Checklist

Before posting an issue, verify:

- [ ] Title is clear, specific, and action-oriented
- [ ] Overview explains the what and why
- [ ] Requirements are specific and numbered
- [ ] Acceptance criteria are testable
- [ ] Technical notes reference actual files/components
- [ ] Related issues are linked
- [ ] Appropriate labels are applied
- [ ] Priority and complexity are indicated
- [ ] Issue can be understood by new contributors
- [ ] No sensitive information is included
- [ ] Grammar and formatting are clean

## Getting Help

If you're unsure about:
- **Issue structure**: Use the templates in this document
- **Technical details**: Ask in #development channel or tag maintainers
- **Priority**: Err on the side of medium, maintainers will adjust
- **Labels**: Start with basic labels, maintainers will add more specific ones

## Conclusion

Using GitHub Copilot effectively for issue management accelerates the entire development workflow. Well-crafted issues lead to:
- Faster implementation (clear requirements)
- Higher quality code (specific acceptance criteria)
- Better collaboration (clear communication)
- Improved project tracking (proper organization)

Invest time in creating quality issues—it pays dividends throughout the development lifecycle.

---

**Questions or suggestions?** Open an issue using these very guidelines! 🌱
