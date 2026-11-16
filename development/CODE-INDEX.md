# Code index, 3D map and watcher

Everything pearOS is searchable by meaning, locally (no cloud): Qdrant (vector database) + Ollama (`unclemusclez/jina-embeddings-v2-base-code`, 768 dimensions) + an MCP server for Claude Code. One collection per repository. Set up and driven by the `pearos-skill` repository.

## Use it
| need | command |
|---|---|
| search every repository by meaning | `python3 scripts/qdrant-search.py "create window handler" -n 8` (add `--repo SkyLight` to narrow) |
| search one repository from Claude Code | the MCP tool `search_code` (path = the repository) |
| find an exact name (function, class, macro) | `sh scripts/where-is.sh NAME` (ctags index, `sh scripts/symbols.sh` rebuilds it) |
| which collection is which repository | `python3 scripts/qdrant-collections.py` |
| look at the data | dashboard http://localhost:6333/dashboard (collections are named `code_<hash>`; the payload `codebasePath` names the repository) |
| see the whole project as a 3D map | https://pearos-bsd.github.io/codemap/ (points coloured by repository, yellow links between near-identical code in different repositories) |

Ask with short questions that contain concrete verbs and names ("add_window", "glass slot"); vague questions return tests and headers. A top score below ~0.55 means "not found or badly asked". Measured on 2026-11-16: 0.25 s and ~215 tokens per result list, against ~12 000 tokens for a grep dump of the same topic.

## Keep it in sync
The index lags behind the files. After editing a repository: `python3 scripts/qdrant-wait.py <repo>` (re-indexes the changes and waits until Qdrant is green), and only then trust a search. A watcher does it every five minutes: `screen -dmS pearindex sh scripts/qdrant-watch.sh` (stop: `screen -S pearindex -X quit`); it also republishes the map to the `codemap` repository.

## What is and is not indexed
Not indexed: `upstream/` (reference code of other projects), `catalogs/`, generated files (`*_Generated.*`, golden data, harvest tables), binaries, `*.json`, `*.txt`. Not indexed on purpose as repositories: AppStore-Backend, virtio, clevo_wmi, kext, misc, pkgbuild, package-repo, codemap, .github. `ploader` is indexed without the vendored rEFInd parts.

## Gotcha (cost two hours once)
The MCP server we build ignores `CODE_CUSTOM_IGNORE` and `CODE_CUSTOM_EXTENSIONS`, so `upstream/` was indexed (CoreFoundation alone produced 2185 chunks from ravynOS code). `patches/mcp-env-ignore.py` fixes the build; `qdrant-setup.sh` applies it. After every full index check that no point has a `relativePath` starting with `upstream/`.

## Speed
About 0.5 chunks per second on CPU (Ollama on 8 cores, shared with the VMs): the whole project is ~5 200 chunks, around two hours for the first full index; later runs only touch changed files.
