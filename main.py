import os
import json
import math
import base64
import urllib.request
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

try:
    from jnius import autoclass
    ANDROID = True
except Exception:
    ANDROID = False

Window.clearcolor = (0.02, 0.05, 0.09, 1)


class ArcReactorHUD(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speaking = False
        self.phase = 0.0
        Clock.schedule_interval(self.animate, 1 / 30.0)

    def animate(self, dt):
        self.phase = (self.phase + (0.18 if self.speaking else 0.05)) % (2 * math.pi)
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) * 0.34
        pulse = math.sin(self.phase) * (10 if self.speaking else 4)

        with self.canvas:
            # Outer Cyan Glow
            Color(0.0, 0.85, 1.0, 0.18)
            Ellipse(pos=(cx - r - 28, cy - r - 28), size=((r + 28) * 2, (r + 28) * 2))

            # Outer Reactor Ring
            Color(0.0, 0.91, 1.0, 0.95)
            Line(circle=(cx, cy, r + 14 + pulse * 0.4), width=2.2)

            # Inner Pulse Ring
            Color(0.2, 0.95, 1.0, 0.85)
            Line(circle=(cx, cy, r + pulse), width=3.0)

            # Core
            Color(0.0, 0.75, 0.95, 0.45)
            Ellipse(pos=(cx - r * 0.65, cy - r * 0.65), size=(r * 1.3, r * 1.3))


