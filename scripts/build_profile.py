#!/usr/bin/env python3
"""Build the mission-control SVG panels for the dpkrobomad profile README.

    python3 scripts/build_profile.py            # rebuild every panel
    python3 scripts/build_profile.py --activity # only the live activity panel (CI)

Live data (contribution calendar + language bytes) comes from the GitHub GraphQL
API using $GITHUB_TOKEN, or `gh auth token` when run locally. Standard library only.
"""
import base64, datetime as dt, json, math, os, subprocess, sys, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
USER = "dpkrobomad"
W = 1000

# palette
BG, PANEL, LINE, LINE2 = "#040906", "#07110b", "#16472a", "#1f6b3b"
G, G2, GD = "#3dff7a", "#27c95c", "#0e3a1e"
TXT, MUT = "#e8f5ec", "#8aa596"


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


FONTS = f"""@font-face{{font-family:'CP';src:url(data:font/woff2;base64,{b64(A/'fonts/chakra-600.woff2')}) format('woff2');font-weight:600}}
@font-face{{font-family:'JBM';src:url(data:font/woff2;base64,{b64(A/'fonts/jbmono-500.woff2')}) format('woff2');font-weight:500}}
.h{{font-family:'CP','Chakra Petch','Segoe UI',sans-serif;font-weight:600;fill:{TXT}}}
.m{{font-family:'JBM','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-weight:500;fill:{MUT}}}
.g{{fill:{G}}} .t{{fill:{TXT}}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
.blink{{animation:blink 1.6s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
.float{{animation:float 6s ease-in-out infinite}}
@keyframes dash{{to{{stroke-dashoffset:-200}}}}
.flow{{animation:dash 9s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}"""

DEFS = f"""<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="{G}" opacity=".07"/></pattern>
<linearGradient id="cardg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1a10"/><stop offset="1" stop-color="#050c08"/></linearGradient>"""


