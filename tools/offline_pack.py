"""Build a shareable offline ZIP of the site.

Usage: py314\\python.exe -I tools\\offline_pack.py

Packaging is allowlist-only: the eleven root HTML pages, the whole assets/ tree and
NOTICE. Nothing else is packed -- README.md, _headers, .gitignore, .nojekyll,
tools/ (.github/ included), any *.zip and assets/logs/ are never included, even
if they reappear in the working tree. A short 使用说明.txt is injected at the
archive root and is not part of the served site.
"""
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "N1X-RTX-Spark-评测网站-离线版-2026-11-27.zip"
TOP = "N1X-RTX-Spark-评测网站"

# Root pages, in reading order. Keep in sync with README.md.
PAGES = (
    "index.html",
    "spec.html",
    "memory.html",
    "memory-story.html",
    "benchmark.html",
    "nvidia-app.html",
    "qwen.html",
    "h3.html",
    "wukong.html",
    "evidence.html",
    "verdict.html",
)

# Non-page root files that are deliberately part of the offline package.
EXTRA_FILES = ("NOTICE", "LICENSE", "LICENSE-CONTENT")

# assets/ is walked as a whole; these paths are skipped defensively so that a
# future purge/QA artifact can never slip back into a distributable archive.
SKIP_ASSET_DIRS = ("assets/logs",)
SKIP_DIR_NAMES = {".git", ".github", "__pycache__", "tmp", "qa", "perf-tmp"}

README = """N1X RTX Spark 全景评测 · 离线版
==============================

打开方式
  解压后双击 index.html 即可阅读，不需要联网，也不需要本地服务器。
  推荐 Chrome / Edge / Firefox 等现代浏览器。

页面
  index.html          总览与三条阅读路径（建议从这里开始）
  spec.html           原始参数报告全文
  memory.html         内存与带宽实测全文
  memory-story.html   10 分钟长文《同一个 GB10，两种内存命运》
  benchmark.html      GPU 性能基准调研
  nvidia-app.html     NVIDIA App 本机硬件与软件配置图文
  qwen.html           Qwen3.8-27B 本地推理性能与质量测试
  h3.html             MiniMax H3 5s / 10s 视频生成实测
  wukong.html         《黑神话：悟空》ARM64 游戏实测
  evidence.html       证据墙与原始读数
  verdict.html        结论与选型

说明
  · 全站为静态文件，样式、图片、脚本都已随包携带，断网可完整阅读。
  · 文中指向 nvidia.com / asus.com / geekbench.com 等外部链接需要联网。
  · assets/downloads/ 内含 4 份 PDF 报告；assets/spec/ 为官方规格页归档
    （归档页已用 CSP 禁用脚本，不执行第三方脚本、不写 Cookie）。
  · 为保证体积，原始 mp4 录屏未打包（网站正文也未引用）。
  · 若浏览器限制本地文件，可在本目录执行
        python -m http.server 8000
    然后访问 http://127.0.0.1:8000/
"""


def collect_files():
    """Return (path, archive-relative-name) pairs from the allowlist."""
    files = []

    for name in PAGES + EXTRA_FILES:
        path = ROOT / name
        if not path.is_file():
            raise SystemExit(f"allowlisted file is missing: {path}")
        files.append((path, name))

    assets = ROOT / "assets"
    if not assets.is_dir():
        raise SystemExit(f"allowlisted directory is missing: {assets}")

    for path in sorted(assets.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        rel_posix = rel.as_posix()
        if any(rel_posix == d or rel_posix.startswith(d + "/") for d in SKIP_ASSET_DIRS):
            continue
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if path.suffix.lower() == ".zip":
            continue
        files.append((path, rel_posix))

    return files


def main():
    files = collect_files()

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path, rel in files:
            zf.write(path, TOP + "/" + rel)
        zf.writestr(TOP + "/使用说明.txt", README)

    size = OUT.stat().st_size / 1024 / 1024
    print("wrote", OUT)
    print("entries", len(files) + 1, "files,", f"{size:.1f} MB")


if __name__ == "__main__":
    main()
