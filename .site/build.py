#!/usr/bin/env python3
"""Build https://pearos-bsd.github.io/docs/ from the Markdown files of this repository, where they are.

    python3 .site/build.py            # -> _build/site (what GitHub Pages serves)
    python3 .site/build.py --serve    # live preview on http://127.0.0.1:8000/docs/

Nothing in the repository is moved or edited. The files are copied to _build/docs and only the copies are touched:
  * a small front matter is added (last commit date, source path) for "Last updated" and "Edit this page";
  * a folder with no README.md / index.md gets a generated overview page that lists its documents;
  * links to a folder (`development/`) are pointed at that folder's page.
The navigation is generated here too, so a new .md file appears on the site at the next push with no config change:
top-level pages in the order README.md links them, then the others; one section per folder, where files that share
a name prefix (DOCK-*, CONTROLCENTER-*) are grouped together.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "_build")
DOCS = os.path.join(OUT, "docs")
SKIP_DIRS = {".git", ".github", ".site", "_build", "site", "node_modules", "upstream"}
ASSET_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".mp4", ".webm"}

# words that do not title-case well when a label is made from a file name
WORDS = {"macos": "macOS", "ui": "UI", "ios": "iOS", "controlcenter": "ControlCenter", "iokit": "IOKit", "dyld": "dyld",
         "repos": "Repositories", "repo": "Repository", "config": "Configuration", "abi": "ABI", "iso": "ISO",
         "api": "API", "cli": "CLI", "rea": "REA", "vm": "VM", "xpc": "XPC", "appkit": "AppKit", "windowserver": "WindowServer",
         "skylight": "SkyLight", "coreui": "CoreUI", "freebsd": "FreeBSD", "mac": "Mac"}


def git(*args):
    try:
        return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def h1(text):
    m = re.search(r"^#\s+(.+?)\s*#*\s*$", text, re.M)
    return m.group(1).strip() if m else None


def summary(text, limit=170):
    """First real paragraph of a document, as plain text."""
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    for block in re.split(r"\n\s*\n", body):
        b = block.strip()
        if not b or b.startswith(("#", "|", "```", "<", "!", "-", "*", "1.", ">")):
            continue
        b = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", b)
        b = re.sub(r"[`*_]", "", b)
        b = " ".join(b.split())
        return b if len(b) <= limit else b[:limit].rsplit(" ", 1)[0] + "…"
    return ""


def pretty(stem):
    """DOCK-SERVICES -> Dock services, what-is-pearos -> What is pearos."""
    words = [w for w in re.split(r"[-_\s]+", stem) if w]
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in WORDS:
            out.append(WORDS[lw])
        else:
            out.append(lw.capitalize() if i == 0 else lw)
    return " ".join(out)


def front_matter(meta, text):
    """Prepend (or merge into) a YAML front matter block."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        old = yaml.safe_load(m.group(1)) or {}
        old.update({k: v for k, v in meta.items() if k not in old})
        meta, text = old, text[m.end():]
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---\n\n" + text


def stage():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(DOCS)
    pages = {}   # relative path -> info
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        rel_dir = os.path.relpath(dirpath, ROOT)
        rel_dir = "" if rel_dir == "." else rel_dir
        for fn in sorted(filenames):
            src = os.path.join(dirpath, fn)
            rel = os.path.join(rel_dir, fn) if rel_dir else fn
            ext = os.path.splitext(fn)[1].lower()
            if ext == ".md":
                text = open(src, encoding="utf-8").read()
                iso = git("log", "-1", "--format=%cI", "--", rel)
                pages[rel] = {"rel": rel, "dir": rel_dir, "stem": os.path.splitext(fn)[0], "text": text,
                              "title": h1(text) or pretty(os.path.splitext(fn)[0]), "summary": summary(text),
                              "updated": iso}
            elif ext in ASSET_EXT:
                os.makedirs(os.path.join(DOCS, rel_dir), exist_ok=True)
                shutil.copy2(src, os.path.join(DOCS, rel))
    # folders that have documents but no landing page get a generated overview
    dirs = sorted({p["dir"] for p in pages.values() if p["dir"]})
    for d in dirs:
        parts = d.split(os.sep)
        for i in range(1, len(parts)):
            if os.sep.join(parts[:i]) not in dirs:
                dirs.append(os.sep.join(parts[:i]))
    generated = {}
    for d in sorted(set(dirs)):
        if any(os.path.join(d, n) in pages for n in ("README.md", "index.md")):
            continue
        generated[d] = os.path.join(d, "index.md")
    return pages, generated


