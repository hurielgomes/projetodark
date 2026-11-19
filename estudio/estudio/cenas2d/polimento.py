"""
polimento.py - acabamento "cinematografico" do M1 (usado pela CenaGenerica; os modelos antigos nao mudam).

    exposicao_auto(frame)      -> levanta sombras quando a cena sai escura demais (o maior problema dos recursos da IA)
    Particulas(...)            -> poeira/brasas/estrelas flutuando com parallax (vida no fundo, mesmo com cena "parada")
    texto_contagem(txt, p)     -> anima o numero de um texto ("8,5 MILHOES" conta de 0 ate 8,5)
    titulo_gancho(...)         -> titulo grande do inicio do video (kinetic: palavra por palavra)
    barra_progresso(...)       -> barra fina no topo (retencao: o espectador ve que falta pouco)
    flash_corte(...)           -> pulso de luz no corte entre cenas (corte "seco" sem escurecer o quadro)
Tudo e funcao pura de t.
"""
import math
import random
import re

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

from ..comum.tween import clamp, out_back, out_cubic, tw
from .pintura import Lona, alfa, mix

ACENTOS = {"noite": (53, 214, 255), "apagado": (90, 150, 255), "dia": (255, 205, 90),
           "entardecer": (255, 150, 90), "alerta": (255, 90, 74)}


def acento_de(cena):
    from .recursos.validar import cor as _cor
    c = cena.get("acento")
    if c:
        v = _cor(c)
        if v:
            return tuple(v[:3])
    return ACENTOS.get(cena.get("clima") or "noite", ACENTOS["noite"])


# ------------------------------------------------------------------ exposicao
def gamma_para(rgb, alvo=64.0, minimo=0.60):
    """gamma (<=1) que leva a luminancia media para `alvo`; 1.0 se a cena ja e clara o bastante"""
    pq = rgb.resize((48, 84), Image.BILINEAR).convert("L")
    h = pq.histogram()
    n = sum(h) or 1
    media = sum(i * c for i, c in enumerate(h)) / n
    if media >= alvo:
        return 1.0
    media = max(media, 4.0)
    g = math.log(alvo / 255.0) / math.log(media / 255.0)
    return max(minimo, min(1.0, g))


_lut_cache = {}


def exposicao(rgb, gamma, base=5):
    if gamma >= 0.995 and base <= 0:
        return rgb
    k = (round(gamma, 3), base)
    if k not in _lut_cache:
        lut = [int(max(0, min(255, base + (255 - base) * ((v / 255.0) ** gamma)))) for v in range(256)]
        _lut_cache[k] = lut * 3
    return rgb.point(_lut_cache[k])


def saturar(rgb, f=1.14, contraste=1.04):
    out = ImageEnhance.Color(rgb).enhance(f)
    return ImageEnhance.Contrast(out).enhance(contraste)


# ------------------------------------------------------------------ particulas
_dot_cache = {}


def _dot(r, cor):
    k = (int(r), cor)
    if k not in _dot_cache:
        d = int(r * 2 + 2)
        m = Image.new("L", (d, d), 0)
        c = d / 2.0
        px = m.load()
        for y in range(d):
            for x in range(d):
                q = math.hypot(x + 0.5 - c, y + 0.5 - c) / max(1.0, r)
                px[x, y] = int(255 * max(0.0, 1 - q) ** 1.6)
        im = Image.new("RGBA", (d, d), tuple(cor[:3]) + (0,))
        im.putalpha(m)
        _dot_cache[k] = im
    return _dot_cache[k]


class Particulas:
    """n particulas que sobem devagar balancando; tamanho/velocidade variam (3 planos de profundidade)"""

    def __init__(self, w, h, cor, n=34, seed=1, intensidade=0.55):
        r = random.Random(seed * 7919 + 13)
        self.w, self.h, self.cor, self.int = w, h, tuple(cor), intensidade
        self.ps = []
        u = min(w, h) / 1080.0
        for _ in range(n):
            z = r.choice((0.5, 0.8, 1.0, 1.4))
            self.ps.append({"x": r.random(), "y": r.random(), "z": z, "r": (3 + 6 * r.random()) * z * u,
                            "v": (0.018 + 0.03 * r.random()) * z, "f": r.random() * 6.28, "a": (0.25 + 0.55 * r.random())})

    def desenhar(self, frame_rgba, t):
        W, H = self.w, self.h
        for p in self.ps:
            y = (p["y"] - p["v"] * t) % 1.15 - 0.075
            x = (p["x"] + 0.018 * math.sin(t * 0.9 + p["f"]) * p["z"]) % 1.0
            a = p["a"] * self.int * (0.6 + 0.4 * math.sin(t * 2.1 + p["f"]))
            if a <= 0.02:
                continue
            d = _dot(p["r"], self.cor)
            if a < 0.99:
                d = d.copy()
                d.putalpha(d.getchannel("A").point(lambda v, a=a: int(v * a)))
            px, py = int(x * W - d.width / 2), int(y * H - d.height / 2)
            if -d.width < px < W and -d.height < py < H:
                frame_rgba.alpha_composite(d.crop((max(0, -px), max(0, -py), min(d.width, W - px), min(d.height, H - py))),
                                           dest=(max(0, px), max(0, py)))


# ------------------------------------------------------------------ objetos "paisagem em retangulo"
_feather = {}


def caixa_dura(img, limiar=0.80):
    """True se o sprite e quase um retangulo cheio (a IA desenhou uma paisagem/quadro em vez de um objeto isolado)"""
    a = img.getchannel("A").resize((24, 24), Image.BILINEAR)
    h = a.histogram()
    cheio = sum(h[60:])
    return cheio / 576.0 >= limiar


