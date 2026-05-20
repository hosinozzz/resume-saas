"""6テンプレート対応HTMLポートフォリオジェネレーター。"""
from html import escape as _e

TEMPLATES = ['dark_tech', 'business_clean', 'minimal_pro', 'creative_bold', 'medical_care', 'academic']

TEMPLATE_LABELS = {
    'dark_tech':      'Dark Tech',
    'business_clean': 'Business Clean',
    'minimal_pro':    'Minimal Pro',
    'creative_bold':  'Creative Bold',
    'medical_care':   'Medical Care',
    'academic':       'Academic',
}


def select_template(data: dict) -> str:
    """職種・スキルキーワードから最適なテンプレートを自動選択する。"""
    meta = data.get('meta', {})
    job_type = str(meta.get('job_type', '')).lower()
    skill_text = ' '.join(str(s.get('category', '')) for s in data.get('skills', [])).lower()
    career_text = ' '.join(
        str(j.get('role', '')) + ' ' + str(j.get('company', ''))
        for j in data.get('career', [])
    ).lower()
    t = f"{job_type} {skill_text} {career_text}"

    if any(k in t for k in ['医療', '看護', '福祉', '介護', '薬剤', '病院', '医師', '保健', '理学', '作業療法']):
        return 'medical_care'
    if any(k in t for k in ['教育', '研究', '公務員', '教員', '教師', '大学', '学校', '行政', '公立', '国家公務']):
        return 'academic'
    if any(k in t for k in ['デザイン', 'design', 'クリエイティブ', '広告', 'ui', 'ux', 'イラスト', 'アート', 'グラフィック', '映像']):
        return 'creative_bold'
    if any(k in t for k in ['事務', '経理', '会計', '総務', '法務', 'コンサル', '財務', '税理', '簿記', '監査']):
        return 'minimal_pro'
    if any(k in t for k in ['営業', '企画', 'マーケ', '管理職', 'マネージャー', 'マネージャ', '人事', '採用', '広報']):
        return 'business_clean'
    return 'dark_tech'


def generate_portfolio_html(data: dict, template: str = None, photo_b64: str | None = None) -> str:
    """指定テンプレートでHTMLポートフォリオを生成する。templateがNoneなら自動選択。"""
    if template is None:
        template = select_template(data)
    fn = {
        'dark_tech':      _gen_dark_tech,
        'business_clean': _gen_business_clean,
        'minimal_pro':    _gen_minimal_pro,
        'creative_bold':  _gen_creative_bold,
        'medical_care':   _gen_medical_care,
        'academic':       _gen_academic,
    }.get(template, _gen_dark_tech)
    return fn(data, photo_b64=photo_b64)


# ─── 共有ビルダー ─────────────────────────────────────────────────────────────

def _build_photo(name_raw: str, photo_b64: str | None) -> str:
    """写真またはイニシャル（フォールバック）のHTMLを返す。"""
    if photo_b64:
        return (
            f'<div class="hero-photo">'
            f'<img src="{photo_b64}" alt="プロフィール写真" class="hero-photo-img">'
            f'</div>'
        )
    initial = next((ch for ch in name_raw if ch.strip()), "?")
    return f'<div class="hero-photo hero-photo-initial"><span>{_e(initial)}</span></div>'


def _build_skills(skills: list) -> str:
    if not skills:
        return ''
    parts = []
    for sk in skills:
        cat  = _e(str(sk.get('category', '')))
        items = sk.get('items', [])
        pct  = int(min(max(float(sk.get('level', 0.7)), 0.0), 1.0) * 100)
        tags = ' '.join(f'<span class="tag">{_e(str(i))}</span>' for i in items)
        parts.append(
            f'<div class="skill-card">'
            f'<div class="skill-header"><span class="skill-category">{cat}</span>'
            f'<span class="skill-pct">{pct}%</span></div>'
            f'<div class="skill-bar"><div class="skill-fill" data-pct="{pct}"></div></div>'
            f'<div class="skill-tags">{tags}</div>'
            f'</div>'
        )
    return '\n'.join(parts)


def _build_certs(certs: list) -> str:
    if not certs:
        return '<p class="empty">資格情報なし</p>'
    parts = []
    for c in certs:
        date  = _e(str(c.get('date', '')))
        name  = _e(str(c.get('name', '')))
        top   = c.get('is_top', False)
        badge = '<span class="top-badge">★ 主要</span>' if top else ''
        cls   = 'cert-item top' if top else 'cert-item'
        parts.append(
            f'<div class="{cls}">'
            f'<span class="cert-date">{date}</span>'
            f'<span class="cert-name">{name}</span>{badge}'
            f'</div>'
        )
    return '\n'.join(parts)


def _build_career(career: list) -> str:
    if not career:
        return '<p class="empty">職歴情報なし</p>'
    parts = []
    for job in career:
        period  = _e(str(job.get('period', '')))
        company = _e(str(job.get('company', '')))
        role    = _e(str(job.get('role', '')))
        bullets = job.get('bullets', [])
        tags    = job.get('tags', [])
        bl_html  = '\n'.join(f'<li>{_e(str(b))}</li>' for b in bullets)
        tag_html = ' '.join(f'<span class="tag tag-sm">{_e(str(t))}</span>' for t in tags)
        parts.append(
            f'<div class="timeline-item">'
            f'<div class="tl-dot"></div>'
            f'<div class="tl-content">'
            f'<p class="tl-period">{period}</p>'
            f'<h3 class="tl-company">{company}</h3>'
            f'<p class="tl-role">{role}</p>'
            + (f'<ul class="tl-bullets">{bl_html}</ul>' if bl_html else '')
            + (f'<div class="tl-tags">{tag_html}</div>' if tag_html else '')
            + '</div></div>'
        )
    return '\n'.join(parts)


def _profile_table(profile: dict) -> str:
    name     = _e(profile.get('name', ''))
    kana     = _e(profile.get('kana', ''))
    dob      = _e(profile.get('dob', ''))
    location = _e(profile.get('location', ''))
    tel      = _e(profile.get('tel', ''))
    pr       = _e(profile.get('pr', ''))
    rows = ''
    if name:
        rows += f'<tr><th>氏名</th><td>{name}' + (f'&emsp;<small>{kana}</small>' if kana else '') + '</td></tr>'
    if dob:
        rows += f'<tr><th>生年月日</th><td>{dob}</td></tr>'
    if location:
        rows += f'<tr><th>所在地</th><td>{location}</td></tr>'
    if tel:
        rows += f'<tr><th>電話番号</th><td>{tel}</td></tr>'
    pr_html = (
        f'<div class="pr-box"><h3>自己PR</h3>'
        f'<p>{pr.replace(chr(10), "<br>")}</p></div>'
    ) if pr else ''
    return f'<table class="profile-table">{rows}</table>{pr_html}'