def is_index(p):
    return p["stem"].lower() in ("readme", "index")


def date_text(iso):
    if not iso:
        return ""
    d = datetime.datetime.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def groups_of(files):
    """Group the files of one folder by the first word of the name when at least two share it."""
    first = {}
    for p in files:
        first.setdefault(re.split(r"[-_]", p["stem"])[0].lower(), []).append(p)
    out = []
    for key, members in first.items():
        if len(members) >= 2 and len(members) < len(files):
            out.append((WORDS.get(key, key.capitalize()), key, sorted(members, key=lambda p: p["stem"].lower())))
        else:
            out.extend((None, None, [p]) for p in members)
    return sorted(out, key=lambda g: (g[0] or pretty(g[2][0]["stem"])).lower())


def label_in_group(p, key):
    rest = re.sub(rf"^{re.escape(key)}[-_]", "", p["stem"], flags=re.I) if key else p["stem"]
    return pretty(rest)


def readme_order(text):
    return [re.sub(r"/$", "", m) for m in re.findall(r"\]\(([^)#\s]+\.md|[^)#\s]+/)\)", text or "")]


def readme_descriptions(text):
    """`| [Label](target) | description |` rows of README.md -> {target: description}."""
    out = {}
    for target, desc in re.findall(r"^\|\s*\[[^\]]+\]\(([^)#\s]+)\)\s*\|\s*([^|]+?)\s*\|", text or "", re.M):
        d = re.sub(r"[`*_]", "", desc).strip()
        out[target.rstrip("/")] = d[:1].upper() + d[1:] if d else ""
    return out


def link_fix(text, rel_dir, generated, readmes):
    """Point links to a folder (`development/`) at that folder's page (only in the staged copy)."""
    def repl(m):
        target = m.group(2)
        if re.match(r"^[a-z]+:", target) or not target.endswith("/"):
            return m.group(0)
        path = os.path.normpath(os.path.join(rel_dir, target.rstrip("/")))
        if path in generated:
            return f"{m.group(1)}({target}index.md)"
        if path in readmes:
            return f"{m.group(1)}({target}README.md)"
        return m.group(0)
    return re.sub(r"(\[[^\]]*\])\(([^)\s]+)\)", repl, text)


def table(rows):
    out = ["| Document | About | Updated |", "|---|---|---|"]
    for label, p in rows:
        about = (p["title"] if p["title"] != pretty(p["stem"]) else p["summary"]).replace("|", "\\|")
        out.append(f"| [{label}]({os.path.basename(p['rel'])}) | {about} | {date_text(p['updated'])} |")
    return out + [""]


def write(pages, generated):
    root_readme = pages.get("README.md")
    readmes = {p["dir"] for p in pages.values() if p["stem"].lower() == "readme" and p["dir"]}
    for rel, p in pages.items():
        meta = {"source": rel}
        if p["updated"]:
            meta["revision_date"] = date_text(p["updated"])
        text = p["text"]
        if rel == "README.md":
            meta.update({"template": "home.html", "hide": ["navigation", "toc"], "title": "Home"})
        dst = os.path.join(DOCS, rel)
        os.makedirs(os.path.dirname(dst) or DOCS, exist_ok=True)
        open(dst, "w", encoding="utf-8").write(front_matter(meta, link_fix(text, p["dir"], generated, readmes)))
    for d, rel in generated.items():
        files = sorted((p for p in pages.values() if p["dir"] == d), key=lambda p: p["stem"].lower())
        subdirs = sorted(x for x in generated if os.path.dirname(x) == d)
        title = pretty(os.path.basename(d))
        lines = [f"# {title}", "",
                 f"All the documents in `{d}/`, generated from the files themselves: a new file here shows up on its own.", ""]
        gs = groups_of(files)
        named = [g for g in gs if g[0]]
        loose = [g[2][0] for g in gs if not g[0]]
        for name, key, members in named:
            lines += [f"## {name}", ""] + table([(label_in_group(p, key), p) for p in members])
        if loose:
            if named:
                lines += ["## Other documents", ""]
            lines += table([(pretty(p["stem"]), p) for p in loose])
        for s in subdirs:
            lines += [f"- [{pretty(os.path.basename(s))}]({os.path.basename(s)}/index.md)"]
        meta = {"source": d + "/", "generated": True, "title": title}
        open(os.path.join(DOCS, rel), "w", encoding="utf-8").write(front_matter(meta, "\n".join(lines) + "\n"))
    # data for the home page: the cards follow the "Start here" table of README.md, then any other top-level page
    cards, seen = [], set()
    rtext = root_readme and root_readme["text"]
    descs = readme_descriptions(rtext)
    pick = lambda summ, desc: summ if len(summ) >= 60 or not desc else (desc if desc.endswith(".") else desc + ".")
    for target in readme_order(rtext):
        t = target[:-1] if target.endswith("/") else target
        if t in seen:
            continue
        if t in pages and not is_index(pages[t]) and not pages[t]["dir"]:
            p = pages[t]
            cards.append({"title": p["title"], "text": pick(p["summary"], descs.get(t, "")), "url": t[:-3] + "/"})
            seen.add(t)
        elif t in generated or t in readmes:
            n = sum(1 for p in pages.values() if p["dir"] == t)
            cards.append({"title": pretty(os.path.basename(t)), "text": pick("", descs.get(t, "")) + f" {n} documents.", "url": t + "/"})
            seen.add(t)
    for rel, p in sorted(pages.items()):
        if not p["dir"] and not is_index(p) and rel not in seen:
            cards.append({"title": p["title"], "text": p["summary"], "url": rel[:-3] + "/"})
    recent = sorted((p for p in pages.values() if p["updated"] and not is_index(p)), key=lambda p: p["updated"], reverse=True)[:6]
    home = {"cards": cards,
            "recent": [{"title": p["title"], "url": p["rel"][:-3] + "/", "date": date_text(p["updated"]),
                        "section": pretty(p["dir"]) if p["dir"] else "Guide"} for p in recent],
            "count": len(pages), "updated": date_text(max((p["updated"] for p in pages.values() if p["updated"]), default=""))}
    return home