def svg(h, body, title, extra_defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>{FONTS}</style>
<defs>{DEFS}{extra_defs}</defs>
<rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="10" fill="{BG}" stroke="{LINE}"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="10" fill="url(#dots)"/>
{body}
</svg>"""


def t(x, y, s, cls="m", size=12, extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" {extra}>{escape(s)}</text>'


def chamfer(x, y, w, h, c=14, fill="url(#cardg)", stroke=LINE2, sw=1.2):
    """Card with top-right + bottom-left chamfers and bright corner ticks."""
    d = f"M{x},{y} H{x+w-c} L{x+w},{y+c} V{y+h} H{x+c} L{x},{y+h-c} Z"
    ticks = (f'<path d="M{x},{y+18} V{y} H{x+18}" fill="none" stroke="{G}" stroke-width="1.6"/>'
             f'<path d="M{x+w-c-10},{y} H{x+w-c} L{x+w},{y+c} V{y+c+10}" fill="none" stroke="{G}" stroke-width="1.6"/>'
             f'<path d="M{x+w},{y+h-18} V{y+h} H{x+w-18}" fill="none" stroke="{G}" stroke-width="1.6"/>')
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>{ticks}'


def brackets(w, h, m=14, L=22):
    s = f'stroke="{G}" stroke-width="2" fill="none"'
    return (f'<path d="M{m},{m+L} V{m} H{m+L}" {s}/><path d="M{w-m-L},{m} H{w-m} V{m+L}" {s}/>'
            f'<path d="M{m},{h-m-L} V{h-m} H{m+L}" {s}/><path d="M{w-m-L},{h-m} H{w-m} V{h-m-L}" {s}/>')


def heading(kicker, title, tags, y=34):
    return (f'<path d="M28,{y-10} l6,-10 h5 l-6,10z M38,{y-10} l6,-10 h5 l-6,10z" fill="{G}"/>'
            + t(56, y - 11, kicker, "m g", 13, 'letter-spacing="2.5"')
            + t(28, y + 22, title, "h", 30, 'letter-spacing="3"')
            + t(W - 28, y - 11, f"[ {tags} ]", "m", 11.5, 'text-anchor="end" letter-spacing="1.5"')
            + f'<line x1="28" y1="{y-30}" x2="{W-28}" y2="{y-30}" stroke="{LINE}" />')


# ---------------------------------------------------------------- icons
ICONS = json.loads((A / "src/icons.json").read_text())
HEX_OVERRIDE = {"django": "44B78B", "amazonwebservices": "FF9900", "apachekafka": "E8F5EC", "github": "E8F5EC"}


def brand(slug, x, y, s):
    if slug == "azure":
        k = s / 24
        return (f'<g transform="translate({x},{y}) scale({k})"><path d="M9.1 1.5h6.2L8.9 20.6c-.1.4-.5.6-.9.6H3.3c-.6 0-1.1-.6-.9-1.2z" fill="#0A7CD4"/>'
                f'<path d="M17.9 14.8H8.3l5.9 6.5h7c.6 0 1-.6.8-1.2L15.3 1.5c-.1-.4-.5-.6-.9-.6h-1.2l4.7 13.9z" fill="#3CCBF4"/></g>')
    i = ICONS[slug]
    col = "#" + HEX_OVERRIDE.get(slug, i["hex"])
    return f'<g transform="translate({x},{y}) scale({s/24})"><path d="{i["path"]}" fill="{col}"/></g>'


def line_icon(kind, x, y, s=34):
    st = f'fill="none" stroke="{G}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    k = s / 24
    p = {
        "code": '<path d="M8 6 2 12l6 6M16 6l6 6-6 6M14 4l-4 16"/>',
        "cloud": '<path d="M7 18h10.5a4.5 4.5 0 0 0 .6-9 6 6 0 0 0-11.4 1.6A3.8 3.8 0 0 0 7 18z"/>',
        "sat": '<path d="m13 7 4 4-6 6-4-4z"/><path d="m10 4 3 3M17 11l3 3M7 13l-3 3 4 4 3-3M14 4l2-2 6 6-2 2M4 14l-2 2"/><path d="M16 18a4 4 0 0 0 2-2M18 21a7 7 0 0 0 3-3"/>',
        "chip": '<rect x="6" y="6" width="12" height="12" rx="1"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
        "radio": '<circle cx="12" cy="12" r="2"/><path d="M8 8a5.6 5.6 0 0 0 0 8M16 8a5.6 5.6 0 0 1 0 8M5 5a10 10 0 0 0 0 14M19 5a10 10 0 0 1 0 14"/>',
        "rocket": '<path d="M5 19c0-2 1-4 3-4s2 2 0 3-3 1-3 1z"/><path d="M9 15 6 12l3-1c2-5 6-8 11-8 0 5-3 9-8 11l-1 3z"/><circle cx="15" cy="9" r="1.6"/>',
        "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
        "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    }[kind]
    return f'<g transform="translate({x},{y}) scale({k})" {st}>{p}</g>'


# ---------------------------------------------------------------- panels
def hero():
    h = 400
    por = b64(A / "src/portrait.jpg")
    # earth: big circle bottom-right with graticule
    ex, ey, er = 905, 700, 430
    grat = "".join(
        f'<ellipse cx="{ex}" cy="{ey}" rx="{er*abs(math.cos(math.radians(a)))}" ry="{er}" fill="none" stroke="{G}" stroke-opacity=".10"/>'
        for a in (15, 40, 65, 82))
    grat += "".join(
        f'<line x1="{ex-er*math.cos(math.asin(d/er))}" y1="{ey-d}" x2="{ex+er*math.cos(math.asin(d/er))}" y2="{ey-d}" stroke="{G}" stroke-opacity=".10"/>'
        for d in (120, 220, 310, 380))
    # satellite: body + two panels, isometric-ish
    def panel(px, flip):
        cells = "".join(
            f'<line x1="{px+i*22}" y1="0" x2="{px+i*22}" y2="44" stroke="{G}" stroke-opacity=".55" stroke-width=".8"/>'
            for i in range(1, 6))
        return (f'<rect x="{px}" y="0" width="132" height="44" fill="#0b2a17" stroke="{G}" stroke-width="1.4"/>{cells}'
                f'<line x1="{px}" y1="22" x2="{px+132}" y2="22" stroke="{G}" stroke-opacity=".55" stroke-width=".8"/>')
    sat = f"""<g transform="translate(838 150) rotate(-22) scale(.78)"><g class="float">
  <g transform="translate(-210 -22)">{panel(0,0)}</g>
  <line x1="-78" y1="0" x2="-34" y2="0" stroke="{G}" stroke-width="2"/>
  <line x1="34" y1="0" x2="78" y2="0" stroke="{G}" stroke-width="2"/>
  <g transform="translate(78 -22)">{panel(0,1)}</g>
  <path d="M-34,-34 L4,-46 L34,-34 L34,34 L-4,46 L-34,34 Z" fill="#0c2414" stroke="{G}" stroke-width="1.6"/>
  <path d="M-34,-34 L-4,-22 L34,-34 M-4,-22 V46" fill="none" stroke="{G}" stroke-width="1.1" stroke-opacity=".8"/>
  <rect x="-26" y="-14" width="16" height="24" fill="none" stroke="{G}" stroke-opacity=".6"/>
  <rect x="6" y="-14" width="20" height="10" fill="none" stroke="{G}" stroke-opacity=".6"/>
  <line x1="4" y1="-46" x2="4" y2="-72" stroke="{G}" stroke-width="1.4"/><circle cx="4" cy="-74" r="3" class="g blink"/>
</g></g>"""
    body = f"""
<defs><radialGradient id="eg" cx=".5" cy=".5" r=".5"><stop offset=".86" stop-color="#06180d"/><stop offset=".985" stop-color="#0f4a23"/><stop offset="1" stop-color="{G}" stop-opacity=".9"/></radialGradient>
<radialGradient id="haze" cx=".85" cy=".95" r=".7"><stop offset="0" stop-color="{G}" stop-opacity=".22"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></radialGradient>
<clipPath id="pc"><circle cx="128" cy="170" r="92"/></clipPath><clipPath id="frame"><rect x="1" y="1" width="{W-2}" height="{h-2}" rx="10"/></clipPath></defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{h}" fill="url(#haze)"/>
<circle cx="{ex}" cy="{ey}" r="{er}" fill="url(#eg)"/>{grat}
<circle cx="{ex}" cy="{ey}" r="{er+10}" fill="none" stroke="{G}" stroke-opacity=".18" stroke-width="6"/>
<ellipse cx="830" cy="190" rx="170" ry="92" transform="rotate(-18 830 190)" fill="none" stroke="{G}" stroke-opacity=".35" stroke-dasharray="3 7" class="flow"/>
<circle cx="838" cy="160" r="120" fill="none" stroke="{G}" stroke-opacity=".08"/>
{sat}
</g>
{brackets(W, h)}
<text x="{W-36}" y="44" class="m" font-size="10.5" text-anchor="end" letter-spacing="1">ORBITAL VIEW  //  CUBESAT</text>
<text x="{W-120}" y="62" class="m g" font-size="10" letter-spacing="1">MODE : TELEMETRY</text>
<text x="{W-120}" y="76" class="m g" font-size="10" letter-spacing="1">LINK : <tspan class="blink">ONLINE</tspan></text>
<text x="{W-120}" y="90" class="m g" font-size="10" letter-spacing="1">SNR  : NOMINAL</text>
<!-- portrait -->
<circle cx="128" cy="170" r="104" fill="none" stroke="{LINE2}" stroke-width="1"/>
<g style="transform-origin:128px 170px;animation:spin 24s linear infinite"><circle cx="128" cy="170" r="104" fill="none" stroke="{G}" stroke-width="2.5" stroke-dasharray="120 533" stroke-linecap="round"/></g>
<image href="data:image/jpeg;base64,{por}" x="36" y="78" width="184" height="184" clip-path="url(#pc)" preserveAspectRatio="xMidYMid slice"/>
<circle cx="128" cy="170" r="92" fill="none" stroke="{G}" stroke-opacity=".7" stroke-width="2"/>
<circle cx="128" cy="170" r="92" fill="{G}" fill-opacity=".06"/>
<path d="M30 330 l8 -14 h6 l-8 14z M44 330 l8 -14 h6 l-8 14z M58 330 l8 -14 h6 l-8 14z" fill="{G}"/>
<!-- identity -->
{t(258, 82, "DEEPAK", "h", 38, 'letter-spacing="3"')}
{t(258, 124, "RADHAKRISHNAN", "h", 38, 'letter-spacing="3"')}
{t(260, 152, "@dpkrobomad", "m g", 19)}
<rect x="260" y="168" width="140" height="26" rx="3" fill="#0a1f12" stroke="{G2}"/>
<circle cx="276" cy="181" r="5" class="g blink"/>{t(288, 185.5, "SYSTEM ONLINE", "m g", 11.5, 'letter-spacing="1"')}
{line_icon("pin", 418, 171, 18)}{t(442, 185.5, "Cardiff, Wales", "m t", 12.5)}
<path d="M262 238 l8 -18 h5 l-8 18z" fill="{G}"/>
{t(286, 238, "ARCHITECTING SYSTEMS", "h g", 27, 'letter-spacing="2.5"')}
{t(286, 270, "BEYOND THE ORDINARY", "h g", 27, 'letter-spacing="2.5"')}
{t(286, 302, "Solution Architect / AI Systems Engineer / Researcher", "m t", 13)}
{t(286, 336, "> building telemetry, AI and cloud systems that survive the real world_", "m", 11.5)}
"""
    return svg(h, body, "Deepak Radhakrishnan — Architecting systems beyond the ordinary")


def button(label, icon, w=230, primary=True):
    h = 46
    fill = G if primary else BG
    col = BG if primary else G
    ic = {
        "gh": f'<g transform="translate(22 13) scale(.83)"><path d="{ICONS["github"]["path"]}" fill="{col}"/></g>',
        "link": f'<g transform="translate(22 13) scale(.83)" fill="none" stroke="{col}" stroke-width="2.2" stroke-linecap="round"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></g>',
        "globe": f'<g transform="translate(22 13) scale(.83)" fill="none" stroke="{col}" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></g>',
    }[icon]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(label)}">
<title>{escape(label)}</title><style>{FONTS}</style>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="4" fill="{fill}" stroke="{G}" stroke-width="1.5"/>
{ic}<text x="{(w+30)/2}" y="28.5" class="m" font-size="13.5" text-anchor="middle" letter-spacing="1.5" style="fill:{col}">{escape(label)}</text>
<text x="{w-22}" y="28.5" class="m" font-size="14" text-anchor="middle" style="fill:{col}">→</text></svg>"""


def telemetry():
    h = 46
    items = [("TELEMETRY", None), ("SYS", "ONLINE"), ("CLOUD", "CONNECTED"), ("STREAM", "ACTIVE"), ("AI", "READY")]
    x, out = 62, []
    out.append(f'<path d="M22 23 h8 l4 -9 l6 18 l4 -9 h6" fill="none" stroke="{G}" stroke-width="2" class="blink"/>')
    for i, (k, v) in enumerate(items):
        if i:
            out.append(f'<line x1="{x}" y1="15" x2="{x}" y2="31" stroke="{LINE2}"/>'); x += 16
        if v is None:
            out.append(t(x, 27.5, k, "m g", 11.5, 'letter-spacing="1.5"')); x += 92
        else:
            out.append(f'<text x="{x}" y="27.5" class="m t" font-size="11.5" letter-spacing="1">{k}: <tspan class="g">{v}</tspan></text>')
            x += (len(k) + len(v) + 2) * 6.9 + 16
    out.append(f'<g transform="translate(642 13)" fill="none" stroke="{G}" stroke-width="1.6"><circle cx="10" cy="10" r="6.5"/><path d="M10 0v5M10 15v5M0 10h5M15 10h5"/></g>')
    out.append(t(W - 22, 27.5, "51.4816° N, 3.1791° W  //  CARDIFF, WALES", "m t", 11, 'text-anchor="end" letter-spacing="1"'))
    return svg(h, "".join(out), "Telemetry: systems online")


def pillars():
    h = 132
    cards = [("code", ["10+ YEARS", "BUILDING"], ["From ideas to", "production-grade systems"]),
             ("cloud", ["CLOUD & AI"], ["Scalable, intelligent", "and reliable systems", "on the cloud"]),
             ("sat", ["SPACE", "TELEMETRY"], ["Telemetry, data systems", "and ground segments"]),
             ("gh", ["OPEN SOURCE"], ["Build · Contribute · Share", "for a better ecosystem"])]
    out, cw, gap = [], 229, 14
    for i, (ic, title, desc) in enumerate(cards):
        x, y = 24 + i * (cw + gap), 18
        out.append(chamfer(x, y, cw, 96))
        out.append(brand("github", x + 18, y + 22, 34) if ic == "gh" else line_icon(ic, x + 18, y + 22, 36))
        ty = y + (34 if len(title) == 2 else 44)
        for j, s in enumerate(title):
            out.append(t(x + 70, ty + j * 22, s, "h", 19.5, 'letter-spacing="1.5"'))
        dy = ty + len(title) * 22 - 4
        for j, s in enumerate(desc[: 3 if len(title) == 1 else 2]):
            out.append(t(x + 70, dy + j * 14, s, "m", 10))
    return svg(h, "".join(out), "10+ years building · Cloud & AI · Space telemetry · Open source")


def illo(kind, x, y):
    st = f'fill="none" stroke="{G}" stroke-width="1.3"'
    earth = (f'<path d="M{x-6},{y+150} Q{x+60},{y+112} {x+136},{y+128}" fill="none" stroke="{G}" stroke-width="2" stroke-opacity=".75"/>'
             f'<path d="M{x-6},{y+150} Q{x+60},{y+112} {x+136},{y+128} V{y+160} H{x-6}z" fill="{G}" fill-opacity=".08"/>')
    if kind == "cube":
        cx, cy, s = x + 64, y + 62, 38
        return earth + f"""<g {st} class="float">
<path d="M{cx},{cy-s} L{cx+s},{cy-s/2} L{cx+s},{cy+s/2} L{cx},{cy+s} L{cx-s},{cy+s/2} L{cx-s},{cy-s/2} Z"/>
<path d="M{cx-s},{cy-s/2} L{cx},{cy} L{cx+s},{cy-s/2} M{cx},{cy} V{cy+s}" />
<path d="M{cx-s*.6},{cy-s*.1} L{cx-s*.6},{cy+s*.5} M{cx-s*.3},{cy+s*.05} V{cy+s*.65} M{cx+s*.3},{cy+s*.05} V{cy+s*.65} M{cx+s*.6},{cy-s*.1} V{cy+s*.5}" stroke-opacity=".5"/>
<line x1="{cx}" y1="{cy-s}" x2="{cx}" y2="{cy-s-18}"/><circle cx="{cx}" cy="{cy-s-20}" r="2.5" class="g blink" stroke="none"/></g>
<path d="M{x+4},{y+20} h18 M{x+4},{y+20} v18" {st} stroke-opacity=".5"/>"""
    if kind == "rocket":
        cx, cy = x + 68, y + 40
        return f"""<g transform="rotate(32 {cx} {cy+30})"><g class="float">
<path d="M{cx},{cy-30} C{cx+16},{cy-12} {cx+16},{cy+30} {cx+12},{cy+50} H{cx-12} C{cx-16},{cy+30} {cx-16},{cy-12} {cx},{cy-30} Z" fill="#0b2a17" stroke="{G}" stroke-width="1.5"/>
<circle cx="{cx}" cy="{cy+4}" r="6" {st}/>
<path d="M{cx-12},{cy+32} L{cx-24},{cy+56} L{cx-12},{cy+50} M{cx+12},{cy+32} L{cx+24},{cy+56} L{cx+12},{cy+50}" {st}/>
<path d="M{cx-8},{cy+52} Q{cx},{cy+100} {cx+8},{cy+52}" fill="{G}" fill-opacity=".85"><animate attributeName="opacity" values="1;.55;1" dur=".6s" repeatCount="indefinite"/></path>
<path d="M{cx-14},{cy+58} Q{cx},{cy+128} {cx+14},{cy+58}" fill="{G}" fill-opacity=".18"/></g></g>
<path d="M{x},{y+150} q20,-22 40,-6 q14,-24 36,-4 q20,-18 40,0 q12,-8 24,6 V{y+160} H{x}z" fill="{G}" fill-opacity=".10" stroke="{G}" stroke-opacity=".4"/>"""
    if kind == "crane":
        bx, by = x + 18, y + 150
        return f"""<g {st}>
<path d="M{bx},{by} V{by-128} M{bx+12},{by} V{by-128} M{bx},{by-128} H{bx+120} M{bx},{by-116} H{bx+120} M{bx-14},{by-122} H{bx}"/>
{''.join(f'<path d="M{bx},{by-12*k} L{bx+12},{by-12*(k+1)} M{bx+12},{by-12*k} L{bx},{by-12*(k+1)}" stroke-opacity=".45"/>' for k in range(10))}
{''.join(f'<path d="M{bx+12+12*k},{by-128} L{bx+24+12*k},{by-116}" stroke-opacity=".45"/>' for k in range(9))}
<line x1="{bx+86}" y1="{by-116}" x2="{bx+86}" y2="{by-80}"/>
<g class="float"><rect x="{bx+56}" y="{by-80}" width="60" height="34" fill="#0b2a17"/>{''.join(f'<line x1="{bx+62+8*k}" y1="{by-76}" x2="{bx+62+8*k}" y2="{by-50}" stroke-opacity=".6"/>' for k in range(7))}</g>
<rect x="{bx+40}" y="{by-30}" width="72" height="30" fill="#0b2a17"/>{''.join(f'<line x1="{bx+46+8*k}" y1="{by-26}" x2="{bx+46+8*k}" y2="{by-4}" stroke-opacity=".6"/>' for k in range(9))}
</g><line x1="{x}" y1="{by}" x2="{x+136}" y2="{by}" stroke="{G}" stroke-opacity=".6"/>"""


def projects():
    h = 262
    cards = [("cube", ["CubeSAT", "Telemetry"], ["Telemetry processing,", "VHF ground stations and", "edge AI for CubeSATs."], ["Python", "Edge AI", "VHF"]),
             ("rocket", ["Rocket", "Telemetry"], ["Real-time payload", "telemetry and flight", "analytics for rockets."], ["STM32", "LoRa", "Python"]),
             ("crane", ["Logistics", "Intelligence"], ["Vessel tracking, delay", "prediction and ERP", "automation for freight."], ["Python", "Odoo", "AI/ML"])]
    out = [heading("MISSION CONTROL", "WHAT I'M BUILDING", "PROJECTS / RESEARCH / EXPERIMENTS")]
    cw, gap = 309, 16
    for i, (kind, title, desc, tags) in enumerate(cards):
        x, y = 24 + i * (cw + gap), 84
        out.append(chamfer(x, y, cw, 162, 16))
        out.append(f'<g clip-path="url(#cc{i})">{illo(kind, x + 2, y)}</g>')
        out.append(f'<clipPath id="cc{i}"><rect x="{x+1}" y="{y+1}" width="140" height="160"/></clipPath>')
        tx = x + 148
        for j, s in enumerate(title):
            out.append(t(tx, y + 34 + j * 23, s, "h", 21, 'letter-spacing="0.5"'))
        for j, s in enumerate(desc):
            out.append(t(tx, y + 92 + j * 13.5, s, "m", 9.6))
        px = tx
        for s in tags:
            tw = len(s) * 6.6 + 14
            out.append(f'<rect x="{px}" y="{y+132}" width="{tw}" height="19" rx="3" fill="#081a0f" stroke="{LINE2}"/>')
            out.append(t(px + tw / 2, y + 145.5, s, "m t", 10, 'text-anchor="middle"'))
            px += tw + 6
    return svg(h, "".join(out), "What I'm building: CubeSAT telemetry, rocket telemetry, logistics intelligence")


def stack():
    h = 190
    tools = [("python", "Python"), ("fastapi", "FastAPI"), ("django", "Django"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
             ("amazonwebservices", "AWS"), ("azure", "Azure"), ("postgresql", "PostgreSQL"), ("apachekafka", "Kafka"), ("react", "React")]
    out = [heading("TECH STACK", "CORE SYSTEMS", "TOOLS / PLATFORMS / FRAMEWORKS")]
    tw, gap = 88, 7.7
    for i, (slug, name) in enumerate(tools):
        x, y = 24 + i * (tw + gap), 84
        out.append(f'<rect x="{x}" y="{y}" width="{tw}" height="86" rx="6" fill="url(#cardg)" stroke="{LINE2}"/>')
        out.append(f'<path d="M{x+6},{y+86} H{x+tw-6}" stroke="{G}" stroke-opacity=".5"/>')
        out.append(brand(slug, x + tw / 2 - 17, y + 14, 34))
        out.append(t(x + tw / 2, y + 70, name, "m t", 11.5, 'text-anchor="middle"'))
    return svg(h, "".join(out), "Core systems: " + ", ".join(n for _, n in tools))


def focus():
    h = 204
    cards = [("chip", ["Edge AI"], ["Lightweight, real-time AI", "at the edge for autonomous", "and remote systems."]),
             ("radio", ["Real-Time", "Streaming"], ["Low-latency, high-throughput", "pipelines for telemetry", "and operations."]),
             ("rocket", ["Aerospace", "Systems"], ["Telemetry, ground systems", "and data intelligence for", "space and launch missions."]),
             ("layers", ["Distributed", "Architecture"], ["Scalable, resilient and", "cloud-native systems for", "real-world workloads."])]
    out = [heading("CURRENT FOCUS", "WHAT I'M EXPLORING NOW", "FOCUS / R&D / NEXT")]
    cw, gap = 229, 14
    for i, (ic, title, desc) in enumerate(cards):
        x, y = 24 + i * (cw + gap), 82
        out.append(chamfer(x, y, cw, 104))
        out.append(line_icon(ic, x + 16, y + 16, 32))
        for j, s in enumerate(title):
            out.append(t(x + 62, y + 30 + j * 19, s, "h", 17))
        for j, s in enumerate(desc):
            out.append(t(x + 62, y + 30 + len(title) * 19 + j * 12.5, s, "m", 9.4))
    return svg(h, "".join(out), "Exploring now: edge AI, real-time streaming, aerospace systems, distributed architecture")


def footer():
    h = 190
    hills = (f'<path d="M0,{h} V150 Q120,120 240,140 T480,128 T720,146 T{W},126 V{h} Z" fill="#06150b" stroke="{G}" stroke-opacity=".35"/>'
             f'<path d="M0,{h} V170 Q160,150 320,166 T660,160 T{W},150 V{h} Z" fill="#040d07"/>')
    dish = f"""<g transform="translate(60 70)" fill="none" stroke="{G}" stroke-width="1.5">
<path d="M0,40 Q30,90 90,70 Z" fill="#0b2a17" transform="rotate(-25 45 55)"/>
<path d="M45,55 L70,15" /><circle cx="71" cy="13" r="3" fill="{G}" class="blink" stroke="none"/>
<path d="M40,64 L32,110 M52,62 L62,110 M26,110 H68"/>
<path d="M78,6 a14 14 0 0 1 12 12 M82,-2 a24 24 0 0 1 18 20" stroke-opacity=".6" class="blink"/></g>"""
    body = f"""<defs><clipPath id="ff"><rect x="1" y="1" width="{W-2}" height="{h-2}" rx="10"/></clipPath>
<radialGradient id="fh" cx=".5" cy="1" r=".7"><stop offset="0" stop-color="{G}" stop-opacity=".16"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></radialGradient></defs>
<g clip-path="url(#ff)"><rect width="{W}" height="{h}" fill="url(#fh)"/>{hills}{dish}</g>
<path d="M300,48 V32 H318 M700,32 H718 V48" fill="none" stroke="{G}" stroke-width="2"/>
<path d="M718,74 V90 H700" fill="none" stroke="{G}" stroke-width="2"/>
{t(W/2+9, 70, "BUILD. BREAK. REFINE. REPEAT.", "h g", 25, 'text-anchor="middle" letter-spacing="5"')}
<g transform="translate(296 104) scale(.8)"><path d="{ICONS['github']['path']}" fill="{TXT}"/></g>
{t(326, 120, "github.com/dpkrobomad", "m t", 13)}
<line x1="512" y1="104" x2="512" y2="126" stroke="{LINE2}"/>
<g transform="translate(540 104) scale(.8)" fill="none" stroke="{TXT}" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></g>
{t(570, 120, "deepakradhakrishnan.com", "m t", 13)}
{t(W-40, 40, "LAT : 51.4816° N", "m", 10.5, 'text-anchor="end"')}
{t(W-40, 56, "LON :  3.1791° W", "m", 10.5, 'text-anchor="end"')}
{t(W-40, 72, "ALT :   0.0 km", "m", 10.5, 'text-anchor="end"')}
{brackets(W, h)}"""
    return svg(h, body, "Build. Break. Refine. Repeat. — github.com/dpkrobomad · deepakradhakrishnan.com")


# ---------------------------------------------------------------- live activity
def token():
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def gql(q):
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": q}).encode(),
                                 {"Authorization": f"bearer {token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        d = json.load(r)
    if "errors" in d:
        raise SystemExit(d["errors"])
    return d["data"]


def activity():
    d = gql(f"""{{user(login:"{USER}"){{
      contributionsCollection{{contributionCalendar{{totalContributions weeks{{contributionDays{{date contributionCount weekday}}}}}}}}
      repositories(first:100,ownerAffiliations:OWNER,isFork:false){{nodes{{languages(first:10){{edges{{size node{{name}}}}}}}}}}}}}}""")["user"]
    cal = d["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"][-52:]
    langs = {}
    for r in d["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    tot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]

    h = 268
    out = [heading("DEVELOPMENT SIGNAL", "ACTIVITY GRID", "CODE / COMMITS / CONTRIBUTIONS")]
    gx, gy, step, cs = 66, 108, 10.6, 8.6
    mx = max((dd["contributionCount"] for w in weeks for dd in w["contributionDays"]), default=1) or 1
    shades = ["#0b1a10", "#0f4a23", "#1a7a3a", "#27b552", G]
    last_m = None
    for wi, w in enumerate(weeks):
        for dd in w["contributionDays"]:
            c = dd["contributionCount"]
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / mx))
            out.append(f'<rect x="{gx+wi*step:.1f}" y="{gy+dd["weekday"]*step:.1f}" width="{cs}" height="{cs}" rx="1.5" fill="{shades[lvl]}"><title>{dd["date"]}: {c}</title></rect>')
        m = dt.date.fromisoformat(w["contributionDays"][0]["date"]).strftime("%b")
        if m != last_m and wi < len(weeks) - 2:
            out.append(t(gx + wi * step, gy - 10, m, "m", 10))
            last_m = m
    for lab, wd in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        out.append(t(28, gy + wd * step + 8, lab, "m", 10))
    out.append(t(gx, gy + 7 * step + 26, f"{cal['totalContributions']} contributions in the last year", "m t", 11.5))
    out.append(t(gx + len(weeks) * step - 2, gy + 7 * step + 26, "updated " + dt.date.today().isoformat(), "m", 10, 'text-anchor="end"'))
    lx = gx + len(weeks) * step - 112
    out.append(t(lx - 30, gy + 7 * step + 44, "less", "m", 9.5))
    for i, sh in enumerate(shades):
        out.append(f'<rect x="{lx+i*12}" y="{gy+7*step+36}" width="9" height="9" rx="1.5" fill="{sh}"/>')
    out.append(t(lx + 64, gy + 7 * step + 44, "more", "m", 9.5))

    # right panel: weekly sparkline + language split (both real)
    px, pw = 652, 324
    out.append(f'<line x1="{px-18}" y1="86" x2="{px-18}" y2="{h-22}" stroke="{LINE}"/>')
    out.append(chamfer(px, 82, pw, 74, 12, fill="#06100a"))
    vals = [sum(dd["contributionCount"] for dd in w["contributionDays"]) for w in weeks]
    vm = max(vals) or 1
    pts = [(px + 10 + i * (pw - 20) / (len(vals) - 1), 146 - 38 * v / vm) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    out.append(f'<polygon points="{px+10},146 {line} {px+pw-10},146" fill="{G}" fill-opacity=".12"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{G}" stroke-width="1.8" stroke-linejoin="round"/>')
    out.append(t(px + 12, 98, "WEEKLY CONTRIBUTIONS · 52 WEEKS", "m", 9, 'letter-spacing="1"'))
    for i, (name, size) in enumerate(top):
        y = 182 + i * 19
        pct = size / tot
        out.append(f'<circle cx="{px+6}" cy="{y-4}" r="3.5" fill="{G}"/>')
        out.append(t(px + 18, y, name, "m t", 10.5))
        out.append(f'<rect x="{px+112}" y="{y-8}" width="{pw-160}" height="6" rx="3" fill="#0d2015"/>')
        out.append(f'<rect x="{px+112}" y="{y-8}" width="{(pw-160)*pct:.1f}" height="6" rx="3" fill="{G}"/>')
        out.append(t(px + pw, y, f"{pct*100:.0f}%", "m", 10, 'text-anchor="end"'))
    out.append(t(px + 18, 182 + 4 * 19 - 2, "language share across my own repositories (by bytes)", "m", 8.6))
    return svg(h, "".join(out), f"Activity: {cal['totalContributions']} contributions in the last year")


def main():
    jobs = {"activity.svg": activity}
    if "--activity" not in sys.argv:
        jobs.update({"hero.svg": hero, "telemetry.svg": telemetry, "pillars.svg": pillars, "projects.svg": projects,
                     "stack.svg": stack, "focus.svg": focus, "footer.svg": footer,
                     "btn-projects.svg": lambda: button("EXPLORE PROJECTS", "gh", 250, True),
                     "btn-connect.svg": lambda: button("CONNECT", "link", 190, False),
                     "btn-site.svg": lambda: button("WEBSITE", "globe", 190, False)})
    for name, fn in jobs.items():
        (A / name).write_text(fn())
        print("wrote", name, f"{(A/name).stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