_JS_COMMON = """
(function(){
  var io=new IntersectionObserver(function(e){
    e.forEach(function(x){if(x.isIntersecting){x.target.classList.add('visible');io.unobserve(x.target);}});
  },{threshold:0.12});
  document.querySelectorAll('.fade-in').forEach(function(el){io.observe(el);});
})();
(function(){
  var bio=new IntersectionObserver(function(e){
    e.forEach(function(x){
      if(x.isIntersecting){
        var f=x.target.querySelector('.skill-fill');
        if(f)f.style.width=f.dataset.pct+'%';
        bio.unobserve(x.target);
      }
    });
  },{threshold:0.3});
  document.querySelectorAll('.skill-card').forEach(function(el){bio.observe(el);});
})();
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DARK TECH  ── IT / インフラ / SES
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_DARK_TECH = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#0a0f1e;--navy2:#0d1529;--navy3:#111d3a;
  --cyan:#00d4ff;--cyan2:#00a8cc;--cyan3:#006f88;
  --white:#e8f0ff;--gray:#8899bb;
  --card:rgba(255,255,255,.04);--border:rgba(0,212,255,.15);--radius:12px;
}
html{scroll-behavior:smooth}
body{font-family:'Noto Sans JP',sans-serif;background:var(--navy);color:var(--white);line-height:1.7}
.hero{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden;padding:4rem 2rem}
.hero-bg{position:absolute;inset:0;
  background:radial-gradient(ellipse 80% 60% at 50% 40%,rgba(0,212,255,.12) 0%,transparent 70%),
    linear-gradient(180deg,#050a18 0%,var(--navy) 100%)}
.hero-bg::after{content:'';position:absolute;inset:0;
  background-image:linear-gradient(rgba(0,212,255,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,212,255,.04) 1px,transparent 1px);
  background-size:40px 40px}
.hero-content{position:relative;z-index:1;max-width:700px}
.hero-kana{font-family:'JetBrains Mono',monospace;font-size:.85rem;letter-spacing:.3em;color:var(--cyan);margin-bottom:.5rem}
.hero-name{font-family:'Bebas Neue',cursive;font-size:clamp(3.5rem,10vw,6rem);letter-spacing:.08em;
  background:linear-gradient(135deg,var(--white) 40%,var(--cyan));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.1}
.hero-badge{display:inline-block;margin:1rem 0;padding:.3rem 1.2rem;border:1px solid var(--cyan3);
  border-radius:999px;font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--cyan);letter-spacing:.1em}
.hero-summary{font-size:1rem;color:var(--gray);max-width:540px;margin:0 auto 1.5rem}
.hero-meta{display:flex;gap:1.5rem;justify-content:center;flex-wrap:wrap;font-size:.85rem;color:var(--gray)}
.section{padding:5rem 2rem}
.section-alt{background:var(--navy2)}
.container{max-width:900px;margin:0 auto}
.section-title{font-family:'Bebas Neue',cursive;font-size:2.8rem;letter-spacing:.12em;color:var(--white);
  margin-bottom:2.5rem;display:flex;align-items:baseline;gap:.7rem}
.section-title span{font-size:1rem;color:var(--cyan);font-family:'JetBrains Mono',monospace}
.skills-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1.2rem}
.skill-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.2rem 1.4rem;transition:border-color .3s,transform .3s}
.skill-card:hover{border-color:var(--cyan2);transform:translateY(-3px)}
.skill-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem}
.skill-category{font-weight:700;font-size:.95rem;color:var(--white)}
.skill-pct{font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--cyan)}
.skill-bar{height:4px;background:rgba(255,255,255,.08);border-radius:2px;overflow:hidden;margin-bottom:.8rem}
.skill-fill{height:100%;width:0;background:linear-gradient(90deg,var(--cyan3),var(--cyan));
  border-radius:2px;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.skill-tags{display:flex;flex-wrap:wrap;gap:.4rem}
.tag{padding:.2rem .6rem;background:rgba(0,212,255,.1);border:1px solid rgba(0,212,255,.2);
  border-radius:4px;font-size:.75rem;color:var(--cyan);white-space:nowrap}
.certs-list{display:flex;flex-direction:column;gap:.7rem}
.cert-item{display:flex;align-items:center;gap:1rem;padding:.8rem 1.2rem;
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);flex-wrap:wrap}
.cert-item.top{border-color:rgba(255,215,0,.3)}
.cert-date{font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--gray);min-width:70px}
.cert-name{flex:1;font-size:.95rem}
.top-badge{font-size:.7rem;padding:.15rem .5rem;background:rgba(255,215,0,.12);
  border:1px solid rgba(255,215,0,.3);color:gold;border-radius:4px}
.timeline{position:relative;padding-left:2rem}
.timeline::before{content:'';position:absolute;left:0;top:0;bottom:0;width:2px;
  background:linear-gradient(180deg,var(--cyan) 0%,transparent 100%)}
.timeline-item{position:relative;margin-bottom:2.5rem;padding-left:1.5rem}
.tl-dot{position:absolute;left:-2.35rem;top:.35rem;width:12px;height:12px;border-radius:50%;
  background:var(--cyan);box-shadow:0 0 8px var(--cyan)}
.tl-period{font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--cyan);margin-bottom:.2rem}
.tl-company{font-size:1.2rem;font-weight:700;margin-bottom:.15rem}
.tl-role{font-size:.9rem;color:var(--gray);margin-bottom:.7rem}
.tl-bullets{list-style:none;display:flex;flex-direction:column;gap:.3rem;margin-bottom:.8rem}
.tl-bullets li::before{content:'▸ ';color:var(--cyan);font-size:.8em}
.tl-bullets li{font-size:.9rem;color:var(--gray)}
.tl-tags{display:flex;flex-wrap:wrap;gap:.4rem}
.tag-sm{font-size:.7rem;padding:.15rem .5rem}
.profile-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:2rem}
.profile-table{width:100%;border-collapse:collapse;margin-bottom:1.5rem}
.profile-table th,.profile-table td{padding:.6rem .8rem}
.profile-table th{text-align:left;color:var(--cyan);font-size:.85rem;width:120px;font-weight:400;white-space:nowrap}
.profile-table td{font-size:.95rem}
.profile-table tr:not(:last-child) td,.profile-table tr:not(:last-child) th{border-bottom:1px solid var(--border)}
.pr-box h3{font-size:.85rem;color:var(--cyan);margin-bottom:.5rem;font-weight:400}
.pr-box p{font-size:.95rem;color:var(--gray)}
.footer{text-align:center;padding:2rem;background:#050a18;color:var(--gray);font-size:.8rem}
.accent{color:var(--cyan)}
.hero-photo{width:120px;height:120px;border-radius:50%;margin:0 auto 1.5rem;overflow:hidden;
  border:2px solid var(--cyan3);box-shadow:0 0 20px rgba(0,212,255,.25);
  display:flex;align-items:center;justify-content:center;background:var(--navy3)}
.hero-photo-img{width:100%;height:100%;object-fit:cover;display:block}
.hero-photo-initial{font-family:'Bebas Neue',cursive;font-size:3rem;color:var(--cyan)}
.fade-in{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}
.fade-in.visible{opacity:1;transform:none}
.empty{color:var(--gray);font-size:.9rem}
@media print{body{background:#fff;color:#111}.hero{min-height:auto;page-break-after:always}
  .hero-bg,.hero-bg::after{display:none}.hero-name{-webkit-text-fill-color:#111}
  .section,.section-alt{background:#fff;padding:1.5rem 0}
  .skill-fill{background:#333!important}.fade-in{opacity:1!important;transform:none!important}}
@media(max-width:600px){.skills-grid{grid-template-columns:1fr}.section-title{font-size:2rem}
  .hero-name{font-size:3rem}.timeline{padding-left:1.2rem}}
"""


def _gen_dark_tech(data: dict, photo_b64: str | None = None) -> str:
    profile   = data.get('profile', {})
    summary   = _e(data.get('summary', ''))
    skills    = data.get('skills', [])
    certs     = data.get('certifications', [])
    career    = data.get('career', [])
    meta      = data.get('meta', {})
    name_raw  = profile.get('name', '')
    name      = _e(name_raw)
    kana      = _e(profile.get('kana', ''))
    dob       = _e(profile.get('dob', ''))
    location  = _e(profile.get('location', ''))
    tel       = _e(profile.get('tel', ''))
    job_type  = _e(meta.get('job_type', 'エンジニア'))
    exp_years = meta.get('experience_years', 0)
    photo_html = _build_photo(name_raw, photo_b64)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — ポートフォリオ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+JP:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>{_CSS_DARK_TECH}</style>