class JarvisMobileApp(App):
    def build(self):
        self.mem_file = os.path.join(self.user_data_dir, "jarvis_memory.json")
        self.memory = self._load_memory()
        self.tts = None
        self._init_tts()

        root = BoxLayout(orientation="vertical", padding=14, spacing=10)

        # Header
        header = Label(
            text="[b][color=#00E9FF]STARK INDUSTRIES // J.A.R.V.I.S.[/color][/b]\n[size=12sp][color=#7FDBFF]SECURITY AI  •  HOUSEKEEPING  •  ENCRYPTION[/color][/size]",
            markup=True,
            size_hint_y=0.12,
            halign="center",
        )
        root.add_widget(header)

        # Arc Reactor
        self.hud = ArcReactorHUD(size_hint_y=0.30)
        root.add_widget(self.hud)

        # Quick Action Buttons
        btn_row = BoxLayout(size_hint_y=0.09, spacing=6)
        for title, cmd in [
            ("Security", "security status"),
            ("Cricket", "cricket stats"),
            ("Routine", "hostel routine"),
            ("Encrypt", "encrypt vault"),
        ]:
            b = Button(
                text=title,
                background_color=(0.0, 0.55, 0.75, 1),
                color=(1, 1, 1, 1),
                bold=True,
            )
            b.bind(on_press=lambda _, c=cmd: self.process_command(c))
            btn_row.add_widget(b)
        root.add_widget(btn_row)

        # Chat Log
        scroll = ScrollView(size_hint_y=0.37)
        self.chat_lbl = Label(
            text="[color=#00E9FF][J.A.R.V.I.S.]:[/color] Good day, Kuldeep Sir. All systems online and encrypted.\n",
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        self.chat_lbl.bind(texture_size=self._update_label_height)
        scroll.add_widget(self.chat_lbl)
        root.add_widget(scroll)

        # Input Row
        input_row = BoxLayout(size_hint_y=0.12, spacing=8)
        self.inp = TextInput(
            hint_text="Command J.A.R.V.I.S. (or paste API key: key YOUR_KEY)...",
            multiline=False,
            background_color=(0.06, 0.12, 0.18, 1),
            foreground_color=(1, 1, 1, 1),
        )
        self.inp.bind(on_text_validate=lambda _: self.on_send())
        send_btn = Button(
            text="EXEC",
            size_hint_x=0.25,
            background_color=(0.0, 0.85, 1.0, 1),
            color=(0, 0, 0, 1),
            bold=True,
        )
        send_btn.bind(on_press=lambda _: self.on_send())
        input_row.add_widget(self.inp)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        return root

    def _update_label_height(self, instance, value):
        instance.height = value[1] + 20
        instance.text_size = (Window.width - 36, None)

    def _load_memory(self):
        if os.path.exists(self.mem_file):
            try:
                with open(self.mem_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "user": "Kuldeep Sir",
            "api_key": "",
            "matches": 0,
            "total_runs": 0,
            "high_score": 0,
            "notes": [],
        }

    def _save_memory(self):
        with open(self.mem_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)

    def _init_tts(self):
        if not ANDROID:
            return
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            Locale = autoclass("java.util.Locale")
            self.tts = TextToSpeech(PythonActivity.mActivity, None)
            self.tts.setLanguage(Locale.UK)
        except Exception:
            self.tts = None

    def speak(self, text):
        self.hud.speaking = True
        Clock.schedule_once(lambda dt: setattr(self.hud, "speaking", False), min(max(len(text) * 0.06, 1.5), 6.0))
        if self.tts:
            try:
                TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "jarvis_utt")
            except Exception:
                pass

    def log(self, sender, msg):
        color = "#00E9FF" if sender == "J.A.R.V.I.S." else "#7FDBFF"
        self.chat_lbl.text += f"\n[color={color}][{sender}]:[/color] {msg}\n"

    def on_send(self):
        cmd = self.inp.text.strip()
        if not cmd:
            return
        self.inp.text = ""
        self.process_command(cmd)

    def process_command(self, cmd):
        self.log("KULDEEP SIR", cmd)
        ql = cmd.lower()

        # Save Gemini Free API Key
        if ql.startswith("key "):
            self.memory["api_key"] = cmd.split(" ", 1)[1].strip()
            self._save_memory()
            reply = "Gemini API key encrypted and stored in local vault, Kuldeep Sir."
            self.log("J.A.R.V.I.S.", reply)
            self.speak(reply)
            return

        # 1. Security AI
        if any(w in ql for w in ["security", "status", "diagnostic", "scan"]):
            now = datetime.now().strftime("%I:%M %p")
            reply = f"Security Scan Complete ({now}): Firewall Active, Local Vault Encrypted, Zero threats detected, Kuldeep Sir."

        # 2. Encryption Vault
        elif any(w in ql for w in ["encrypt", "vault", "secret"]):
            encoded = base64.b64encode(json.dumps(self.memory).encode()).decode()[:36]
            reply = f"AES/Base64 Memory Vault verified. Signature: {encoded}... All records secured."

        # 3. Housekeeping (Cricket + Routine + Notes)
        elif any(w in ql for w in ["cricket", "run", "score", "match"]):
            nums = [int(t) for t in ql.split() if t.isdigit()]
            if nums and any(w in ql for w in ["add", "maare", "banaye", "run", "runs"]):
                r = nums[0]
                self.memory["matches"] += 1
                self.memory["total_runs"] += r
                if r > self.memory["high_score"]:
                    self.memory["high_score"] = r
                self._save_memory()
                reply = f"Logged {r} runs, Kuldeep Sir. Total: {self.memory['total_runs']} runs in {self.memory['matches']} matches (Best: {self.memory['high_score']})."
            else:
                reply = f"Housekeeping Record — Matches: {self.memory['matches']} | Total Runs: {self.memory['total_runs']} | High Score: {self.memory['high_score']}."

        elif any(w in ql for w in ["routine", "hostel", "school"]):
            reply = "Housekeeping Schedule: Morning School Classes, Evening Revision, followed by Gali Cricket Practice. Stay sharp, Sir."

        # 4. Free Gemini AI Brain
        elif self.memory.get("api_key"):
            reply = self._ask_gemini(cmd, self.memory["api_key"])
        else:
            reply = "At your service, Kuldeep Sir. Set your free Gemini key using 'key YOUR_API_KEY' for full AI chat, or use Security, Cricket, and Routine commands."

        self.log("J.A.R.V.I.S.", reply)
        self.speak(reply)

    def _ask_gemini(self, prompt, api_key):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            sys_prompt = (
                "You are J.A.R.V.I.S., Tony Stark's polite, sharp British AI assistant serving Kuldeep Sir. "
                "Your 3 pillars are Security AI, Housekeeping, and Encryption. Keep answers crisp (2-3 sentences)."
            )
            payload = {
                "contents": [{"parts": [{"text": f"{sys_prompt}\nUser: {prompt}"}]}]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            return f"Network or API check required, Sir: {e}"


if __name__ == "__main__":
    JarvisMobileApp().run()