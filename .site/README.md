# Docs site

https://pearos-bsd.github.io/docs/ is built from the Markdown files of this repository by `.github/workflows/pages.yml`
on every push to `main`. Write documents as usual, anywhere in the repository: they are not moved or edited.

- `build.py` copies the `.md` files to `_build/docs`, adds "Last updated" from git, generates the navigation (a new file
  shows up by itself; files sharing a prefix such as `DOCK-*` become one section) and an overview page for any folder
  without a README, then runs MkDocs.
- `mkdocs.yml` is the base configuration (theme, features, Markdown extensions). Do not add `nav:` to it.
- `overrides/` holds the home page and the page actions; `assets/` holds the stylesheet and the logo.

Preview locally:

```sh
pip install -r .site/requirements.txt
python3 .site/build.py --serve      # http://127.0.0.1:8000/docs/
```
