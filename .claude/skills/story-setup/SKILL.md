---
name: story-setup
description: Set up the story-telling environment. Checks Node, installs dependencies, creates .env from the template, verifies the Sarvam, fal and OpenAI keys, and confirms all Remotion packages are on one version.
argument-hint: "[project-directory]"

---

Prepare the project so `story-new` and `story-render` can run without surprises.

## Arguments

- `$0` = project directory (optional, default: current directory)

## Steps

### Step 0: Bootstrap the project if it is not here

The skills carry the craft: the rules, the schema and the story templates. The
pipeline they drive, `cli/` and `src/`, lives in the project repo. When someone
installs only the skills with `npx skills add`, that pipeline is missing and
has to be fetched once.

Detect it:

```bash
test -f cli/generate.ts && test -f src/Root.tsx && echo "project present" || echo "project missing"
```

If it is missing, look one level down as well, in case it was fetched before:

```bash
test -f story-telling/cli/generate.ts && echo "project in ./story-telling"
```

Still missing, fetch it. Tell the user what is about to be downloaded and
where, then run one of these from the directory they want it in:

```bash
# Preferred: no git history, small download
npx --yes degit marketcalls/story-telling story-telling

# Fallback if degit is unavailable
git clone --depth 1 https://github.com/marketcalls/story-telling story-telling
```

Then `cd story-telling` and continue with Step 1. Everything after this point
runs from the project root, the directory holding `package.json`.

If the current directory is already the project, skip all of this.

### Step 1: Check Node

```bash
node --version
npm --version
```

Node 20 or newer is required. Neither bun nor ffmpeg is needed: the CLI runs
through `npx tsx`, and durations are measured with `@remotion/media-parser`.

### Step 2: Install dependencies

```bash
npm install
```

### Step 3: Create .env

If `.env` does not exist, copy the template and tell the user which keys to
fill in:

```bash
cp .env.example .env
```

Never write a real key into `.env.example`, into a skill file, or into
`.claude/settings.local.json`. If an existing key is found in any tracked file,
stop and tell the user to rotate it.

Required:

- `SARVAM_API_KEY` from sarvam.ai, for narration
- `FAL_KEY` from fal.ai, for images

Optional:

- `OPENAI_API_KEY`, only for `npm run draft`. Writing `story.json` by hand
  skips it entirely.

`cli/env.ts` also reads a `.env` in the parent folder, so a shared key file one
level up works. `SARVAM_KEY` is accepted as an alias for `SARVAM_API_KEY`.

### Step 4: Verify the keys

Do this before any long run: a bad key discovered after twelve images is an
expensive way to find out.

```bash
set -a && . ./.env && set +a

# OpenAI, expect 200
curl -s -o /dev/null -w "openai %{http_code}\n" https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Sarvam, expect 200
curl -s -o /dev/null -w "sarvam %{http_code}\n" -X POST https://api.sarvam.ai/text-to-speech \
  -H "api-subscription-key: $SARVAM_API_KEY" -H "Content-Type: application/json" \
  -d '{"text":"key test","language_code":"en-IN","speaker":"shubh","model":"bulbul:v3"}'

# fal, expect IN_QUEUE then a validation error on the missing prompt, which costs nothing
curl -s -X POST https://queue.fal.run/fal-ai/flux-2-pro \
  -H "Authorization: Key $FAL_KEY" -H "Content-Type: application/json" -d '{}' | head -c 120
```

Never print a key value back to the user or into a log.

### Step 5: Check the Remotion install

```bash
npx remotion versions
```

Every `@remotion/*` package must report the same version, with the matching
`mediabunny`. A mixed install fails at bundling with
`export 'Logging' was not found in 'mediabunny'`. Fix with:

```bash
npx remotion upgrade
npm install <the exact list it prints>
```

### Step 6: Typecheck and smoke test

```bash
npm run typecheck
npx remotion compositions
```

`compositions` should list one composition per story folder under `public/`.
The shipped example prints `Jhunjhunwala 30 1920x1080 1760 (58.67 sec)`, though
its media files are gitignored, so a fresh clone shows the story with no assets
until it is regenerated.

### Step 7: Report

Tell the user:

- Node and npm versions found
- Whether `.env` was created or already existed, and which keys are missing
- Result of each key check, as a status code, never the key
- Whether Remotion versions are aligned
- The exact next command, for example
  `npm run story -- --slug my-story --context ./article.md --seconds 60`

## Example usage

`/story-setup`
`/story-setup ./story-telling`
