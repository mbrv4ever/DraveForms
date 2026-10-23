#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveForms - PDF-lezer met invulbare formulieren (dropdowns, tekst, vinkjes).
Dravenlock-huisstijl. Open, invullen, opslaan - werkt buiten Adobe.
"""
import os
import sys
import json
import math

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from PyQt6.QtCore import Qt, QRect, QLocale, pyqtSignal, QPoint
from PyQt6.QtGui import (QPixmap, QImage, QPainter, QColor, QBrush, QPen,
                         QIcon, QDesktopServices)
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QScrollArea, QFileDialog, QComboBox, QLineEdit, QCheckBox,
    QMessageBox, QDialog, QToolButton, QSpinBox, QFrame,
    QPlainTextEdit, QStatusBar)

APP_NAME = "DraveForms"
APP_VERSION = "0.8.3"
DONATE_URL = "https://paypal.me/roger076"
SUPPORT_MAIL = "service@dravenlock.nl"

# ---- Dravenlock-huisstijl ----
BG = "#0e0e11"
PANEL = "#16161b"
SILVER = "#d4d4d4"
MUTE = "#8a8a94"
ACCENT = "#6fa3d6"
WARN = "#e0a23a"

# ---------------------------------------------------------------------------
# Pad-helpers (frozen-bewust)
# ---------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "draveforms_config.json")


DEFAULT_CONFIG = {"lang": ""}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal (NL basis + OS-detectie + handmatige keuze)
# ---------------------------------------------------------------------------
_LANG = "nl"

TRANSLATIONS = {
    "en": {
        "Openen": "Open", "Opslaan": "Save", "Opslaan als\u2026": "Save as\u2026",
        "Vorige": "Previous", "Volgende": "Next", "Pagina": "Page",
        "Instellingen\u2026": "Settings\u2026", "Snelgids": "Quick guide",
        "Over": "About", "Sluiten": "Close", "Taal:": "Language:",
        "Automatisch (OS)": "Automatic (OS)", "Nederlands": "Dutch", "Engels": "English",
        "Open een PDF om te beginnen": "Open a PDF to get started",
        "Geen invulvelden op deze pagina": "No form fields on this page",
        "PDF-bestanden (*.pdf)": "PDF files (*.pdf)", "Alle bestanden (*)": "All files (*)",
        "Opgeslagen": "Saved", "Opgeslagen als": "Saved as",
        "Het bestand is opgeslagen.": "The file has been saved.",
        "Kon niet openen": "Could not open", "Kon niet opslaan": "Could not save",
        "velden": "fields", "Beveiligd (XFA)": "Protected (XFA)",
        "Dit formulier gebruikt XFA": "This form uses XFA",
        "xfa_uitleg": ("This PDF uses Adobe's XFA form technology. DraveForms shows and "
                       "fills the standard (AcroForm) layer if present, but purely dynamic "
                       "XFA forms may not behave exactly as in Adobe."),
        "Niet-opgeslagen wijzigingen": "Unsaved changes",
        "Wil je de wijzigingen opslaan?": "Do you want to save your changes?",
        "Inzoomen": "Zoom in", "Uitzoomen": "Zoom out", "Passend": "Fit width",
        "Donatie": "Donate", "van": "of",
        "snelgids_titel": "DraveForms - quick guide",
        "Geen invulvelden": "No form fields",
        "Tekst toevoegen": "Add text",
        "Welke tekst wil je plaatsen?": "What text do you want to place?",
        "Tekst bewerken": "Edit text",
        "Pas de tekst aan (leeg maken = verwijderen):": "Edit the text (clear it = delete):",
        "Klik op de pagina waar je tekst wilt plaatsen.": "Click on the page where you want to place text.",
        "Lettergrootte": "Font size",
        "Typ hier je tekst\u2026": "Type your text here\u2026",
        "Tip: na plaatsen kun je de tekst verslepen naar de juiste plek.":
            "Tip: after placing, you can drag the text to the right spot.",
        "Verwijderen": "Delete", "Annuleren": "Cancel", "Plaatsen": "Place",
        "Tekst-editor": "Text editor", "Kleiner": "Smaller", "Groter": "Larger",
        "Vet": "Bold", "Cursief": "Italic", "Kleur": "Color",
        "Sleep geplaatste tekst om te verschuiven; dubbelklik om te bewerken.":
            "Drag placed text to move it; double-click to edit.",
        "Sleep om te verschuiven, dubbelklik om te bewerken.":
            "Drag to move, double-click to edit.",
    }
}


def detect_lang(cfg):
    forced = (cfg.get("lang") or "").strip().lower()
    if forced in ("nl", "en"):
        return forced
    try:
        loc = QLocale.system().name().lower()
        if loc.startswith("nl"):
            return "nl"
    except Exception:
        pass
    try:
        loc = QLocale.system().name().lower()
        if loc.startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


def t(s, lang=None):
    lg = lang or _LANG
    if lg == "nl":
        return s
    return TRANSLATIONS.get(lg, {}).get(s, s)


# ---------------------------------------------------------------------------
# Logo / icoon (document met dropdown-pijltje, staalblauw)
# ---------------------------------------------------------------------------
def make_logo(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    # documentvorm
    p.setBrush(QBrush(QColor(ACCENT)))
    p.setPen(Qt.PenStyle.NoPen)
    margin = s * 0.16
    p.drawRoundedRect(int(margin), int(margin * 0.7),
                      int(s - 2 * margin), int(s - 1.4 * margin),
                      int(s * 0.10), int(s * 0.10))
    # "regels"
    p.setPen(QPen(QColor(BG), max(1, int(s * 0.05))))
    y0 = s * 0.40
    for i in range(2):
        yy = int(y0 + i * s * 0.16)
        p.drawLine(int(s * 0.32), yy, int(s * 0.68), yy)
    # dropdown-driehoekje
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(BG)))
    cx, cy, w = s * 0.50, s * 0.74, s * 0.12
    from PyQt6.QtGui import QPolygon
    from PyQt6.QtCore import QPoint
    tri = QPolygon([QPoint(int(cx - w), int(cy - w * 0.6)),
                    QPoint(int(cx + w), int(cy - w * 0.6)),
                    QPoint(int(cx), int(cy + w * 0.8))])
    p.drawPolygon(tri)
    p.end()
    return pm


def _logo_path():
    dirs = [_app_dir()]
    mp = getattr(sys, "_MEIPASS", None)
    if mp:
        dirs.append(mp)
    dirs.append(os.path.join(_app_dir(), "_internal"))
    for d in dirs:
        for name in ("logo.ico", "logo.png"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def app_icon():
    p = _logo_path()
    if p:
        ic = QIcon(p)
        if not ic.isNull():
            return ic
    return QIcon(make_logo(64))


def logo_pixmap(size=32):
    p = _logo_path()
    if p:
        pm = QPixmap(p)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    return make_logo(size)


# ---------------------------------------------------------------------------
# PDF-model (PyMuPDF)
# ---------------------------------------------------------------------------
TYPE_TEXT = fitz.PDF_WIDGET_TYPE_TEXT
TYPE_CHECK = fitz.PDF_WIDGET_TYPE_CHECKBOX
TYPE_COMBO = fitz.PDF_WIDGET_TYPE_COMBOBOX
TYPE_LIST = fitz.PDF_WIDGET_TYPE_LISTBOX
TYPE_RADIO = fitz.PDF_WIDGET_TYPE_RADIOBUTTON


class PdfModel:
    def __init__(self):
        self.doc = None
        self.path = None
        self.dirty = False

    def open(self, path):
        doc = fitz.open(path)
        self.doc = doc
        self.path = path
        self.dirty = False

    def close(self):
        if self.doc:
            self.doc.close()
        self.doc = None
        self.path = None

    @property
    def page_count(self):
        return self.doc.page_count if self.doc else 0

    def is_xfa(self):
        try:
            cat = self.doc.pdf_catalog()
            acro = self.doc.xref_get_key(cat, "AcroForm")
            if acro and acro[0] == "xref":
                ax = int(acro[1].split()[0])
                xfa = self.doc.xref_get_key(ax, "XFA")
                return xfa is not None and xfa[0] != "null"
        except Exception:
            pass
        return False

    def render(self, pno, zoom):
        page = self.doc[pno]
        # annots=False: velden en onze tekst tonen we als overlay-widgets,
        # dus geen dubbele weergave (de PDF zelf houdt alles wel).
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False,
                              annots=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                     QImage.Format.Format_RGB888)
        return img.copy(), pix.width, pix.height

    def fields(self, pno):
        """Lijst van velden op een pagina (genormaliseerd voor de UI)."""
        page = self.doc[pno]
        out = []
        radios = {}
        for w in page.widgets():
            ft = w.field_type
            r = w.rect
            base = {
                "name": w.field_name or "",
                "xref": w.xref,
                "rect": (float(r.x0), float(r.y0), float(r.x1), float(r.y1)),
                "value": w.field_value,
                "type": ft,
            }
            if ft == TYPE_COMBO or ft == TYPE_LIST:
                opts = []
                for o in (w.choice_values or []):
                    if isinstance(o, (list, tuple)):
                        # PDF-standaard: (exportwaarde, weergavetekst)
                        exp = str(o[0]) if len(o) > 0 else ""
                        disp = str(o[1]) if (len(o) > 1 and str(o[1]) != "") else exp
                    else:
                        disp = exp = str(o)
                    opts.append((disp, exp))
                base["choices"] = [d for d, _e in opts]
                base["choice_pairs"] = opts
                out.append(base)
            elif ft == TYPE_TEXT:
                out.append(base)
            elif ft == TYPE_CHECK:
                states = self._on_state(w)
                base["on"] = states
                out.append(base)
            elif ft == TYPE_RADIO:
                grp = radios.setdefault(w.field_name or "", {
                    "name": w.field_name or "", "type": TYPE_RADIO,
                    "value": w.field_value, "options": []})
                grp["options"].append({
                    "xref": w.xref,
                    "rect": (float(r.x0), float(r.y0), float(r.x1), float(r.y1)),
                    "on": self._on_state(w),
                })
            else:
                base["readonly"] = True
                out.append(base)
        for grp in radios.values():
            out.append(grp)
        return out

    @staticmethod
    def _on_state(w):
        try:
            states = w.button_states() or {}
            for key in ("normal", "down"):
                for s in states.get(key, []) or []:
                    if s and s != "Off":
                        return s
        except Exception:
            pass
        return "Yes"

    def set_text(self, pno, name, value):
        self._set(pno, name, value)

    def set_choice(self, pno, name, value):
        self._set(pno, name, value)

    def set_check(self, pno, name, on, value):
        self._set(pno, name, on if value else "Off")

    def set_radio(self, pno, name, on_state):
        self._set(pno, name, on_state, match_on=on_state)

    def _set(self, pno, name, value, match_on=None):
        page = self.doc[pno]
        for w in page.widgets():
            if w.field_name == name:
                if match_on is not None:
                    # radio: zet de gekozen optie aan
                    on = self._on_state(w)
                    w.field_value = (on == match_on) and on or "Off"
                    if on == match_on:
                        w.field_value = match_on
                    w.update()
                    self.dirty = True
                else:
                    if w.field_type in (TYPE_COMBO, TYPE_LIST):
                        w.choice_values = self._sanitize_choices(w.choice_values)
                    w.field_value = value
                    w.update()
                    self.dirty = True
                    return

    @staticmethod
    def _sanitize_choices(opts):
        """PyMuPDF eist bij update() dat elke keuze twee niet-lege leden heeft.
        Echte sheets hebben soms een blanco optie; die maken we 'bijna leeg'."""
        out = []
        for o in (opts or []):
            if isinstance(o, (list, tuple)):
                d = str(o[0]) if len(o) > 0 else ""
                e = str(o[1]) if len(o) > 1 else ""
            else:
                d = e = str(o)
            d = d or e or " "
            e = e or d or " "
            out.append((d, e))
        return out

    def save(self, path=None):
        if path and path != self.path:
            self.doc.save(path, garbage=4, deflate=True)
            self.doc.close()
            self.doc = fitz.open(path)
            self.path = path
        else:
            target = self.path
            tmp = target + ".dfsave.tmp"
            self.doc.save(tmp, garbage=4, deflate=True)
            self.doc.close()
            os.replace(tmp, target)
            self.doc = fitz.open(target)
        self.dirty = False

    # ---- Tekst toevoegen (Fase 2): vrije-tekst-annotaties met stijl ----
    @staticmethod
    def _hex_to_rgb01(hx):
        try:
            hx = (hx or "#000000").lstrip("#")
            return (int(hx[0:2], 16) / 255.0, int(hx[2:4], 16) / 255.0,
                    int(hx[4:6], 16) / 255.0)
        except Exception:
            return (0.0, 0.0, 0.0)

    def _add_text_rect(self, pno, rect, text, size, bold, italic, color):
        page = self.doc[pno]
        annot = page.add_freetext_annot(rect, text, fontsize=float(size),
                                        text_color=self._hex_to_rgb01(color))
        try:
            annot.set_border(width=0)
        except Exception:
            pass
        try:
            annot.set_colors(stroke=None, fill=None)
        except Exception:
            pass
        # stijl bewaren in 'subject' zodat het na opslaan/heropenen terugkomt
        try:
            style = json.dumps({"s": float(size), "b": bool(bold),
                                "i": bool(italic), "c": color})
            annot.set_info(subject=style)
        except Exception:
            pass
        annot.update()
        self.dirty = True
        return annot.xref

    def add_text(self, pno, x, y, text, size=14, bold=False, italic=False,
                 color="#000000"):
        """Plaats tekst op (x, y) (PDF-punten, top-left). Meerdere regels (\\n)
        mogen. Grootte en kleur tonen overal; vet/cursief tonen in DraveForms."""
        page = self.doc[pno]
        fs = float(size)
        lines = text.split("\n") or [""]
        longest = max((len(ln) for ln in lines), default=1)
        char_w = fs * 0.62
        line_h = fs * 1.45
        unclamped = longest * char_w + 12
        avail = max(60.0, page.rect.width - x - 4)
        width = min(avail, unclamped)
        # als de regel breder is dan de ruimte, breekt PyMuPDF af -> meer hoogte
        wrap = max(1, int(math.ceil(unclamped / width))) if width > 0 else 1
        total_lines = len(lines) * wrap
        height = total_lines * line_h + 12
        return self._add_text_rect(pno, fitz.Rect(x, y, x + width, y + height),
                                   text, fs, bold, italic, color)

    def _read_size(self, xref):
        try:
            da = self.doc.xref_get_key(xref, "DA")
            if da and len(da) > 1:
                import re
                m = re.search(r"([\d.]+)\s+Tf", da[1])
                if m:
                    return float(m.group(1))
        except Exception:
            pass
        return 14.0

    @staticmethod
    def _read_style(a, fallback_size):
        size, bold, italic, color = fallback_size, False, False, "#000000"
        try:
            subj = a.info.get("subject", "") or ""
            if subj:
                d = json.loads(subj)
                size = float(d.get("s", size))
                bold = bool(d.get("b", False))
                italic = bool(d.get("i", False))
                color = str(d.get("c", color))
        except Exception:
            pass
        return size, bold, italic, color

    def text_annots(self, pno):
        """Alle freetext-annotaties op een pagina (met stijl) voor de overlay."""
        page = self.doc[pno]
        out = []
        try:
            for a in page.annots(types=(fitz.PDF_ANNOT_FREE_TEXT,)):
                r = a.rect
                size, bold, italic, color = self._read_style(a, self._read_size(a.xref))
                out.append({"xref": a.xref,
                            "rect": (float(r.x0), float(r.y0), float(r.x1), float(r.y1)),
                            "text": a.info.get("content", ""),
                            "size": size, "bold": bold, "italic": italic,
                            "color": color})
        except Exception:
            pass
        return out

    def text_annot_at(self, pno, x, y):
        for a in self.text_annots(pno):
            x0, y0, x1, y1 = a["rect"]
            if x0 - 3 <= x <= x1 + 3 and y0 - 3 <= y <= y1 + 3:
                return a
        return None

    def _annot_by_xref(self, page, xref):
        try:
            for a in page.annots():
                if a.xref == xref:
                    return a
        except Exception:
            pass
        return None

    def edit_text(self, pno, xref, text, size=14, bold=False, italic=False,
                  color="#000000"):
        page = self.doc[pno]
        a = self._annot_by_xref(page, xref)
        if not a:
            return None
        r = fitz.Rect(a.rect)
        page.delete_annot(a)
        return self.add_text(pno, r.x0, r.y0, text, size, bold, italic, color)

    def move_text(self, pno, xref, x, y):
        """Versleep een tekst-annotatie naar nieuwe top-left (x, y)."""
        page = self.doc[pno]
        a = self._annot_by_xref(page, xref)
        if not a:
            return
        r = a.rect
        w, h = r.width, r.height
        a.set_rect(fitz.Rect(x, y, x + w, y + h))
        a.update()
        self.dirty = True

    def delete_text(self, pno, xref):
        page = self.doc[pno]
        a = self._annot_by_xref(page, xref)
        if a:
            page.delete_annot(a)
            self.dirty = True

    def field_count_total(self):
        n = 0
        if not self.doc:
            return 0
        for pno in range(self.page_count):
            try:
                n += len(self.fields(pno))
            except Exception:
                pass
        return n


# ---------------------------------------------------------------------------
# Pagina-weergave met overlay-velden
# ---------------------------------------------------------------------------
class TextEditorDialog(QDialog):
    """Mini tekst-editor: werkbalk met grootte, vet, cursief, kleur + tekstvlak."""

    DELETE = 2
    COLORS = ["#000000", "#c01616", "#1144cc", "#1a7a32", "#d98a00", "#ffffff"]

    def __init__(self, parent, title, text="", size=14, ok_label=None,
                 allow_delete=False, bold=False, italic=False, color="#000000"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setObjectName("texteditor")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(520, 380)
        self._size = int(round(size))
        self._color = color or "#000000"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- werkbalk ---
        bar = QWidget()
        bar.setObjectName("edbar")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(12, 8, 12, 8)
        bl.setSpacing(6)
        cap = QLabel("\u270e " + t("Tekst-editor"))
        cap.setObjectName("edcap")
        bl.addWidget(cap)
        bl.addStretch(1)

        self.b_minus = QToolButton()
        self.b_minus.setText("A\u2212")
        self.b_minus.setObjectName("edtool")
        self.b_minus.setToolTip(t("Kleiner"))
        self.b_minus.clicked.connect(lambda: self._bump(-2))
        bl.addWidget(self.b_minus)
        self.size_lbl = QLabel()
        self.size_lbl.setObjectName("sizereadout")
        self.size_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_lbl.setMinimumWidth(52)
        bl.addWidget(self.size_lbl)
        self.b_plus = QToolButton()
        self.b_plus.setText("A\u002b")
        self.b_plus.setObjectName("edtool")
        self.b_plus.setToolTip(t("Groter"))
        self.b_plus.clicked.connect(lambda: self._bump(+2))
        bl.addWidget(self.b_plus)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("sep")
        bl.addWidget(sep)

        self.b_bold = QToolButton()
        self.b_bold.setText("B")
        self.b_bold.setObjectName("edstyle")
        self.b_bold.setCheckable(True)
        self.b_bold.setChecked(bool(bold))
        self.b_bold.setToolTip(t("Vet"))
        self.b_bold.toggled.connect(self._apply_font)
        bl.addWidget(self.b_bold)
        self.b_italic = QToolButton()
        self.b_italic.setText("I")
        self.b_italic.setObjectName("edstyle")
        self.b_italic.setCheckable(True)
        self.b_italic.setChecked(bool(italic))
        self.b_italic.setToolTip(t("Cursief"))
        self.b_italic.toggled.connect(self._apply_font)
        bl.addWidget(self.b_italic)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setObjectName("sep")
        bl.addWidget(sep2)

        bl.addWidget(QLabel(t("Kleur") + ":"))
        self._swatches = []
        for c in self.COLORS:
            sw = QToolButton()
            sw.setObjectName("swatch")
            sw.setCheckable(True)
            sw.setFixedSize(20, 20)
            sw.setStyleSheet("QToolButton#swatch{background:%s;border:1px solid #555;"
                             "border-radius:4px;} QToolButton#swatch:checked{"
                             "border:2px solid %s;}" % (c, ACCENT))
            sw.clicked.connect(lambda _=False, col=c: self._set_color(col))
            bl.addWidget(sw)
            self._swatches.append((c, sw))

        root.addWidget(bar)

        # --- tekstvlak ---
        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 12)
        body.setSpacing(8)
        self.edit = QPlainTextEdit()
        self.edit.setObjectName("texteditarea")
        self.edit.setPlainText(text)
        self.edit.setPlaceholderText(t("Typ hier je tekst\u2026"))
        body.addWidget(self.edit, 1)
        hint = QLabel(t("Sleep geplaatste tekst om te verschuiven; dubbelklik om te bewerken."))
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        body.addWidget(hint)

        btns = QHBoxLayout()
        if allow_delete:
            dele = QPushButton(t("Verwijderen"))
            dele.setObjectName("danger")
            dele.clicked.connect(lambda: self.done(self.DELETE))
            btns.addWidget(dele)
        btns.addStretch(1)
        cancel = QPushButton(t("Annuleren"))
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        ok = QPushButton(ok_label or t("Plaatsen"))
        ok.setObjectName("primary")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        btns.addWidget(ok)
        body.addLayout(btns)
        root.addLayout(body)

        self._set_color(self._color)
        self._apply_font()
        self.edit.setFocus()

    def _bump(self, d):
        self._size = max(8, min(72, self._size + d))
        self._apply_font()

    def _set_color(self, col):
        self._color = col
        for c, sw in self._swatches:
            sw.setChecked(c.lower() == col.lower())
        self._apply_font()

    def _apply_font(self, *a):
        self.size_lbl.setText("%d pt" % self._size)
        color = self._color if self._color.lower() != "#ffffff" else "#10131a"
        weight = "bold" if self.b_bold.isChecked() else "normal"
        style = "italic" if self.b_italic.isChecked() else "normal"
        self.edit.setStyleSheet(
            "QPlainTextEdit#texteditarea{background:#ffffff;color:%s;"
            "font-size:%dpt;font-weight:%s;font-style:%s;"
            "border:1px solid #2c2c36;border-radius:6px;padding:10px;"
            "selection-background-color:%s;selection-color:#ffffff;}"
            % (color, self._size, weight, style, ACCENT))

    def values(self):
        return (self.edit.toPlainText().strip(), self._size,
                self.b_bold.isChecked(), self.b_italic.isChecked(), self._color)


class PageLabel(QLabel):
    pressed = pyqtSignal(int, float, float)
    moved = pyqtSignal(int, float, float)
    releasedAt = pyqtSignal(int, float, float)
    doubleClicked = pyqtSignal(int, float, float)

    def __init__(self, pno, zoom, parent=None):
        super().__init__(parent)
        self.pno = pno
        self.zoom = zoom
        self.setObjectName("canvas")

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            p = ev.position()
            self.pressed.emit(self.pno, p.x() / self.zoom, p.y() / self.zoom)
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.MouseButton.LeftButton:
            p = ev.position()
            self.moved.emit(self.pno, p.x() / self.zoom, p.y() / self.zoom)
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        p = ev.position()
        self.releasedAt.emit(self.pno, p.x() / self.zoom, p.y() / self.zoom)
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            p = ev.position()
            self.doubleClicked.emit(self.pno, p.x() / self.zoom, p.y() / self.zoom)
        super().mouseDoubleClickEvent(ev)


class TextOverlay(QLabel):
    """Toegevoegde tekst als sleepbare widget (toont vet/cursief/kleur/grootte).
    Slepen = verschuiven, dubbelklik = bewerken."""
    movedTo = pyqtSignal(object)
    editRequested = pyqtSignal(object)

    def __init__(self, item, zoom, parent=None):
        super().__init__(parent)
        self.item = dict(item)
        self.zoom = zoom
        self.setObjectName("textitem")
        self.setWordWrap(False)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("")
        self._press = None
        self._dragging = False
        self.apply_style()

    def apply_style(self):
        it = self.item
        f = self.font()
        f.setPixelSize(max(6, int(round(it["size"] * self.zoom))))
        f.setBold(bool(it["bold"]))
        f.setItalic(bool(it["italic"]))
        self.setFont(f)
        self.setStyleSheet("QLabel#textitem{color:%s;background:transparent;}"
                           % it.get("color", "#000000"))
        x0, y0, x1, y1 = it["rect"]
        w_px = max(20, int((x1 - x0) * self.zoom))
        self.setWordWrap(True)
        self.setFixedWidth(w_px)
        self.setText(it["text"])
        self.adjustSize()
        self.move(int(x0 * self.zoom), int(y0 * self.zoom))

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._press = ev.position()
            self._dragging = False
        ev.accept()

    def mouseMoveEvent(self, ev):
        if self._press is not None and (ev.buttons() & Qt.MouseButton.LeftButton):
            if not self._dragging:
                self._dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.raise_()
            delta = ev.position() - self._press
            self.move(int(self.x() + delta.x()), int(self.y() + delta.y()))
        ev.accept()

    def mouseReleaseEvent(self, ev):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if self._dragging:
            self.item["nx"] = max(0.0, self.x() / self.zoom)
            self.item["ny"] = max(0.0, self.y() / self.zoom)
            self.movedTo.emit(self)
        self._press = None
        self._dragging = False
        ev.accept()

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.editRequested.emit(self)
        ev.accept()


class PageView(QScrollArea):
    changed = pyqtSignal()
    pageChanged = pyqtSignal(int)
    hint = pyqtSignal(str)
    addFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setObjectName("pageview")
        self.container = QWidget()
        self.container.setObjectName("pagestack")
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(20, 20, 20, 20)
        self.vbox.setSpacing(18)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.setWidget(self.container)
        self.model = None
        self.zoom = 1.5
        self.text_mode = False
        self._drag = None
        self._labels = []
        self._overlays = []
        self._empty = QLabel("")
        self._empty.setObjectName("empty")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setMinimumSize(600, 400)
        self.vbox.addWidget(self._empty, 0, Qt.AlignmentFlag.AlignHCenter)
        self.verticalScrollBar().valueChanged.connect(
            lambda _=0: self.pageChanged.emit(self.current_page()))

    # ---- algemeen ----
    def set_model(self, model):
        self.model = model

    def set_empty_text(self, txt):
        self._empty.setText(txt)

    def set_text_mode(self, on):
        self.text_mode = bool(on)
        cur = (Qt.CursorShape.CrossCursor if self.text_mode
               else Qt.CursorShape.ArrowCursor)
        self.viewport().setCursor(cur)

    def _clear(self):
        for w in self._overlays:
            w.setParent(None)
            w.deleteLater()
        self._overlays = []
        for lbl in self._labels:
            self.vbox.removeWidget(lbl)
            lbl.setParent(None)
            lbl.deleteLater()
        self._labels = []

    # ---- alle pagina's renderen (doorlopend) ----
    def render_all(self):
        self._clear()
        if not self.model or not self.model.doc:
            self._empty.setVisible(True)
            return
        self._empty.setVisible(False)
        for pno in range(self.model.page_count):
            img, w, h = self.model.render(pno, self.zoom)
            lbl = PageLabel(pno, self.zoom, self.container)
            lbl.setPixmap(QPixmap.fromImage(img))
            lbl.setFixedSize(w, h)
            lbl.pressed.connect(self._on_press)
            self.vbox.addWidget(lbl, 0, Qt.AlignmentFlag.AlignHCenter)
            self._labels.append(lbl)
            self._place_fields(pno, lbl)
            self._place_text(pno, lbl)
        QApplication.processEvents()

    def rerender(self):
        sb = self.verticalScrollBar()
        ratio = (sb.value() / sb.maximum()) if sb.maximum() else 0.0
        self.render_all()
        QApplication.processEvents()
        sb = self.verticalScrollBar()
        sb.setValue(int(ratio * sb.maximum()))

    # behoud van oude naam zodat bestaande aanroepen blijven werken
    def render_page(self):
        self.render_all()

    def go_to_page(self, pno):
        if 0 <= pno < len(self._labels):
            y = self._labels[pno].pos().y()
            self.verticalScrollBar().setValue(max(0, y - 16))

    def current_page(self):
        if not self._labels:
            return 0
        mid = self.verticalScrollBar().value() + self.viewport().height() // 3
        best = 0
        for i, lbl in enumerate(self._labels):
            if lbl.pos().y() <= mid:
                best = i
            else:
                break
        return best

    # ---- velden plaatsen (per pagina) ----
    def _place_fields(self, pno, parent):
        z = self.zoom
        for fld in self.model.fields(pno):
            ft = fld["type"]
            if ft == TYPE_RADIO:
                self._make_radio(pno, fld, z, parent)
                continue
            x0, y0, x1, y1 = fld["rect"]
            geo = QRect(int(x0 * z), int(y0 * z),
                        max(16, int((x1 - x0) * z)), max(14, int((y1 - y0) * z)))
            name = fld["name"]
            if ft == TYPE_COMBO or ft == TYPE_LIST:
                cb = QComboBox(parent)
                cb.setObjectName("field")
                cb.addItems(fld.get("choices", []))
                val = fld.get("value")
                cur = None
                for disp, exp in fld.get("choice_pairs", []):
                    if val == disp or val == exp:
                        cur = disp
                        break
                if cur is not None:
                    cb.setCurrentText(cur)
                cb.setGeometry(geo)
                cb.currentTextChanged.connect(
                    lambda v, n=name, p=pno: self._on_choice(p, n, v))
                cb.show()
                self._overlays.append(cb)
            elif ft == TYPE_TEXT:
                le = QLineEdit(parent)
                le.setObjectName("field")
                le.setText(fld["value"] or "")
                le.setGeometry(geo)
                le.editingFinished.connect(
                    lambda n=name, w=le, p=pno: self._on_text(p, n, w.text()))
                le.show()
                self._overlays.append(le)
            elif ft == TYPE_CHECK:
                ck = QCheckBox(parent)
                ck.setObjectName("fieldcheck")
                on = fld.get("on", "Yes")
                ck.setChecked(fld["value"] not in ("Off", "", None))
                ck.setGeometry(geo)
                ck.toggled.connect(
                    lambda v, n=name, o=on, p=pno: self._on_check(p, n, o, v))
                ck.show()
                self._overlays.append(ck)

    def _make_radio(self, pno, grp, z, parent):
        name = grp["name"]
        cur = grp.get("value")
        for opt in grp["options"]:
            x0, y0, x1, y1 = opt["rect"]
            geo = QRect(int(x0 * z), int(y0 * z),
                        max(14, int((x1 - x0) * z)), max(14, int((y1 - y0) * z)))
            rb = QCheckBox(parent)
            rb.setObjectName("fieldradio")
            rb.setChecked(cur == opt["on"])
            rb.setGeometry(geo)
            rb.clicked.connect(lambda _=False, n=name, o=opt["on"], p=pno:
                               self._on_radio(p, n, o))
            rb.show()
            self._overlays.append(rb)

    # ---- tekst-overlays plaatsen ----
    def _place_text(self, pno, parent):
        for it in self.model.text_annots(pno):
            it = dict(it)
            it["pno"] = pno
            ov = TextOverlay(it, self.zoom, parent)
            ov.movedTo.connect(self._on_text_moved)
            ov.editRequested.connect(self._on_text_edit)
            ov.show()
            self._overlays.append(ov)

    # ---- klik op lege pagina (alleen in tekstmodus): nieuwe tekst plaatsen ----
    def _on_press(self, pno, x, y):
        if not self.model or not self.model.doc:
            return
        if self.text_mode:
            self._add_text_at(pno, x, y)

    def _on_text_moved(self, ov):
        self.model.move_text(ov.item["pno"], ov.item["xref"],
                             ov.item["nx"], ov.item["ny"])
        self.changed.emit()

    def _on_text_edit(self, ov):
        self._edit_annot(ov.item["pno"], ov.item)

    def _add_text_at(self, pno, x, y):
        dlg = TextEditorDialog(self, t("Tekst toevoegen"), "", 14,
                               ok_label=t("Plaatsen"))
        placed = False
        if dlg.exec() == QDialog.DialogCode.Accepted:
            text, size, bold, italic, color = dlg.values()
            if text:
                self.model.add_text(pno, x, y, text, size, bold, italic, color)
                self.changed.emit()
                self.rerender()
                placed = True
        # tekst plaatsen is eenmalig: knop weer uit
        self.addFinished.emit()
        return placed

    def _edit_annot(self, pno, hit):
        dlg = TextEditorDialog(self, t("Tekst bewerken"), hit["text"],
                               hit.get("size", 14), ok_label=t("Opslaan"),
                               allow_delete=True, bold=hit.get("bold", False),
                               italic=hit.get("italic", False),
                               color=hit.get("color", "#000000"))
        res = dlg.exec()
        if res == TextEditorDialog.DELETE:
            self.model.delete_text(pno, hit["xref"])
        elif res == QDialog.DialogCode.Accepted:
            text, size, bold, italic, color = dlg.values()
            if text == "":
                self.model.delete_text(pno, hit["xref"])
            else:
                self.model.edit_text(pno, hit["xref"], text, size, bold,
                                     italic, color)
        else:
            return
        self.changed.emit()
        self.rerender()

    # ---- veld-wijzigingen ----
    def _on_choice(self, pno, name, val):
        self.model.set_choice(pno, name, val)
        self.changed.emit()

    def _on_text(self, pno, name, val):
        self.model.set_text(pno, name, val)
        self.changed.emit()

    def _on_check(self, pno, name, on, val):
        self.model.set_check(pno, name, on, val)
        self.changed.emit()

    def _on_radio(self, pno, name, on_state):
        self.model.set_radio(pno, name, on_state)
        self.changed.emit()
        self.rerender()


# ---------------------------------------------------------------------------
# Snelgids
# ---------------------------------------------------------------------------
GUIDE_NL = """DraveForms - Snelgids

