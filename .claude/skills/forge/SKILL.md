---
name: forge
description: Run the FORGE workflow (Feed context, Outcome not task, Reverse interview, Generate then grade, Export the win) to turn a vague request into a finished, high-quality deliverable such as an email, script, post, proposal or plan. Use when the user says "forge", "/forge", "run FORGE on this", or asks for written or creative work and has not yet given a clear audience, goal or definition of done.
---

# FORGE

FORGE replaces one-shot prompting with a repeatable process. A capable model raises the ceiling. A clear brief is what lets the work reach it. Run these five steps in order. Don't skip ahead to drafting.

## F — Feed it context

Before anything else, collect what you already know:
- Check the project files, memory, CLAUDE.md, and any earlier messages for who the user is, their business, their audience, and samples of their past work.
- What you need: **who they are** (role, what they sell, what they don't do), **who it's for** (a specific audience, not "small business owners"), and **what good looks like** (2–3 examples of their best past work).
- Examples beat adjectives. If the user has samples, ask for them. Match the voice of the samples, not a list of style words. If a sample looks weak, say so, because you will copy its bad habits too.
- If context is missing and the user will use this workflow again, suggest saving it once (project instructions or memory) so later sessions start with it.

## O — Outcome, not task

Turn the task into an outcome. Get answers to these three questions, from context or by asking:
1. **Who is this for?** (specific reader, what they believe, what they're tired of)
2. **What should they do or feel afterwards?**
3. **How will we know it worked?** (success criteria plus hard constraints: length, tone, words or punctuation to avoid)

Write these down as an explicit **brief** with numbered success criteria. Step G grades against this brief.

## R — Reverse interview

Don't guess the gaps. Interview the user:
- Ask the questions you would need answered to do this really well, **one at a time**, waiting for each answer.
- Include at least one question that gets at the real point, e.g. "What's the one belief your audience holds that stops them from acting?"
- Point out anything vague or contradictory in what the user said.
- **Don't start the actual work until the user says "go"** (or clearly signals that they're ready). Before drafting, play back the final brief in a few lines.

Skip or shorten this step only if the user says to, or if the context already answers everything. If you skip it, say what you assumed.

## G — Generate, then grade

1. **Generate 3 genuinely different versions.** Use different angles, structures or hooks, not the same idea reworded three times. Label each with its angle.
2. **Grade each one harshly against the numbered success criteria** from step O. Name a winner and say concretely what is still weak in it. Think the critique through carefully; don't skim.
3. **Fix the winner.** Address every weakness you named and present the final version. Keep the other versions brief or collapsed, unless the user wants them.

## E — Export the win

After the user is happy with the result, offer to turn the session into a reusable template:
- Capture the context, the interview questions that mattered, the success criteria, the grading rubric and the output format.
- Write it as a ready-to-use set of instructions: a project instructions block, or a new skill at `.claude/skills/<name>/SKILL.md` that has its own frontmatter `description`.
- Next time, the whole process runs in one go and needs only new inputs.

## Quick reference

| Step | You do | Done when |
|---|---|---|
| F | Load who/audience/examples | You could describe the reader and the voice |
| O | Write the brief + criteria | Numbered success criteria exist |
| R | Interview one question at a time | User says "go" |
| G | 3 angles → grade → fix | Final version beats every criterion |
| E | Offer reusable template | Saved, or user declined |
