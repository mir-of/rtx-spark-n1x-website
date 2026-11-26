# -*- coding: utf-8 -*-
"""Wrap the original N1X specification report in the site chrome."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
SRC = PROJECT / "report-spec-2026-11-26" / "RTX-Spark-N1X-参数报告.html"
DST = ROOT / "spec.html"

# spec.html is hand-edited after generation (review fixes, role pills, page question).
# Refuse to overwrite it unless the caller explicitly forces a rebuild.
import sys
if DST.exists() and "--force" not in sys.argv:
    raise SystemExit("spec.html contains hand edits; pass --force to rebuild, then reapply the review fixes")

html = SRC.read_text(encoding="utf-8")

# Surface the content/code licences in the generated footer.
LICENSE_LINE = ('  <p class="small">除第三方素材外，文字、表格与图表以 '
                '<a href="LICENSE-CONTENT">CC BY 4.0</a> 授权，代码以 '
                '<a href="LICENSE">MIT</a> 授权；第三方素材见 <a href="NOTICE">NOTICE</a>。</p>\n')
html = html.replace("</footer>", LICENSE_LINE + "</footer>", 1)

# Raw log downloads are not published; drop those rows and leave a note.
def strip_log_rows(doc):
    marker = "<h3>原始文件</h3>"
    start = doc.find(marker)
    if start == -1:
        return doc
    end = doc.find("</table>", start)
    block = doc[start:end]
    block = re.sub(r'<tr><td><a href="logs/[^"]*".*?</tr>\s*', "", block, flags=re.S)
    note = '<tr><td>原始日志</td><td>未随公开站点发布，保留在作者本地</td></tr>\n'
    block = block.replace("</tbody>", note + "      </tbody>", 1)
    return doc[:start] + block + doc[end:]


html = strip_log_rows(html)

# The source report embeds five PNGs as base64 (1.76 MB). Serve the same images
# as external WebP instead, so spec.html stays small and shares the cache with
# evidence.html. Dimensions are the originals in assets/img/spec/.
SPEC_IMAGES = {
    "NVIDIA RTX Spark 官方规格页连续长图": ("spec-long.webp", 3000, 4299),
    "ffmpeg 枚举 NVENC 编码器与 CUVID 解码器": ("shot-ffmpeg-codecs.webp", 2400, 880),
    "ffmpeg 实际编码与解码输出": ("shot-codec-run.webp", 2400, 1094),
    "vulkaninfo 枚举的光追与视频扩展": ("shot-vulkan.webp", 2400, 1522),
    "DLSS 运行时组件版本": ("shot-dlss.webp", 2400, 678),
}


def externalize_spec_images(doc):
    def repl(m):
        tag = m.group(0)
        alt_m = re.search(r'alt="([^"]*)"', tag)
        alt = alt_m.group(1) if alt_m else ""
        if alt not in SPEC_IMAGES:
            raise SystemExit(f"unmapped embedded image in source report: {alt!r}")
        name, w, h = SPEC_IMAGES[alt]
        return (f'<img src="assets/img/spec/{name}" width="{w}" height="{h}" '
                f'loading="lazy" decoding="async" alt="{alt}">')

    return re.sub(r'<img\b[^>]*src="data:image/png;base64,[^"]+"[^>]*>', repl, doc)


html = externalize_spec_images(html)

html = html.replace(
    "<title>NVIDIA RTX Spark N1X 参数与能力报告 · ASUS ProArt GR1X</title>",
    "<title>01 参数与能力报告 · NVIDIA RTX Spark N1X · ASUS ProArt GR1X</title>",
)

# self-contained evidence links
html = html.replace('href="logs/', 'href="assets/logs/')
html = html.replace('href="spec/', 'href="assets/spec/')

TOP = """
<div class="progress-bar" style="position:fixed;left:0;top:0;height:2px;width:0;background:linear-gradient(90deg,#76b900,#c8f36b);z-index:100;transition:width .08s linear"></div>
<header class="topbar">
  <div class="wrap">
    <a class="brand" href="index.html"><span class="mark">N1X</span><span>N1X 全景评测<small>ASUS ProArt GR1X · 2026</small></span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">目录</button>
    <nav class="nav" id="site-nav" aria-label="站点导航">
      <a href="index.html">总览</a>
      <a href="spec.html" class="active">参数</a>
      <a href="nvidia-app.html">配置</a>
      <a href="benchmark.html">基准</a>
      <a href="memory.html">内存</a>
      <a href="memory-story.html">快读</a>
      <a href="qwen.html">推理</a>
      <a href="h3.html">视频</a>
      <a href="evidence.html">证据</a>
      <a href="verdict.html">总评</a>
    </nav>
  </div>
</header>
"""

FRAME = """
<link rel="stylesheet" href="assets/frame.css">
<style>
  .toc{top:56px}
  section{scroll-margin-top:112px}
  @media (max-width:900px){ .toc{top:56px} section{scroll-margin-top:106px} }
</style>
"""

BOTTOM = """
<div class="n1x-return">
  <div class="wrap">
    <a href="index.html">← 返回总览</a>
    <span>下一份：02 NVIDIA App 本机配置图文报告</span>
    <a href="nvidia-app.html">继续阅读 →</a>
  </div>
</div>
<script src="assets/site.js"></script>
"""

html = html.replace("</head>", FRAME + "\n</head>", 1)
html = html.replace("<body>", "<body>\n" + TOP, 1)
html = html.replace("</body>", BOTTOM + "\n</body>", 1)

DST.write_text(html, encoding="utf-8")
print("wrote", DST, len(html), "chars")