DraveForms opent PDF's en laat je invulbare formulieren invullen:
dropdowns (keuzelijsten), tekstvakken en vinkjes - ook als ze normaal
alleen in Adobe werken. Je hoeft Adobe dus niet meer.

Aan de slag
- Klik op 'Openen' en kies een PDF.
- Alle pagina's staan nu onder elkaar: scroll gewoon door het hele
  document. 'Vorige'/'Volgende' en het paginanummer springen naar een pagina.
- Velden verschijnen automatisch op de pagina. Klik op een dropdown en
  kies; typ in een tekstvak; klik een vinkje aan.
- Zoom met + en - (of 'Passend' voor paginabreedte).

Tekst toevoegen aan een PDF
- Klik op 'Tekst toevoegen' en klik daarna op de plek in de pagina. Er opent een
  tekst-editor: typ je tekst (meerdere regels mag) en kies grootte (A- / A+),
  vet (B), cursief (I) en een kleur.
- Plaatsen is eenmalig: na het plaatsen springt de knop vanzelf weer uit. Wil je
  nog een stuk tekst? Klik opnieuw op 'Tekst toevoegen'.
- Verschuiven: pak geplaatste tekst met de muis vast en sleep 'm naar de plek.
- Bewerken: DUBBELKLIK op de tekst (tekst, grootte, vet/cursief, kleur), of klik
  in dat venster op 'Verwijderen'.
