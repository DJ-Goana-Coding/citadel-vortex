---
title: citadel-vortex
emoji: 🏆
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

This Space deploys the lightweight FastAPI app defined in `/home/runner/work/citadel-vortex/citadel-vortex/app.py`.
`/home/runner/work/citadel-vortex/citadel-vortex/main.py` stays in the repository unchanged, but it is not used for the Hugging Face runtime because it depends on additional trading services and packages that are not part of this minimal Space deployment.

## Deployment notes

- GitHub Actions synchronizes `main` to `https://huggingface.co/spaces/DJ-Goanna-Coding/citadel-vortex` through `.github/workflows/hf-sync.yml`.
- The workflow reads the existing `HF_TOKEN` GitHub secret at runtime and authenticates with `GIT_ASKPASS`, so the token is never committed or embedded in the remote URL.
- The workflow only performs fast-forward-safe synchronization. If the target Space still has unrelated starter-template history, the job fails deliberately instead of force-pushing over it.

## Safe handling for starter-template history

Some Hugging Face Spaces are created from a starter template, which can leave the Space with an unrelated initial commit history. If the first sync fails with a non-fast-forward or unrelated-history error:

1. Review the Space commit history and confirm it only contains disposable starter-template/bootstrap commits.
2. From a trusted maintainer environment, perform a one-time manual replacement using a reviewed `--force-with-lease` push.
3. After the histories match, re-run the workflow so future deployments stay fast-forward-only.