def suavizar_caixa(img, fator=0.16):
    """derrete as bordas duras: mascara de retangulo arredondado com borda difusa (vira uma 'janela de luz', nao uma caixa)"""
    w, h = img.size
    k = (w // 4, h // 4, fator)
    if k not in _feather:
        sw, sh = max(8, w // 4), max(8, h // 4)
        m = Image.new("L", (sw, sh), 0)
        from PIL import ImageDraw
        ins = fator * min(sw, sh)
        ImageDraw.Draw(m).rounded_rectangle((ins, ins, sw - ins, sh - ins), radius=ins * 1.4, fill=255)
        _feather[k] = m.filter(ImageFilter.GaussianBlur(ins * 0.62))
    mask = _feather[k].resize((w, h), Image.BILINEAR)
    out = img.copy()
    out.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    return out


# ------------------------------------------------------------------ contador
_NUM = re.compile(r"\d[\d\.,]*")


def texto_contagem(texto, p):
    """anima o 1o numero do texto de 0 ate o valor (mantem formato pt-BR: 8,5 / 7.300 / 360)"""
    m = _NUM.search(texto or "")
    if not m or p >= 0.999:
        return texto
    tok = m.group(0).rstrip(".,")
    if "," in tok:
        casas = len(tok.split(",")[1])
        val = float(tok.replace(".", "").replace(",", "."))
        s = f"{val * clamp(p):.{casas}f}".replace(".", ",")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", tok):
        val = float(tok.replace(".", ""))
        s = f"{int(round(val * clamp(p))):,}".replace(",", ".")
    else:
        try:
            val = float(tok)
        except ValueError:
            return texto
        s = str(int(round(val * clamp(p))))
    return texto[:m.start()] + s + texto[m.start() + len(tok):]


# ------------------------------------------------------------------ titulo gancho
def _quebrar(txt, maxw, medir):
    pal, linhas, cur = txt.split(), [], ""
    for w in pal:
        tent = (cur + " " + w).strip()
        if cur and medir(tent) > maxw:
            linhas.append(cur)
            cur = w
        else:
            cur = tent
    if cur:
        linhas.append(cur)
    return linhas


def titulo_gancho(f, t, w, h, u, texto, acento, ini=0.12, fim=3.0, y=0.19, tam=76, vertical=True):
    """headline do inicio: cada palavra 'pula' em sequencia; ultima linha na cor de acento"""
    if not texto or not (ini <= t < fim):
        return
    ts = tam * u * (1.0 if vertical else 0.85)
    tmp = Lona(10, 10, 1)
    maxw = w * (0.88 if vertical else 0.62)
    linhas = _quebrar(texto.upper(), maxw, lambda s: tmp.largura(s, "preto", ts))
    linhas = linhas[:4]
    alt = ts * 1.12
    topo = h * y - len(linhas) * alt / 2
    saida = clamp((fim - t) / 0.25)
    n_pal = sum(len(l.split()) for l in linhas)
    k = 0
    W0, H0 = int(w), int(len(linhas) * alt + ts * 2)
    sh, tx = Lona(W0, H0, 1), Lona(W0, H0, 2)
    for li, linha in enumerate(linhas):
        pals = linha.split()
        ws = [tmp.largura(p, "preto", ts) for p in pals]
        esp = ts * 0.28
        x = (W0 - (sum(ws) + esp * (len(pals) - 1))) / 2
        yy = ts + li * alt + alt / 2
        for p, wp in zip(pals, ws):
            pe = tw(t, ini + 0.09 * k, 0.32, "out_back")
            k += 1
            if pe <= 0.001:
                x += wp + esp
                continue
            cor = acento if li == len(linhas) - 1 else (255, 255, 255)
            esc = 0.6 + 0.4 * pe
            cx, cy = x + wp / 2, yy - (1 - pe) * ts * 0.35
            sh.texto(cx, cy + ts * 0.07, p, "preto", ts * esc, (0, 0, 0, 255), anchor="mm", stroke=ts * 0.10, stroke_fill=(0, 0, 0, 255))
            tx.texto(cx, cy, p, "preto", ts * esc, cor + (255,), anchor="mm", stroke=ts * 0.045, stroke_fill=(8, 10, 24, 255))
            x += wp + esp
    a = sh.pronto().filter(ImageFilter.GaussianBlur(ts * 0.10))
    b = tx.pronto()
    if saida < 0.999:
        for im in (a, b):
            im.putalpha(im.getchannel("A").point(lambda v, s=saida: int(v * s)))
    f.alpha_composite(a, dest=(0, int(topo - ts)))
    f.alpha_composite(b, dest=(0, int(topo - ts)))


# ------------------------------------------------------------------ progresso / flash
def barra_progresso(f, w, h, u, frac, cor, y=0.0):
    if frac <= 0:
        return
    hh = max(4, int(7 * u))
    y0 = int(h * y)
    trilho = Image.new("RGBA", (w, hh), (255, 255, 255, 38))
    f.alpha_composite(trilho, dest=(0, y0))
    ww = max(2, int(w * min(1.0, frac)))
    barra = Image.new("RGBA", (ww, hh), tuple(cor[:3]) + (235,))
    f.alpha_composite(barra, dest=(0, y0))
    brilho = Image.new("RGBA", (int(28 * u), hh), (255, 255, 255, 150))
    f.alpha_composite(brilho, dest=(max(0, ww - brilho.width), y0))


def flash_corte(f, t, cor, dur=0.16, forca=0.30):
    a = (1 - clamp(t / dur)) ** 2 * forca
    if a > 0.01:
        f.alpha_composite(Image.new("RGBA", f.size, tuple(mix(cor, (255, 255, 255), 0.55)) + (int(255 * a),)))