- Grootte en kleur zijn in elke PDF-lezer zichtbaar; vet en cursief worden in
  DraveForms getoond.

Opslaan
- 'Opslaan' bewaart in hetzelfde bestand.
- 'Opslaan als...' maakt een nieuwe kopie.
De ingevulde waarden en toegevoegde tekst blijven zichtbaar in elke
PDF-lezer, niet alleen in DraveForms.

Over XFA
Sommige formulieren gebruiken Adobe's XFA-techniek. DraveForms toont en
vult de standaardlaag (AcroForm) als die er is; puur-dynamische XFA kan
afwijken. Je krijgt een melding bovenin als een PDF XFA gebruikt.

Vragen of een tip? service@dravenlock.nl
"""

GUIDE_EN = """DraveForms - Quick guide

DraveForms opens PDFs and lets you fill interactive forms: dropdowns,
text boxes and checkboxes - even ones that normally only work in Adobe.
So you can uninstall Adobe.

Getting started
- Click 'Open' and pick a PDF.
- All pages now appear stacked: just scroll through the whole document.
  'Previous'/'Next' and the page number jump to a page.
- Fields appear on the page automatically. Click a dropdown and choose;
  type in a text box; tick a checkbox.
- Zoom with + and - (or 'Fit width').

Add text to a PDF
- Click 'Add text', then click where you want it on the page. A text editor
  opens: type your text (multiple lines allowed) and choose size (A- / A+),
  bold (B), italic (I) and a color.