</head>
<body>
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-content fade-in">
    {photo_html}
    <p class="hero-kana">{kana}</p>
    <h1 class="hero-name">{name}</h1>
    <p class="hero-badge">{job_type} / 経験 {exp_years}年</p>
    <p class="hero-summary">{summary.replace(chr(10),'<br>')}</p>
    <div class="hero-meta">
      {"<span>📍 " + location + "</span>" if location else ""}
      {"<span>📞 " + tel + "</span>" if tel else ""}
    </div>
  </div>
</section>
<section class="section" id="skills"><div class="container">
  <h2 class="section-title fade-in"><span>01</span>SKILLS</h2>
  <div class="skills-grid fade-in">{_build_skills(skills)}</div>
</div></section>
<section class="section section-alt" id="certs"><div class="container">
  <h2 class="section-title fade-in"><span>02</span>CERTIFICATIONS</h2>
  <div class="certs-list fade-in">{_build_certs(certs)}</div>
</div></section>
<section class="section" id="career"><div class="container">
  <h2 class="section-title fade-in"><span>03</span>CAREER</h2>
  <div class="timeline fade-in">{_build_career(career)}</div>
</div></section>
<section class="section section-alt" id="profile"><div class="container">
  <h2 class="section-title fade-in"><span>04</span>PROFILE</h2>
  <div class="profile-card fade-in">{_profile_table(profile)}</div>