def nav(pages, generated):
    out = [{"Home": "README.md"}] if "README.md" in pages else []
    top = [p for p in pages.values() if not p["dir"] and not is_index(p)]
    order = readme_order(pages.get("README.md", {}).get("text"))
    top.sort(key=lambda p: (order.index(p["rel"]) if p["rel"] in order else 999, p["title"].lower()))
    out += [{p["title"]: p["rel"]} for p in top]

    def section(d):
        items = [generated[d]] if d in generated else [os.path.join(d, "README.md") if os.path.join(d, "README.md") in pages else os.path.join(d, "index.md")]
        files = [p for p in pages.values() if p["dir"] == d and not is_index(p)]
        for name, key, members in groups_of(files):
            if name:
                items.append({name: [{label_in_group(p, key): p["rel"]} for p in members]})
            else:
                items.append({pretty(members[0]["stem"]): members[0]["rel"]})
        for sub in sorted({p["dir"] for p in pages.values()} | set(generated)):
            if sub and os.path.dirname(sub) == d:
                items.append(section(sub))
        return {pretty(os.path.basename(d)): items}

    for d in sorted({p["dir"] for p in pages.values()} | set(generated)):
        if d and os.sep not in d:
            out.append(section(d))
    return out


def main():
    pages, generated = stage()
    home = write(pages, generated)
    cfg = yaml.safe_load(open(os.path.join(HERE, "mkdocs.yml"), encoding="utf-8"))
    cfg.update({"docs_dir": DOCS, "site_dir": os.path.join(OUT, "site"), "nav": nav(pages, generated)})
    cfg["theme"]["custom_dir"] = os.path.join(HERE, "overrides")
    cfg.setdefault("extra", {})["home"] = home
    # theme assets (css, logo) live in .site/assets and are copied next to the pages
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(DOCS, "assets"), dirs_exist_ok=True)
    conf = os.path.join(OUT, "mkdocs.yml")
    # Mermaid diagrams (```mermaid blocks) are rendered by Material; the fence formatter is a Python reference,
    # which safe YAML cannot write, so it goes in as a placeholder replaced in the text
    for i, ext in enumerate(cfg["markdown_extensions"]):
        if ext == "pymdownx.superfences" or (isinstance(ext, dict) and "pymdownx.superfences" in ext):
            cfg["markdown_extensions"][i] = {"pymdownx.superfences": {"custom_fences": [{"name": "mermaid", "class": "mermaid", "format": "__FENCE_CODE_FORMAT__"}]}}
    text = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True).replace("__FENCE_CODE_FORMAT__", "!!python/name:pymdownx.superfences.fence_code_format")
    open(conf, "w", encoding="utf-8").write(text)
    print(f"staged {len(pages)} documents, {len(generated)} generated overview page(s)")
    cmd = [sys.executable, "-m", "mkdocs", "serve" if "--serve" in sys.argv else "build", "-f", conf]
    if "--serve" not in sys.argv:
        cmd.append("--strict")
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