- Placing is one-shot: after placing, the button pops out again. Want another
  piece of text? Click 'Add text' again.
- Move: grab placed text with the mouse and drag it to the spot.
- Edit: DOUBLE-CLICK the text (text, size, bold/italic, color), or click
  'Delete' in that window.
- Size and color show in any PDF reader; bold and italic are shown in DraveForms.

Saving
- 'Save' writes to the same file.
- 'Save as...' makes a new copy.
Filled values and added text stay visible in any PDF reader, not just
DraveForms.

About XFA
Some forms use Adobe's XFA technology. DraveForms shows and fills the
standard (AcroForm) layer if present; purely dynamic XFA may differ.
You'll see a notice at the top if a PDF uses XFA.

Questions or feedback? service@dravenlock.nl
"""


class GuideDialog(QDialog):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.setWindowTitle(t("snelgids_titel", lang))
        self.resize(560, 520)
        lay = QVBoxLayout(self)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setPlainText(GUIDE_NL if lang == "nl" else GUIDE_EN)
        box.setObjectName("guide")
        lay.addWidget(box)
        row = QHBoxLayout()
        donate = QPushButton("\u2665 " + t("Donatie", lang))
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        row.addWidget(donate)
        row.addStretch(1)
        close = QPushButton(t("Sluiten", lang))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


# ---------------------------------------------------------------------------
# Instellingen
# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(t("Instellingen\u2026", lang))
        self.resize(360, 160)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (OS)", lang), "")
        self.langbox.addItem(t("Nederlands", lang), "nl")
        self.langbox.addItem(t("Engels", lang), "en")
        self.langbox.setCurrentIndex({"": 0, "nl": 1, "en": 2}.get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)
        hint = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang)
                      if lang == "nl" else "Some settings apply after a restart.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)

    def result_cfg(self):
        self.cfg["lang"] = self.langbox.currentData()
        return self.cfg


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class DraveForms(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.lang = _LANG
        self.model = PdfModel()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1040, 760)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())
        outer.addWidget(self._toolbar())
        self.notice = QLabel("")
        self.notice.setObjectName("notice")
        self.notice.setVisible(False)
        self.notice.setWordWrap(True)
        outer.addWidget(self.notice)

        self.view = PageView()
        self.view.changed.connect(self._on_changed)
        self.view.pageChanged.connect(self._on_view_page)
        self.view.hint.connect(lambda m: self.statusBar().showMessage(m, 5000))
        self.view.addFinished.connect(lambda: self.b_text.setChecked(False))
        outer.addWidget(self.view, 1)

        self.view.set_empty_text(t("Open een PDF om te beginnen", self.lang))

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.field_count = QLabel("")
        self.field_count.setObjectName("muted")
        sb.addWidget(self.field_count)
        sb.addPermanentWidget(QLabel("v" + APP_VERSION))
        donate = QToolButton()
        donate.setText("\u2665 " + t("Donatie", self.lang))
        donate.setObjectName("donate")
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        sb.addPermanentWidget(donate)

        self._update_actions()

    # ---- UI-opbouw ----
    def _header(self):
        w = QWidget()
        w.setObjectName("header")
        w.setFixedHeight(56)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(30))
        lay.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("ver")
        lay.addWidget(ver)
        lay.addStretch(1)
        for label, slot in [(t("Instellingen\u2026", self.lang), self._settings),
                            (t("Snelgids", self.lang), self._guide),
                            (t("Over", self.lang), self._about)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, s=slot: s())
            lay.addWidget(b)
        return w

    def _toolbar(self):
        w = QWidget()
        w.setObjectName("toolbar")
        w.setFixedHeight(48)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)

        self.b_open = QPushButton(t("Openen", self.lang))
        self.b_open.setObjectName("primary")
        self.b_open.clicked.connect(self.open_pdf)
        lay.addWidget(self.b_open)

        self.b_save = QPushButton(t("Opslaan", self.lang))
        self.b_save.clicked.connect(self.save_pdf)
        lay.addWidget(self.b_save)

        self.b_saveas = QPushButton(t("Opslaan als\u2026", self.lang))
        self.b_saveas.clicked.connect(self.save_pdf_as)
        lay.addWidget(self.b_saveas)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("sep")
        lay.addWidget(sep)

        self.b_prev = QToolButton()
        self.b_prev.setText("\u25c0")
        self.b_prev.clicked.connect(self.prev_page)
        lay.addWidget(self.b_prev)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self._goto_spin)
        lay.addWidget(self.page_spin)
        self.page_total = QLabel("/ 0")
        self.page_total.setObjectName("muted")
        lay.addWidget(self.page_total)

        self.b_next = QToolButton()
        self.b_next.setText("\u25b6")
        self.b_next.clicked.connect(self.next_page)
        lay.addWidget(self.b_next)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setObjectName("sep")
        lay.addWidget(sep2)

        self.b_zout = QToolButton()
        self.b_zout.setText("\u2212")
        self.b_zout.clicked.connect(lambda: self.set_zoom(self.view.zoom - 0.25))
        lay.addWidget(self.b_zout)
        self.zoom_lbl = QLabel("150%")
        self.zoom_lbl.setObjectName("muted")
        lay.addWidget(self.zoom_lbl)
        self.b_zin = QToolButton()
        self.b_zin.setText("+")
        self.b_zin.clicked.connect(lambda: self.set_zoom(self.view.zoom + 0.25))
        lay.addWidget(self.b_zin)
        self.b_fit = QPushButton(t("Passend", self.lang))
        self.b_fit.clicked.connect(self.fit_width)
        lay.addWidget(self.b_fit)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.VLine)
        sep3.setObjectName("sep")
        lay.addWidget(sep3)

        self.b_text = QPushButton("\u270e " + t("Tekst toevoegen", self.lang))
        self.b_text.setCheckable(True)
        self.b_text.setObjectName("texttoggle")
        self.b_text.toggled.connect(self._toggle_text_mode)
        lay.addWidget(self.b_text)

        lay.addStretch(1)
        return w

    # ---- acties ----
    def open_pdf(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, t("Openen", self.lang), "",
                t("PDF-bestanden (*.pdf)", self.lang) + ";;" + t("Alle bestanden (*)", self.lang))
        if not path:
            return
        try:
            self.model.open(path)
        except Exception as e:
            QMessageBox.warning(self, t("Kon niet openen", self.lang), str(e))
            return
        self.view.set_model(self.model)
        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(max(1, self.model.page_count))
        self.page_spin.setValue(1)
        self.page_spin.blockSignals(False)
        self.page_total.setText("/ %d" % self.model.page_count)
        self._show_xfa_notice()
        self.view.render_all()
        self.view.go_to_page(0)
        self.setWindowTitle("%s \u2014 %s" % (APP_NAME, os.path.basename(path)))
        self._update_field_count()
        self._update_actions()

    def _show_xfa_notice(self):
        if self.model.is_xfa():
            self.notice.setText("\u26a0 %s. %s"
                                % (t("Dit formulier gebruikt XFA", self.lang),
                                   t("xfa_uitleg", self.lang)))
            self.notice.setVisible(True)
        else:
            self.notice.setVisible(False)

    def save_pdf(self):
        if not self.model.doc:
            return
        try:
            self.model.save(None)
            self.statusBar().showMessage(t("Opgeslagen", self.lang), 4000)
            QMessageBox.information(
                self, t("Opgeslagen", self.lang),
                "%s\n\n%s" % (t("Het bestand is opgeslagen.", self.lang),
                              os.path.basename(self.model.path or "")))
        except Exception as e:
            QMessageBox.warning(self, t("Kon niet opslaan", self.lang), str(e))
        self._update_actions()

    def save_pdf_as(self):
        if not self.model.doc:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t("Opslaan als\u2026", self.lang),
            self.model.path or "", t("PDF-bestanden (*.pdf)", self.lang))
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            self.model.save(path)
            self.statusBar().showMessage("%s %s" % (t("Opgeslagen als", self.lang),
                                                    os.path.basename(path)), 5000)
            self.setWindowTitle("%s \u2014 %s" % (APP_NAME, os.path.basename(path)))
            self.view.render_all()
            QMessageBox.information(
                self, t("Opgeslagen", self.lang),
                "%s\n\n%s" % (t("Het bestand is opgeslagen.", self.lang),
                              os.path.basename(path)))
        except Exception as e:
            QMessageBox.warning(self, t("Kon niet opslaan", self.lang), str(e))
        self._update_actions()

    def prev_page(self):
        if self.model.doc:
            self.page_spin.setValue(max(1, self.view.current_page()))

    def next_page(self):
        if self.model.doc:
            self.page_spin.setValue(min(self.model.page_count, self.view.current_page() + 2))

    def _goto_spin(self, val):
        if not self.model.doc:
            return
        self.view.go_to_page(max(0, min(self.model.page_count - 1, val - 1)))
        self._update_actions()

    def _on_view_page(self, pno):
        # spinner meelopen met scrollen, zonder lus
        if not self.model.doc:
            return
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(pno + 1)
        self.page_spin.blockSignals(False)
        self._update_actions()

    def _toggle_text_mode(self, on):
        self.view.set_text_mode(on)
        if on:
            self.statusBar().showMessage(
                t("Klik op de pagina waar je tekst wilt plaatsen.", self.lang), 6000)

    def set_zoom(self, z):
        z = max(0.5, min(4.0, round(z, 2)))
        self.view.zoom = z
        self.zoom_lbl.setText("%d%%" % int(z * 100))
        if self.model.doc:
            self.view.rerender()

    def fit_width(self):
        if not self.model.doc:
            return
        page = self.model.doc[self.view.current_page()]
        pw = page.rect.width or 600
        avail = self.view.viewport().width() - 48
        self.set_zoom(avail / pw)

    def _on_changed(self):
        self._update_actions()

    def _update_field_count(self):
        if not self.model.doc:
            self.field_count.setText("")
            return
        n = self.model.field_count_total()
        if n:
            self.field_count.setText("%d %s" % (n, t("velden", self.lang)))
        else:
            self.field_count.setText(t("Geen invulvelden", self.lang))

    def _update_actions(self):
        has = self.model.doc is not None
        for b in (self.b_save, self.b_saveas, self.b_prev, self.b_next,
                  self.b_fit, self.b_zin, self.b_zout, self.page_spin, self.b_text):
            b.setEnabled(has)
        if has:
            cur = self.view.current_page()
            self.b_prev.setEnabled(cur > 0)
            self.b_next.setEnabled(cur < self.model.page_count - 1)
        title = APP_NAME
        if self.model.path:
            mark = "*" if self.model.dirty else ""
            title = "%s \u2014 %s%s" % (APP_NAME, os.path.basename(self.model.path), mark)
        self.setWindowTitle(title)

    def _settings(self):
        dlg = SettingsDialog(self, dict(self.cfg), self.lang)
        if dlg.exec():
            self.cfg = dlg.result_cfg()
            save_config(self.cfg)

    def _guide(self):
        GuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(
            self, t("Over", self.lang),
            "%s v%s\n\nPDF-lezer met invulbare formulieren.\nDravenlock\n%s\n%s"
            % (APP_NAME, APP_VERSION, SUPPORT_MAIL, DONATE_URL))

    def closeEvent(self, ev):
        if self.model.doc and self.model.dirty:
            r = QMessageBox.question(
                self, t("Niet-opgeslagen wijzigingen", self.lang),
                t("Wil je de wijzigingen opslaan?", self.lang),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Save:
                self.save_pdf()
            elif r == QMessageBox.StandardButton.Cancel:
                ev.ignore()
                return
        ev.accept()


QSS = """
* { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid #23232b; }
#title { font-size: 19px; font-weight: 700; color: %(silver)s; }
#ver { color: %(mute)s; font-size: 12px; }
#toolbar { background: %(bg)s; border-bottom: 1px solid #23232b; }
#notice { background: #2a2410; color: %(warn)s; padding: 8px 14px;
          border-bottom: 1px solid #3a3217; }
QPushButton { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 7px 13px; color: %(silver)s; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton#primary { background: %(accent)s; color: #08131f; font-weight: 700;
                      border: none; }
QPushButton#primary:hover { background: #87b6e3; }
QToolButton { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 5px 9px; color: %(silver)s; min-width: 20px; }
QToolButton:hover { border-color: %(accent)s; }
QToolButton#donate { border: none; background: transparent; color: %(accent)s; }
QSpinBox { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 6px;
           padding: 3px 6px; min-width: 48px; }
QFrame#sep { color: #2c2c36; }
#muted, #hint { color: %(mute)s; font-size: 12px; }
#empty { color: %(mute)s; font-size: 16px; }
QScrollArea#pageview { background: #4a4a52; border: none; }
QWidget#pagestack { background: #4a4a52; }
QLabel#canvas { background: #ffffff; }
QPushButton#texttoggle:checked { background: %(accent)s; color: #08131f;
                                 font-weight: 700; border: none; }
