"""
Local dev server with live reload.

Watches posts/, templates/, static/, authors/, and build.py for changes;
rebuilds the site on every save; auto-refreshes the browser. Build errors
(broken wikilinks, bad frontmatter) are printed to the terminal and the
browser keeps showing the last successful build.

Run: python serve.py
Then open http://localhost:8000

Stop with Ctrl-C.
"""

import sys
from livereload import Server

import build as build_module


def safe_rebuild():
    try:
        # Drafts are only visible during local development, never on the
        # production GitHub Actions build.
        build_module.build(include_drafts=True)
    except build_module.BuildError as e:
        # Don't crash the server — just print and keep serving the last
        # good build. The error stays on screen until you fix it.
        print(f"\n  ✗ Build failed: {e}\n", file=sys.stderr)
    except Exception as e:
        print(f"\n  ✗ Unexpected error: {e}\n", file=sys.stderr)


# Initial build so dist/ exists before the server starts.
safe_rebuild()

server = Server()
# Each call to server.watch() registers a glob; when a matching file
# changes, the callback runs and a browser reload is triggered.
server.watch("posts/*.md", safe_rebuild)
server.watch("templates/*.html", safe_rebuild)
server.watch("templates/*.xml", safe_rebuild)
server.watch("static/**/*", safe_rebuild)
server.watch("authors/*.yaml", safe_rebuild)
server.watch("build.py", safe_rebuild)

print("\n  Math for the People — dev server")
print("  → http://localhost:8000")
print("  → editing any source file triggers a rebuild + browser refresh")
print("  → Ctrl-C to stop\n")

server.serve(root="dist", port=8000, host="localhost", open_url_delay=None)