</div></section>
<footer class="footer"><p>Generated by <span class="accent">Resume AI</span></p></footer>
<script>{_JS_COMMON}</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 2. BUSINESS CLEAN  ── 営業 / 企画 / マーケ  （白 × ネイビー）
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_BUSINESS_CLEAN = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#ffffff;--bg2:#f4f7fb;--navy:#1e3a6e;--blue:#2563eb;
  --text:#1a1a2e;--gray:#64748b;--border:#e2e8f0;--card:#ffffff;
  --radius:8px;--shadow:0 1px 4px rgba(0,0,0,.08);
}
html{scroll-behavior:smooth}
body{font-family:'Noto Sans JP',sans-serif;background:var(--bg);color:var(--text);line-height:1.75}
.accent-top{height:5px;background:linear-gradient(90deg,var(--navy),var(--blue))}
.hero{background:var(--bg2);padding:4rem 2rem 3.5rem;border-bottom:1px solid var(--border)}
.hero-inner{max-width:920px;margin:0 auto;display:grid;grid-template-columns:auto auto 1fr;gap:2rem;align-items:center}
.hero-name{font-size:clamp(2rem,5vw,3.4rem);font-weight:700;color:var(--navy);line-height:1.15;margin-bottom:.4rem}
.hero-kana{font-size:.8rem;color:var(--gray);letter-spacing:.1em;margin-bottom:.7rem}
.hero-badge{display:inline-block;padding:.35rem 1rem;background:var(--navy);color:#fff;font-size:.75rem;border-radius:4px;letter-spacing:.05em}
.hero-exp{font-family:'JetBrains Mono',monospace;font-size:.76rem;color:var(--blue);letter-spacing:.12em;margin-bottom:.5rem}
.hero-summary{font-size:.95rem;color:var(--text);line-height:1.9;margin-bottom:1rem}
.hero-meta{display:flex;gap:1.5rem;flex-wrap:wrap;font-size:.82rem;color:var(--gray)}
.section{padding:4.5rem 2rem}
.section-alt{background:var(--bg2)}
.container{max-width:920px;margin:0 auto}
.section-title{font-size:1.45rem;font-weight:700;color:var(--navy);margin-bottom:2rem;
  padding-left:.9rem;border-left:4px solid var(--blue);display:flex;align-items:center;gap:.7rem}
.section-title span{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--blue);font-weight:400}
.skills-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}
.skill-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.2rem 1.4rem;box-shadow:var(--shadow);transition:box-shadow .2s,transform .2s}
.skill-card:hover{box-shadow:0 4px 14px rgba(37,99,235,.1);transform:translateY(-2px)}
.skill-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem}
.skill-category{font-weight:700;font-size:.9rem;color:var(--navy)}
.skill-pct{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--blue)}
.skill-bar{height:3px;background:var(--border);border-radius:2px;overflow:hidden;margin-bottom:.8rem}
.skill-fill{height:100%;width:0;background:linear-gradient(90deg,var(--navy),var(--blue));
  border-radius:2px;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.skill-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag{padding:.18rem .55rem;background:rgba(37,99,235,.07);border:1px solid rgba(37,99,235,.18);
  border-radius:4px;font-size:.72rem;color:var(--blue)}
.certs-list{display:flex;flex-direction:column;gap:.6rem}
.cert-item{display:flex;align-items:center;gap:1rem;padding:.75rem 1rem;
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.cert-item.top{border-left:3px solid #f59e0b}
.cert-date{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--gray);min-width:68px}
.cert-name{flex:1;font-size:.92rem}
.top-badge{font-size:.66rem;padding:.12rem .45rem;background:rgba(245,158,11,.1);
  border:1px solid rgba(245,158,11,.3);color:#b45309;border-radius:3px}
.timeline{position:relative;padding-left:2rem}
.timeline::before{content:'';position:absolute;left:0;top:0;bottom:0;width:2px;
  background:linear-gradient(180deg,var(--navy),rgba(37,99,235,.1))}
.timeline-item{position:relative;margin-bottom:2.5rem;padding-left:1.5rem}
.tl-dot{position:absolute;left:-2.35rem;top:.4rem;width:11px;height:11px;border-radius:50%;
  background:var(--blue);border:2px solid var(--bg)}
.tl-period{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--blue);margin-bottom:.2rem}
.tl-company{font-size:1.15rem;font-weight:700;color:var(--navy);margin-bottom:.12rem}
.tl-role{font-size:.88rem;color:var(--gray);margin-bottom:.65rem}
.tl-bullets{list-style:none;display:flex;flex-direction:column;gap:.3rem;margin-bottom:.7rem}
.tl-bullets li{font-size:.88rem;color:var(--text);padding-left:.9rem;position:relative}
.tl-bullets li::before{content:'›';position:absolute;left:0;color:var(--blue);font-weight:700}
.tl-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag-sm{font-size:.7rem;padding:.12rem .48rem}
.profile-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:2rem;box-shadow:var(--shadow)}
.profile-table{width:100%;border-collapse:collapse;margin-bottom:1.4rem}
.profile-table th,.profile-table td{padding:.55rem .8rem}
.profile-table th{text-align:left;color:var(--navy);font-size:.83rem;width:120px;font-weight:700}
.profile-table tr:not(:last-child) td,.profile-table tr:not(:last-child) th{border-bottom:1px solid var(--border)}
.pr-box h3{font-size:.83rem;color:var(--navy);margin-bottom:.4rem;font-weight:700}
.pr-box p{font-size:.92rem;color:var(--gray)}
.footer{text-align:center;padding:2rem;background:var(--navy);color:rgba(255,255,255,.55);font-size:.78rem}
.accent{color:rgba(147,197,253,1)}
.hero-photo{width:110px;height:110px;border-radius:50%;overflow:hidden;flex-shrink:0;
  border:3px solid var(--navy);box-shadow:0 4px 16px rgba(0,0,0,.12);
  display:flex;align-items:center;justify-content:center;background:var(--bg2)}
.hero-photo-img{width:100%;height:100%;object-fit:cover;display:block}
.hero-photo-initial{font-size:2.4rem;font-weight:700;color:var(--navy)}
.fade-in{opacity:0;transform:translateY(20px);transition:opacity .6s ease,transform .6s ease}
.fade-in.visible{opacity:1;transform:none}
.empty{color:var(--gray);font-size:.88rem}
@media print{.accent-top{display:none}body{color:#111;background:#fff}
  .hero{background:#f8faff;border-bottom:2px solid var(--navy);padding:1.5rem 1rem}
  .section-alt{background:#fff}.fade-in{opacity:1!important;transform:none!important}
  .skill-fill{background:var(--navy)!important}}
@media(max-width:700px){.hero-inner{grid-template-columns:1fr}.skills-grid{grid-template-columns:1fr}}
"""


def _gen_business_clean(data: dict, photo_b64: str | None = None) -> str:
    profile   = data.get('profile', {})
    summary   = _e(data.get('summary', ''))
    skills    = data.get('skills', [])
    certs     = data.get('certifications', [])
    career    = data.get('career', [])
    meta      = data.get('meta', {})
    name_raw  = profile.get('name', '')
    name      = _e(name_raw)
    kana      = _e(profile.get('kana', ''))
    location  = _e(profile.get('location', ''))
    tel       = _e(profile.get('tel', ''))
    job_type  = _e(meta.get('job_type', ''))
    exp_years = meta.get('experience_years', 0)
    photo_html = _build_photo(name_raw, photo_b64)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — ポートフォリオ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>{_CSS_BUSINESS_CLEAN}</style>
</head>
<body>
<div class="accent-top"></div>
<section class="hero">
  <div class="hero-inner">
    <div class="fade-in">{photo_html}</div>
    <div class="fade-in">
      <p class="hero-kana">{kana}</p>
      <h1 class="hero-name">{name}</h1>
      <span class="hero-badge">{job_type}</span>
    </div>
    <div class="fade-in">
      <p class="hero-exp">EXPERIENCE {exp_years} YEARS</p>
      <p class="hero-summary">{summary.replace(chr(10),'<br>')}</p>
      <div class="hero-meta">
        {"<span>📍 " + location + "</span>" if location else ""}
        {"<span>📞 " + tel + "</span>" if tel else ""}
      </div>
    </div>
  </div>
</section>
<section class="section" id="skills"><div class="container">
  <h2 class="section-title fade-in"><span>01</span> SKILLS</h2>
  <div class="skills-grid fade-in">{_build_skills(skills)}</div>
</div></section>
<section class="section section-alt" id="certs"><div class="container">
  <h2 class="section-title fade-in"><span>02</span> CERTIFICATIONS</h2>
  <div class="certs-list fade-in">{_build_certs(certs)}</div>
</div></section>
<section class="section" id="career"><div class="container">
  <h2 class="section-title fade-in"><span>03</span> CAREER</h2>
  <div class="timeline fade-in">{_build_career(career)}</div>
</div></section>
<section class="section section-alt" id="profile"><div class="container">
  <h2 class="section-title fade-in"><span>04</span> PROFILE</h2>
  <div class="profile-card fade-in">{_profile_table(profile)}</div>
</div></section>
<footer class="footer"><p>Generated by <span class="accent">Resume AI</span></p></footer>
<script>{_JS_COMMON}</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MINIMAL PRO  ── 事務 / 経理 / コンサル  （オフホワイト × チャコール）
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_MINIMAL_PRO = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f9f9f7;--bg2:#f0f0ed;--ink:#111111;--mid:#555555;
  --light:#999999;--border:#d8d8d5;--radius:4px;
}
html{scroll-behavior:smooth}
body{font-family:'Noto Sans JP',sans-serif;background:var(--bg);color:var(--ink);line-height:1.85}
.hero{padding:6rem 2rem 5rem;text-align:center;border-bottom:1px solid var(--border)}
.hero-kana{font-size:.75rem;letter-spacing:.38em;color:var(--light);margin-bottom:1.2rem}
.hero-name{font-size:clamp(3rem,8vw,5.5rem);font-weight:300;color:var(--ink);line-height:1;
  letter-spacing:-.02em;margin-bottom:1rem}
.hero-divider{width:36px;height:1px;background:var(--ink);margin:.8rem auto 1rem}
.hero-badge{display:inline-block;font-size:.76rem;letter-spacing:.2em;color:var(--mid);margin-bottom:1.6rem}
.hero-summary{max-width:560px;margin:0 auto 1.5rem;font-size:.95rem;color:var(--mid);line-height:1.95;font-weight:300}
.hero-meta{display:flex;gap:2rem;justify-content:center;font-size:.8rem;color:var(--light)}
.section{padding:5rem 2rem}
.section-alt{background:var(--bg2)}
.container{max-width:840px;margin:0 auto}
.section-title{font-size:.7rem;letter-spacing:.32em;color:var(--light);margin-bottom:2.5rem;
  display:flex;align-items:center;gap:1rem}
.section-title::after{content:'';flex:1;height:1px;background:var(--border)}
.section-title span{display:none}
.skills-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1.5rem}
.skill-card{padding:1.4rem 0;border-bottom:1px solid var(--border);background:transparent}
.skill-header{display:flex;justify-content:space-between;margin-bottom:.5rem}
.skill-category{font-size:.88rem;font-weight:700;color:var(--ink)}
.skill-pct{font-size:.76rem;color:var(--light)}
.skill-bar{height:1px;background:var(--border);margin-bottom:.85rem;overflow:visible}
.skill-fill{height:1px;width:0;background:var(--ink);transition:width 1.2s ease}
.skill-tags{display:flex;flex-wrap:wrap;gap:.3rem}
.tag{padding:.14rem .48rem;border:1px solid var(--border);border-radius:2px;font-size:.7rem;color:var(--mid)}
.certs-list{display:flex;flex-direction:column}
.cert-item{display:flex;align-items:baseline;gap:1.5rem;padding:.75rem 0;border-bottom:1px solid var(--border)}
.cert-item.top .cert-name{font-weight:700}
.cert-date{font-size:.76rem;color:var(--light);min-width:65px;flex-shrink:0}
.cert-name{font-size:.9rem;color:var(--ink);flex:1}
.top-badge{font-size:.64rem;color:var(--mid);border:1px solid var(--border);padding:.1rem .4rem;border-radius:2px}
.timeline{display:flex;flex-direction:column}
.timeline-item{display:grid;grid-template-columns:110px 1fr;gap:1.5rem;padding:2.5rem 0;border-bottom:1px solid var(--border)}
.tl-dot{display:none}
.tl-content{}
.tl-period{font-size:.74rem;color:var(--light);line-height:1.5;padding-top:.2rem}
.tl-company{font-size:1.05rem;font-weight:700;color:var(--ink);margin-bottom:.15rem}
.tl-role{font-size:.85rem;color:var(--mid);margin-bottom:.7rem}
.tl-bullets{list-style:none;display:flex;flex-direction:column;gap:.35rem;margin-bottom:.8rem}
.tl-bullets li{font-size:.88rem;color:var(--mid);padding-left:.9rem;position:relative}
.tl-bullets li::before{content:'—';position:absolute;left:0;color:var(--light)}
.tl-tags{display:flex;flex-wrap:wrap;gap:.3rem}
.tag-sm{font-size:.7rem;padding:.12rem .45rem}
.profile-card{padding:0}
.profile-table{width:100%;border-collapse:collapse}
.profile-table th,.profile-table td{padding:.7rem 0;border-bottom:1px solid var(--border)}
.profile-table th{font-size:.78rem;color:var(--light);width:110px;font-weight:400;letter-spacing:.05em}
.profile-table td{font-size:.9rem;color:var(--ink)}
.pr-box{margin-top:2.5rem;padding-top:2.5rem;border-top:1px solid var(--border)}
.pr-box h3{font-size:.7rem;letter-spacing:.22em;color:var(--light);margin-bottom:.8rem}
.pr-box p{font-size:.92rem;color:var(--mid);line-height:1.95}
.footer{text-align:center;padding:3rem 2rem;color:var(--light);font-size:.75rem;border-top:1px solid var(--border)}
.accent{color:var(--ink)}
.hero-photo{width:100px;height:100px;border-radius:50%;margin:0 auto 2rem;overflow:hidden;
  border:1px solid var(--border);display:flex;align-items:center;justify-content:center;background:var(--bg2)}
.hero-photo-img{width:100%;height:100%;object-fit:cover;display:block}
.hero-photo-initial{font-size:2.2rem;font-weight:300;color:var(--ink)}
.fade-in{opacity:0;transform:translateY(16px);transition:opacity .5s ease,transform .5s ease}
.fade-in.visible{opacity:1;transform:none}
.empty{color:var(--light);font-size:.88rem}
@media print{body{background:#fff}.section-alt{background:#fff}.fade-in{opacity:1!important;transform:none!important}}
@media(max-width:600px){.timeline-item{grid-template-columns:1fr}.tl-period{padding:0}.skills-grid{grid-template-columns:1fr}}
"""


def _gen_minimal_pro(data: dict, photo_b64: str | None = None) -> str:
    profile   = data.get('profile', {})
    summary   = _e(data.get('summary', ''))
    skills    = data.get('skills', [])
    certs     = data.get('certifications', [])
    career    = data.get('career', [])
    meta      = data.get('meta', {})
    name_raw  = profile.get('name', '')
    name      = _e(name_raw)
    kana      = _e(profile.get('kana', ''))
    location  = _e(profile.get('location', ''))
    tel       = _e(profile.get('tel', ''))
    job_type  = _e(meta.get('job_type', ''))
    exp_years = meta.get('experience_years', 0)
    photo_html = _build_photo(name_raw, photo_b64)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — ポートフォリオ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap" rel="stylesheet">
<style>{_CSS_MINIMAL_PRO}</style>
</head>
<body>
<section class="hero">
  <div class="container">
    <div class="fade-in">
      {photo_html}
      <p class="hero-kana">{kana}</p>
      <h1 class="hero-name">{name}</h1>
      <div class="hero-divider"></div>
      <p class="hero-badge">{job_type}&nbsp;&nbsp;/&nbsp;&nbsp;経験 {exp_years}年</p>
      <p class="hero-summary">{summary.replace(chr(10),'<br>')}</p>
      <div class="hero-meta">
        {"<span>" + location + "</span>" if location else ""}
        {"<span>" + tel + "</span>" if tel else ""}
      </div>
    </div>
  </div>
</section>
<section class="section" id="skills"><div class="container">
  <h2 class="section-title fade-in">SKILLS <span></span></h2>
  <div class="skills-grid fade-in">{_build_skills(skills)}</div>
</div></section>
<section class="section section-alt" id="certs"><div class="container">
  <h2 class="section-title fade-in">CERTIFICATIONS <span></span></h2>
  <div class="certs-list fade-in">{_build_certs(certs)}</div>
</div></section>
<section class="section" id="career"><div class="container">
  <h2 class="section-title fade-in">CAREER <span></span></h2>
  <div class="timeline fade-in">{_build_career(career)}</div>
</div></section>
<section class="section section-alt" id="profile"><div class="container">
  <h2 class="section-title fade-in">PROFILE <span></span></h2>
  <div class="profile-card fade-in">{_profile_table(profile)}</div>
</div></section>
<footer class="footer"><p>Generated by <span class="accent">Resume AI</span></p></footer>
<script>{_JS_COMMON}</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CREATIVE BOLD  ── デザイン / 広告 / クリエイティブ  （黒 × 紫ピンク）
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_CREATIVE_BOLD = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#060010;--bg2:#0a0018;--purple:#8b5cf6;--pink:#ec4899;--orange:#f59e0b;
  --text:#f0e8ff;--gray:#a78bfa;--dim:#6d5a8a;--border:rgba(139,92,246,.2);--radius:12px;
}
html{scroll-behavior:smooth}
body{font-family:'Noto Sans JP',sans-serif;background:var(--bg);color:var(--text);line-height:1.7}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(139,92,246,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(139,92,246,.03) 1px,transparent 1px);background-size:50px 50px}
.hero{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;
  text-align:center;padding:5rem 2rem;overflow:hidden}
.hero::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 70% 60% at 50% 40%,rgba(139,92,246,.18) 0%,transparent 70%)}
.hero-content{position:relative;z-index:1;max-width:760px}
.hero-kana{font-family:'JetBrains Mono',monospace;font-size:.76rem;letter-spacing:.32em;color:var(--purple);margin-bottom:1rem}
.hero-name{font-family:'Bebas Neue',cursive;font-size:clamp(4rem,12vw,8rem);line-height:.95;letter-spacing:.04em;
  background:linear-gradient(135deg,#c4b5fd 0%,var(--pink) 50%,var(--orange) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:1rem}
.hero-badge{display:inline-block;margin-bottom:1.2rem;padding:.4rem 1.2rem;
  border:1px solid var(--border);border-radius:999px;
  font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--purple);letter-spacing:.1em}
.hero-summary{font-size:.98rem;color:var(--gray);max-width:560px;margin:0 auto 1.5rem;line-height:1.85}
.hero-meta{display:flex;gap:1.5rem;justify-content:center;font-size:.82rem;color:var(--dim)}
.section{padding:5rem 2rem;position:relative;z-index:1}
.section-alt{background:var(--bg2)}
.container{max-width:900px;margin:0 auto}
.section-title{font-family:'Bebas Neue',cursive;font-size:3rem;letter-spacing:.1em;margin-bottom:2.5rem;
  background:linear-gradient(90deg,#c4b5fd,var(--pink));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  display:flex;align-items:baseline;gap:.6rem}
.section-title span{font-family:'JetBrains Mono',monospace;font-size:.85rem;
  color:var(--purple);-webkit-text-fill-color:var(--purple)}
.skills-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1.2rem}
.skill-card{background:rgba(139,92,246,.06);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.3rem;transition:border-color .3s,box-shadow .3s}
.skill-card:hover{border-color:var(--purple);box-shadow:0 0 20px rgba(139,92,246,.15)}
.skill-header{display:flex;justify-content:space-between;margin-bottom:.6rem}
.skill-category{font-weight:700;font-size:.92rem;color:var(--text)}
.skill-pct{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--purple)}
.skill-bar{height:3px;background:rgba(139,92,246,.15);border-radius:2px;overflow:hidden;margin-bottom:.8rem}
.skill-fill{height:100%;width:0;background:linear-gradient(90deg,var(--purple),var(--pink));
  border-radius:2px;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.skill-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag{padding:.18rem .55rem;background:rgba(139,92,246,.12);border:1px solid rgba(139,92,246,.25);
  border-radius:4px;font-size:.72rem;color:#c4b5fd}
.certs-list{display:flex;flex-direction:column;gap:.7rem}
.cert-item{display:flex;align-items:center;gap:1rem;padding:.8rem 1.1rem;
  background:rgba(139,92,246,.06);border:1px solid var(--border);border-radius:var(--radius)}
.cert-item.top{border-color:rgba(236,72,153,.35)}
.cert-date{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--dim);min-width:65px}
.cert-name{flex:1;font-size:.9rem}
.top-badge{font-size:.65rem;padding:.12rem .45rem;background:rgba(236,72,153,.12);
  border:1px solid rgba(236,72,153,.3);color:var(--pink);border-radius:4px}
.timeline{position:relative;padding-left:2rem}
.timeline::before{content:'';position:absolute;left:0;top:0;bottom:0;width:1px;
  background:linear-gradient(180deg,var(--purple),transparent)}
.timeline-item{position:relative;margin-bottom:2.5rem;padding-left:1.5rem}
.tl-dot{position:absolute;left:-2.28rem;top:.4rem;width:10px;height:10px;border-radius:50%;
  background:var(--purple);box-shadow:0 0 8px var(--purple)}
.tl-period{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--purple);margin-bottom:.2rem}
.tl-company{font-size:1.15rem;font-weight:700;margin-bottom:.12rem}
.tl-role{font-size:.88rem;color:var(--gray);margin-bottom:.65rem}
.tl-bullets{list-style:none;display:flex;flex-direction:column;gap:.3rem;margin-bottom:.7rem}
.tl-bullets li{font-size:.88rem;color:var(--gray);padding-left:.8rem;position:relative}
.tl-bullets li::before{content:'▸';position:absolute;left:0;color:var(--purple);font-size:.8em}
.tl-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag-sm{font-size:.7rem;padding:.12rem .48rem}
.profile-card{background:rgba(139,92,246,.06);border:1px solid var(--border);border-radius:var(--radius);padding:2rem}
.profile-table{width:100%;border-collapse:collapse;margin-bottom:1.4rem}
.profile-table th,.profile-table td{padding:.6rem .8rem}
.profile-table th{text-align:left;color:var(--purple);font-size:.82rem;width:120px;font-weight:400}
.profile-table tr:not(:last-child) td,.profile-table tr:not(:last-child) th{border-bottom:1px solid var(--border)}
.pr-box h3{font-size:.82rem;color:var(--purple);margin-bottom:.4rem;font-weight:400}
.pr-box p{font-size:.92rem;color:var(--gray)}
.footer{text-align:center;padding:2rem;background:#030008;color:var(--dim);font-size:.78rem}
.accent{color:var(--pink)}
.hero-photo{width:128px;height:128px;border-radius:50%;margin:0 auto 1.5rem;overflow:hidden;
  border:2px solid var(--purple);box-shadow:0 0 24px rgba(139,92,246,.35);
  display:flex;align-items:center;justify-content:center;background:rgba(139,92,246,.1)}
.hero-photo-img{width:100%;height:100%;object-fit:cover;display:block}
.hero-photo-initial{font-family:'Bebas Neue',cursive;font-size:3rem;color:var(--purple)}
.fade-in{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}
.fade-in.visible{opacity:1;transform:none}
.empty{color:var(--dim);font-size:.88rem}
@media print{body{background:#fff;color:#111}.hero::before{display:none}.section-alt{background:#fff}
  .fade-in{opacity:1!important;transform:none!important}.skill-fill{background:#6d28d9!important}
  .hero-name{-webkit-text-fill-color:#6d28d9}.section-title{-webkit-text-fill-color:#6d28d9}}
@media(max-width:600px){.skills-grid{grid-template-columns:1fr}.hero-name{font-size:4rem}}
"""


def _gen_creative_bold(data: dict, photo_b64: str | None = None) -> str:
    profile   = data.get('profile', {})
    summary   = _e(data.get('summary', ''))
    skills    = data.get('skills', [])
    certs     = data.get('certifications', [])
    career    = data.get('career', [])
    meta      = data.get('meta', {})
    name_raw  = profile.get('name', '')
    name      = _e(name_raw)
    kana      = _e(profile.get('kana', ''))
    location  = _e(profile.get('location', ''))
    tel       = _e(profile.get('tel', ''))
    job_type  = _e(meta.get('job_type', ''))
    exp_years = meta.get('experience_years', 0)
    photo_html = _build_photo(name_raw, photo_b64)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — ポートフォリオ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+JP:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>{_CSS_CREATIVE_BOLD}</style>
</head>
<body>
<section class="hero">
  <div class="hero-content fade-in">
    {photo_html}
    <p class="hero-kana">{kana}</p>
    <h1 class="hero-name">{name}</h1>
    <p class="hero-badge">{job_type} / {exp_years}年のキャリア</p>
    <p class="hero-summary">{summary.replace(chr(10),'<br>')}</p>
    <div class="hero-meta">
      {"<span>📍 " + location + "</span>" if location else ""}
      {"<span>📞 " + tel + "</span>" if tel else ""}
    </div>
  </div>
</section>
<section class="section" id="skills"><div class="container">
  <h2 class="section-title fade-in"><span>01</span> SKILLS</h2>
  <div class="skills-grid fade-in">{_build_skills(skills)}</div>
</div></section>
<section class="section section-alt" id="certs"><div class="container">
  <h2 class="section-title fade-in"><span>02</span> WORKS &amp; CERTS</h2>
  <div class="certs-list fade-in">{_build_certs(certs)}</div>
</div></section>
<section class="section" id="career"><div class="container">
  <h2 class="section-title fade-in"><span>03</span> CAREER</h2>
  <div class="timeline fade-in">{_build_career(career)}</div>
</div></section>
<section class="section section-alt" id="profile"><div class="container">
  <h2 class="section-title fade-in"><span>04</span> PROFILE</h2>
  <div class="profile-card fade-in">{_profile_table(profile)}</div>
</div></section>
<footer class="footer"><p>Generated by <span class="accent">Resume AI</span></p></footer>
<script>{_JS_COMMON}</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MEDICAL CARE  ── 医療 / 福祉 / 介護  （淡いミント × ティール）
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_MEDICAL_CARE = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f0faf8;--bg2:#ffffff;--teal:#0d9488;--teal2:#14b8a6;--dark:#0f3d38;
  --gray:#4d7770;--light:#94b8b4;--border:#b2dbd7;--card:#ffffff;
  --radius:14px;--shadow:0 2px 12px rgba(13,148,136,.1);
}
html{scroll-behavior:smooth}
body{font-family:'Noto Sans JP',sans-serif;background:var(--bg);color:var(--dark);line-height:1.8}
.hero{padding:5rem 2rem 4rem;text-align:center;
  background:linear-gradient(180deg,#dff5f1 0%,var(--bg) 100%);border-bottom:1px solid var(--border)}
.hero-content{max-width:680px;margin:0 auto}
.hero-icon{font-size:2.2rem;margin-bottom:.8rem;line-height:1}
.hero-kana{font-size:.76rem;letter-spacing:.28em;color:var(--light);margin-bottom:.6rem}
.hero-name{font-size:clamp(2.4rem,6vw,4rem);font-weight:700;color:var(--dark);line-height:1.15;margin-bottom:.6rem}
.hero-badge{display:inline-flex;align-items:center;gap:.4rem;padding:.4rem 1.1rem;
  background:var(--teal);color:#fff;border-radius:999px;font-size:.8rem;margin-bottom:1.2rem;letter-spacing:.05em}
.hero-summary{font-size:.95rem;color:var(--gray);line-height:1.9;margin-bottom:1.4rem}
.hero-meta{display:flex;gap:1.5rem;justify-content:center;font-size:.82rem;color:var(--light)}
.section{padding:4.5rem 2rem}
.section-alt{background:var(--bg2)}
.container{max-width:880px;margin:0 auto}
.section-title{font-size:1.3rem;font-weight:700;color:var(--teal);margin-bottom:2rem;
  display:flex;align-items:center;gap:.8rem}
.section-title::before{content:'';width:5px;height:1.3em;background:var(--teal);border-radius:3px;flex-shrink:0}
.section-title span{font-size:.7rem;color:var(--light);letter-spacing:.15em;font-weight:400}
.skills-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem}
.skill-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.3rem;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s}
.skill-card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(13,148,136,.15)}
.skill-header{display:flex;justify-content:space-between;margin-bottom:.6rem}
.skill-category{font-weight:700;font-size:.9rem;color:var(--dark)}
.skill-pct{font-size:.78rem;color:var(--teal)}
.skill-bar{height:4px;background:rgba(13,148,136,.12);border-radius:2px;overflow:hidden;margin-bottom:.8rem}
.skill-fill{height:100%;width:0;background:linear-gradient(90deg,var(--teal),var(--teal2));
  border-radius:2px;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.skill-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag{padding:.2rem .6rem;background:rgba(13,148,136,.08);border:1px solid rgba(13,148,136,.2);
  border-radius:999px;font-size:.72rem;color:var(--teal)}
.certs-list{display:flex;flex-direction:column;gap:.7rem}
.cert-item{display:flex;align-items:center;gap:1rem;padding:.8rem 1.2rem;
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.cert-item.top{border-left:4px solid var(--teal2)}
.cert-date{font-size:.78rem;color:var(--light);min-width:68px;flex-shrink:0}
.cert-name{flex:1;font-size:.9rem}
.top-badge{font-size:.66rem;padding:.12rem .45rem;background:rgba(13,148,136,.1);
  border:1px solid rgba(13,148,136,.25);color:var(--teal);border-radius:999px}
.timeline{position:relative;padding-left:1.8rem}
.timeline::before{content:'';position:absolute;left:0;top:0;bottom:0;width:2px;
  background:linear-gradient(180deg,var(--teal),rgba(13,148,136,.1));border-radius:2px}
.timeline-item{position:relative;margin-bottom:2.2rem;padding-left:1.5rem}
.tl-dot{position:absolute;left:-2.2rem;top:.4rem;width:12px;height:12px;border-radius:50%;
  background:var(--teal);border:2px solid var(--bg);box-shadow:0 0 0 2px rgba(13,148,136,.3)}
.tl-period{font-size:.78rem;color:var(--light);margin-bottom:.2rem}
.tl-company{font-size:1.1rem;font-weight:700;color:var(--dark);margin-bottom:.12rem}
.tl-role{font-size:.88rem;color:var(--gray);margin-bottom:.65rem}
.tl-bullets{list-style:none;display:flex;flex-direction:column;gap:.3rem;margin-bottom:.7rem}
.tl-bullets li{font-size:.88rem;color:var(--gray);padding-left:.8rem;position:relative}
.tl-bullets li::before{content:'✓';position:absolute;left:0;color:var(--teal);font-size:.82em}
.tl-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag-sm{font-size:.7rem;padding:.14rem .5rem;border-radius:999px}
.profile-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:2rem;box-shadow:var(--shadow)}
.profile-table{width:100%;border-collapse:collapse;margin-bottom:1.4rem}
.profile-table th,.profile-table td{padding:.6rem .8rem}
.profile-table th{text-align:left;color:var(--teal);font-size:.83rem;width:120px;font-weight:700}
.profile-table tr:not(:last-child) td,.profile-table tr:not(:last-child) th{border-bottom:1px solid var(--border)}
.pr-box h3{font-size:.83rem;color:var(--teal);margin-bottom:.4rem;font-weight:700}
.pr-box p{font-size:.92rem;color:var(--gray)}
.footer{text-align:center;padding:2rem;background:var(--dark);color:rgba(255,255,255,.5);font-size:.78rem}
.accent{color:var(--teal2)}
.hero-photo{width:120px;height:120px;border-radius:50%;margin:0 auto 1.2rem;overflow:hidden;
  border:3px solid var(--teal);box-shadow:0 0 18px rgba(13,148,136,.25);
  display:flex;align-items:center;justify-content:center;background:var(--bg2)}
.hero-photo-img{width:100%;height:100%;object-fit:cover;display:block}
.hero-photo-initial{font-size:2.8rem;font-weight:700;color:var(--teal)}
.fade-in{opacity:0;transform:translateY(20px);transition:opacity .6s ease,transform .6s ease}
.fade-in.visible{opacity:1;transform:none}
.empty{color:var(--light);font-size:.88rem}
@media print{body{background:#fff}.hero{background:#fff;border-bottom:2px solid var(--teal)}
  .section-alt{background:#fff}.fade-in{opacity:1!important;transform:none!important}}
@media(max-width:600px){.skills-grid{grid-template-columns:1fr}}
"""


def _gen_medical_care(data: dict, photo_b64: str | None = None) -> str:
    profile   = data.get('profile', {})
    summary   = _e(data.get('summary', ''))
    skills    = data.get('skills', [])
    certs     = data.get('certifications', [])
    career    = data.get('career', [])
    meta      = data.get('meta', {})
    name_raw  = profile.get('name', '')
    name      = _e(name_raw)
    kana      = _e(profile.get('kana', ''))
    location  = _e(profile.get('location', ''))
    tel       = _e(profile.get('tel', ''))
    job_type  = _e(meta.get('job_type', ''))
    exp_years = meta.get('experience_years', 0)
    photo_html = _build_photo(name_raw, photo_b64)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — ポートフォリオ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap" rel="stylesheet">
<style>{_CSS_MEDICAL_CARE}</style>
</head>
<body>
<section class="hero">
  <div class="hero-content fade-in">
    {photo_html}
    <p class="hero-kana">{kana}</p>
    <h1 class="hero-name">{name}</h1>
    <p class="hero-badge">🩺 {job_type} / 経験 {exp_years}年</p>
    <p class="hero-summary">{summary.replace(chr(10),'<br>')}</p>
    <div class="hero-meta">
      {"<span>📍 " + location + "</span>" if location else ""}
      {"<span>📞 " + tel + "</span>" if tel else ""}
    </div>
  </div>
</section>
<section class="section" id="skills"><div class="container">
  <h2 class="section-title fade-in"><span>01</span> スキル・専門領域</h2>
  <div class="skills-grid fade-in">{_build_skills(skills)}</div>
</div></section>
<section class="section section-alt" id="certs"><div class="container">
  <h2 class="section-title fade-in"><span>02</span> 資格・認定</h2>
  <div class="certs-list fade-in">{_build_certs(certs)}</div>
</div></section>
<section class="section" id="career"><div class="container">
  <h2 class="section-title fade-in"><span>03</span> 職歴</h2>
  <div class="timeline fade-in">{_build_career(career)}</div>
</div></section>
<section class="section section-alt" id="profile"><div class="container">
  <h2 class="section-title fade-in"><span>04</span> プロフィール</h2>
  <div class="profile-card fade-in">{_profile_table(profile)}</div>
</div></section>
<footer class="footer"><p>Generated by <span class="accent">Resume AI</span></p></footer>
<script>{_JS_COMMON}</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ACADEMIC  ── 教育 / 研究 / 公務員  （クリーム × バーガンディ）
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_ACADEMIC = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#faf7f0;--bg2:#f3ede0;--burgundy:#6b2737;--gold:#c9a84c;--dark:#2d1f1a;
  --gray:#6b5a52;--light:#a8928a;--border:#d4c4b0;--card:#fffdf8;--radius:6px;
}
html{scroll-behavior:smooth}
body{font-family:'Noto Sans JP',sans-serif;background:var(--bg);color:var(--dark);line-height:1.85}
.deco-top{height:5px;background:var(--burgundy)}
.deco-gold{height:2px;background:var(--gold)}
.hero{padding:4.5rem 2rem 4rem;text-align:center;border-bottom:2px solid var(--border);background:var(--bg)}
.hero-content{max-width:680px;margin:0 auto}
.hero-crest{font-size:1.6rem;color:var(--burgundy);margin-bottom:1rem}
.hero-kana{font-size:.76rem;letter-spacing:.32em;color:var(--light);margin-bottom:.5rem}
.hero-name{font-family:'Lora',serif;font-size:clamp(2.5rem,6vw,4.2rem);font-weight:700;
  color:var(--burgundy);line-height:1.15;margin-bottom:.6rem}
.hero-divider{width:60px;height:2px;background:var(--gold);margin:.8rem auto 1rem}
.hero-badge{display:inline-block;font-size:.8rem;letter-spacing:.12em;color:var(--gray);
  border:1px solid var(--gold);padding:.35rem 1.1rem;border-radius:3px;margin-bottom:1.4rem}
.hero-summary{font-size:.95rem;color:var(--gray);line-height:1.95;margin-bottom:1.4rem}
.hero-meta{display:flex;gap:2rem;justify-content:center;font-size:.82rem;color:var(--light)}
.section{padding:4.5rem 2rem}
.section-alt{background:var(--bg2)}
.container{max-width:860px;margin:0 auto}
.section-title{font-family:'Lora',serif;font-size:1.5rem;font-weight:700;color:var(--burgundy);
  margin-bottom:2rem;display:flex;align-items:baseline;gap:.8rem;
  padding-bottom:.6rem;border-bottom:2px solid var(--gold)}
.section-title span{font-size:.72rem;color:var(--gold);letter-spacing:.15em;font-family:'Noto Sans JP',sans-serif;font-weight:400}
.skills-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1.2rem}
.skill-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.3rem;border-left:3px solid var(--gold)}
.skill-header{display:flex;justify-content:space-between;margin-bottom:.6rem}
.skill-category{font-weight:700;font-size:.9rem;color:var(--dark)}
.skill-pct{font-size:.78rem;color:var(--gold)}
.skill-bar{height:3px;background:var(--border);border-radius:2px;overflow:hidden;margin-bottom:.8rem}
.skill-fill{height:100%;width:0;background:linear-gradient(90deg,var(--burgundy),var(--gold));
  border-radius:2px;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.skill-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag{padding:.18rem .55rem;background:rgba(107,39,55,.06);border:1px solid rgba(107,39,55,.15);
  border-radius:3px;font-size:.72rem;color:var(--burgundy)}
.certs-list{display:flex;flex-direction:column;gap:.6rem}
.cert-item{display:flex;align-items:center;gap:1.2rem;padding:.8rem 1.1rem;
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius)}
.cert-item.top{border-color:var(--gold)}
.cert-date{font-size:.78rem;color:var(--light);min-width:68px;flex-shrink:0}
.cert-name{flex:1;font-size:.9rem}
.top-badge{font-size:.66rem;padding:.12rem .45rem;background:rgba(201,168,76,.12);
  border:1px solid rgba(201,168,76,.4);color:#8a6e1e;border-radius:3px}
.timeline{position:relative;padding-left:2rem;border-left:2px solid var(--border)}
.timeline-item{position:relative;margin-bottom:2.5rem;padding-left:1.5rem}
.tl-dot{position:absolute;left:-2.4rem;top:.4rem;width:10px;height:10px;border-radius:50%;
  background:var(--gold);border:2px solid var(--bg)}
.tl-period{font-size:.78rem;color:var(--light);margin-bottom:.2rem}
.tl-company{font-family:'Lora',serif;font-size:1.1rem;font-weight:700;color:var(--burgundy);margin-bottom:.12rem}
.tl-role{font-size:.88rem;color:var(--gray);margin-bottom:.65rem}
.tl-bullets{list-style:disc;padding-left:1.1rem;display:flex;flex-direction:column;gap:.3rem;margin-bottom:.7rem}
.tl-bullets li{font-size:.88rem;color:var(--gray)}
.tl-tags{display:flex;flex-wrap:wrap;gap:.35rem}
.tag-sm{font-size:.7rem;padding:.12rem .45rem}
.profile-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:2rem}
.profile-table{width:100%;border-collapse:collapse;margin-bottom:1.4rem}
.profile-table th,.profile-table td{padding:.6rem .8rem}
.profile-table th{text-align:left;color:var(--burgundy);font-size:.83rem;width:120px;font-weight:700}
.profile-table tr:not(:last-child) td,.profile-table tr:not(:last-child) th{border-bottom:1px solid var(--border)}
.pr-box h3{font-family:'Lora',serif;font-size:.88rem;color:var(--burgundy);margin-bottom:.5rem;font-weight:700}
.pr-box p{font-size:.92rem;color:var(--gray)}
.footer{text-align:center;padding:2rem;background:var(--dark);color:var(--light);font-size:.78rem;border-top:3px solid var(--burgundy)}
.accent{color:var(--gold)}
.hero-photo{width:120px;height:120px;border-radius:50%;margin:0 auto 1.2rem;overflow:hidden;
  border:2px solid var(--gold);box-shadow:0 4px 16px rgba(107,39,55,.15);
  display:flex;align-items:center;justify-content:center;background:var(--bg2)}
.hero-photo-img{width:100%;height:100%;object-fit:cover;display:block}
.hero-photo-initial{font-size:2.8rem;font-weight:700;color:var(--burgundy)}
.fade-in{opacity:0;transform:translateY(20px);transition:opacity .6s ease,transform .6s ease}
.fade-in.visible{opacity:1;transform:none}
.empty{color:var(--light);font-size:.88rem}
@media print{body{background:#fff}.section-alt{background:#fff}.deco-top,.deco-gold{display:none}
  .fade-in{opacity:1!important;transform:none!important}}
@media(max-width:600px){.skills-grid{grid-template-columns:1fr}.hero-name{font-size:2.5rem}}
"""


def _gen_academic(data: dict, photo_b64: str | None = None) -> str:
    profile   = data.get('profile', {})
    summary   = _e(data.get('summary', ''))
    skills    = data.get('skills', [])
    certs     = data.get('certifications', [])
    career    = data.get('career', [])
    meta      = data.get('meta', {})
    name_raw  = profile.get('name', '')
    name      = _e(name_raw)
    kana      = _e(profile.get('kana', ''))
    location  = _e(profile.get('location', ''))
    tel       = _e(profile.get('tel', ''))
    job_type  = _e(meta.get('job_type', ''))
    exp_years = meta.get('experience_years', 0)
    photo_html = _build_photo(name_raw, photo_b64)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — ポートフォリオ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;700&family=Noto+Sans+JP:wght@300;400;700&display=swap" rel="stylesheet">
<style>{_CSS_ACADEMIC}</style>
</head>
<body>
<div class="deco-top"></div>
<div class="deco-gold"></div>
<section class="hero">
  <div class="hero-content fade-in">
    {photo_html}
    <div class="hero-crest">⚜</div>
    <p class="hero-kana">{kana}</p>
    <h1 class="hero-name">{name}</h1>
    <div class="hero-divider"></div>
    <p class="hero-badge">{job_type} / 経験 {exp_years}年</p>
    <p class="hero-summary">{summary.replace(chr(10),'<br>')}</p>
    <div class="hero-meta">
      {"<span>📍 " + location + "</span>" if location else ""}
      {"<span>📞 " + tel + "</span>" if tel else ""}
    </div>
  </div>
</section>
<section class="section" id="skills"><div class="container">
  <h2 class="section-title fade-in">専門スキル <span>SKILLS</span></h2>
  <div class="skills-grid fade-in">{_build_skills(skills)}</div>
</div></section>
<section class="section section-alt" id="certs"><div class="container">
  <h2 class="section-title fade-in">資格・免許 <span>CERTIFICATIONS</span></h2>
  <div class="certs-list fade-in">{_build_certs(certs)}</div>
</div></section>
<section class="section" id="career"><div class="container">
  <h2 class="section-title fade-in">職歴 <span>CAREER</span></h2>
  <div class="timeline fade-in">{_build_career(career)}</div>
</div></section>
<section class="section section-alt" id="profile"><div class="container">
  <h2 class="section-title fade-in">プロフィール <span>PROFILE</span></h2>
  <div class="profile-card fade-in">{_profile_table(profile)}</div>
</div></section>
<footer class="footer"><p>Generated by <span class="accent">Resume AI</span></p></footer>
<script>{_JS_COMMON}</script>
</body></html>"""