QLabel#dragghost { background: rgba(111,163,214,0.30); color: #10131a;
                   border: 1px dashed %(accent)s; border-radius: 3px; }
QDialog#texteditor { background: %(bg)s; }
QWidget#edbar { background: %(panel)s; border-bottom: 1px solid #2c2c36; }
#edcap { color: %(silver)s; font-weight: 700; }
QToolButton#edtool { background: %(panel)s; border: 1px solid #2c2c36;
    border-radius: 6px; padding: 4px 10px; color: %(silver)s;
    font-weight: 700; min-width: 28px; }
QToolButton#edtool:hover { border-color: %(accent)s; }
QToolButton#edstyle { background: %(panel)s; border: 1px solid #2c2c36;
    border-radius: 6px; padding: 4px 10px; color: %(silver)s; min-width: 24px; }
QToolButton#edstyle:hover { border-color: %(accent)s; }
QToolButton#edstyle:checked { background: %(accent)s; color: #08131f;
    font-weight: 700; border: none; }
#sizereadout { color: %(accent)s; font-weight: 700; }
QPlainTextEdit#texteditarea { background: #ffffff; color: #10131a;
    border: 1px solid #2c2c36; border-radius: 6px; padding: 10px;
    selection-background-color: %(accent)s; selection-color: #ffffff; }
