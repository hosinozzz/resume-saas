_WATERMARK_ROWS = 8
_WATERMARK_TEXT = "PREVIEW - 500円で完全版ダウンロード"

_STYLE = """
<style id="wm-style">
.wm-overlay{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;overflow:hidden}
.wm-line{position:absolute;width:140%;left:-20%;text-align:center;font-size:1.8rem;font-weight:900;
  color:rgba(255,80,80,.13);transform:rotate(-30deg);user-select:none;white-space:nowrap;
  font-family:sans-serif;letter-spacing:.05em}
</style>"""

_OVERLAY = (
    '<div class="wm-overlay">'
    + "".join(
        f'<div class="wm-line" style="top:{i * 13}%">{_WATERMARK_TEXT}</div>'
        for i in range(_WATERMARK_ROWS)
    )
    + "</div>"
)

# キーボードショートカット（Ctrl+S / Ctrl+P / Ctrl+U）を無効化
_GUARD_SCRIPT = """
<script>
(function(){
  document.addEventListener('contextmenu',function(e){e.preventDefault()});
  document.addEventListener('keydown',function(e){
    if((e.ctrlKey||e.metaKey)&&['s','p','u'].includes(e.key.toLowerCase()))e.preventDefault();
  });
})();
</script>"""


def add_watermark(html: str) -> str:
    """クリーンHTMLにウォーターマークを付与して返す。"""
    inject = _STYLE + _OVERLAY + _GUARD_SCRIPT
    if "</body>" in html:
        return html.replace("</body>", inject + "</body>", 1)
    return html + inject
