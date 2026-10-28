---
tags: [inbox]
related: ["[[_inbox/TEMPLATE_inbox]]"]
summary: "How the inbox works: raw notes land here, get refined with an agent, then get decomposed into the core buckets."
---

# Inbox

The inbox is the **intake layer** of the vault: raw, unrefined notes live here while they are worked on with agents or collaborators.

## What Goes Here

- Raw notes from conversations with an AI assistant
- Rough drafts without structure or polish
- Work-in-progress ideas awaiting refinement
- Content awaiting decomposition into concepts, patterns, techniques, or case studies

Notes that already clearly fit one core bucket can go straight there; archive material goes in `_archive/`.

## How It Works

### 1. Create a Raw Note
Drop a note into `_inbox/` in any format, named descriptively (`onboarding_ideas.md`, not `notes.md`). Use [[_inbox/TEMPLATE_inbox|the inbox template]] as a scaffold. At minimum:

```yaml
---
tags: [inbox, raw]
status: raw
source: agent-chat | user-created
created: YYYY-MM-DD
---
```

### 2. Iterate and Refine
Work on it with the **Iterate Raw Note** agent or a collaborator:
- Move `status` along: `raw`, then `in-review`, then `ready-to-decompose`
- Add `next-steps` that say concretely what should happen next ("split into two concepts", not "make this better")
- Add `related` links to existing vault notes (full paths, targets must exist)
- Bump `last-updated`

The Iterate Raw Note agent only ever writes inside `_inbox/`.

### 3. Decompose into the Vault
When the note is ready, split it into notes in the core buckets using their templates (the **Decompose Inbox to Concepts** agent does this for concept-worthy material, after you approve its plan). New notes cite their source with `> Derived from [[_inbox/source_note]]`. Then move the raw note to `_archive/`.

## Status Values

- **`raw`**: fresh content, initial exploration
- **`in-review`**: being refined
- **`ready-to-decompose`**: clear enough to split into the vault
- **`archived`**: not used, or already integrated

## Source Values

- **`agent-chat`**: came out of a conversation with an AI assistant
- **`user-created`**: written by hand

## Tips

- Keep it messy if needed; that is what "raw" means.
- Write down questions and gaps; don't hide uncertainty.
- Link to existing vault notes when they are relevant, so agents see the connections.

## Related Concepts

- [[_inbox/TEMPLATE_inbox|Inbox Template]]: the scaffold for new inbox notes