QPushButton#danger { background: #7a2230; color: #fff; border: none; }
QPushButton#danger:hover { background: #9a2c3d; }
QPlainTextEdit#guide { background: %(panel)s; border: 1px solid #2c2c36;
                       border-radius: 8px; padding: 10px; }
QDialog { background: %(bg)s; }
/* Overlay-velden op de (witte) pagina: licht en leesbaar */
QComboBox#field, QLineEdit#field {
    background: rgba(232,240,250,0.96); color: #10131a;
    border: 1px solid %(accent)s; border-radius: 3px; padding: 0px 4px;
    font-size: 13px;
}
QComboBox#field QAbstractItemView { background: #ffffff; color: #10131a;
    selection-background-color: %(accent)s; selection-color: #ffffff; }
QCheckBox#fieldcheck, QCheckBox#fieldradio { background: transparent; }
QCheckBox#fieldcheck::indicator, QCheckBox#fieldradio::indicator {
    width: 15px; height: 15px; border: 2px solid %(accent)s;
    border-radius: 3px; background: rgba(236,243,252,0.95); }
QCheckBox#fieldradio::indicator { border-radius: 8px; }
QCheckBox#fieldcheck::indicator:checked, QCheckBox#fieldradio::indicator:checked {
    background: %(accent)s; }
""" % {"bg": BG, "panel": PANEL, "silver": SILVER, "mute": MUTE,
       "accent": ACCENT, "warn": WARN}


def _install_excepthook():
    import traceback

    def hook(exctype, value, tb):
        msg = "".join(traceback.format_exception(exctype, value, tb))
        try:
            with open(os.path.join(_app_dir(), "draveforms-fout.txt"),
                      "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "DraveForms - fout",
                                     "Er ging iets mis bij het starten:\n\n"
                                     + msg[-1500:]
                                     + "\n\n(Ook opgeslagen in draveforms-fout.txt)")
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = hook


def main():
    global _LANG
    _install_excepthook()
    app = QApplication(sys.argv)
    try:
        cfg = load_config()
        _LANG = detect_lang(cfg)
        app.setStyleSheet(QSS)
        win = DraveForms(cfg)
        win.show()
        if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".pdf"):
            win.open_pdf(sys.argv[1])
    except Exception:
        sys.excepthook(*sys.exc_info())
        return
    try:  # Dravenlock: stille update-check (uit te zetten; Ctrl+Shift+U = met de hand)
        import drave_update
        drave_update.start(win, 'DraveForms', APP_VERSION)
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
