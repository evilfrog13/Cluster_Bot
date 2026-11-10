#!/usr/bin/env python3
"""
Cluster Bot v7.0
Rewritten to produce large covering polygons matching your examples
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import cv2
import numpy as np
import pyautogui
from mss import MSS
from pynput import keyboard, mouse
from PIL import Image, ImageTk
import sys
import json
import os

VERSION = "7.0"

MAX_POINTS = 8
CLICK_DELAY = 0.36
MOVE_DURATION = 0.40
AFTER_POLYGON_WAIT = 0.70
AFTER_ALL_POLYGONS_WAIT = 1.3
AFTER_SUBMIT_WAIT = 2.0
BETWEEN_CONTINUES = 1.7

CONFIG_FILE = os.path.expanduser("~/.cluster_bot_config.json")

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.03


class ClusterBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Cluster Bot v{VERSION}")
        self.root.geometry("960x850")
        self.root.resizable(True, True)
        self.root.attributes("-topmost", True)

        self.region = None
        self.button_pos = None
        self.running = False
        self.selecting_plot = False
        self.selecting_button = False
        self.click_count = 0
        self.temp_points = []
        self.max_loops = tk.IntVar(value=30)

        self.sensitivity = tk.DoubleVar(value=0.40)
        self.min_size = tk.IntVar(value=2200)
        self.separation = tk.IntVar(value=55)

        self.live_preview = tk.BooleanVar(value=True)
        self.preview_photo = None

        self.load_config()
        self.setup_ui()
        self.setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    if "button_pos" in data and data["button_pos"]:
                        self.button_pos = tuple(data["button_pos"])
            except Exception:
                pass

    def save_config(self):
        data = {}
        if self.button_pos:
            data["button_pos"] = list(self.button_pos)
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def setup_ui(self):
        left = ttk.Frame(self.root, padding=10)
        left.pack(side="left", fill="y")

        ttk.Label(left, text=f"Cluster Bot v{VERSION}", font=("Segoe UI", 15, "bold")).pack(pady=(0, 8))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(left, textvariable=self.status_var, wraplength=280, foreground="#0055aa").pack(pady=3)

        self.region_var = tk.StringVar(value="Plot area: not set")
        ttk.Label(left, textvariable=self.region_var).pack(pady=1)

        self.button_var = tk.StringVar(
            value=f"Submit button: {self.button_pos}" if self.button_pos else "Submit button: NOT SET"
        )
        ttk.Label(left, textvariable=self.button_var).pack(pady=1)

        ttk.Separator(left).pack(fill="x", pady=10)
        ttk.Label(left, text="Detection Controls", font=("Segoe UI", 11, "bold")).pack()

        f1 = ttk.Frame(left)
        f1.pack(fill="x", pady=4)
        ttk.Label(f1, text="Sensitivity (lower = more clusters)").pack(anchor="w")
        scale1 = ttk.Scale(f1, from_=0.10, to=0.90, variable=self.sensitivity, orient="horizontal")
        scale1.pack(fill="x")
        scale1.bind("<ButtonRelease-1>", self.on_slider_release)

        f2 = ttk.Frame(left)
        f2.pack(fill="x", pady=4)
        ttk.Label(f2, text="Minimum cluster size").pack(anchor="w")
        scale2 = ttk.Scale(f2, from_=800, to=7000, variable=self.min_size, orient="horizontal")
        scale2.pack(fill="x")
        scale2.bind("<ButtonRelease-1>", self.on_slider_release)

        f3 = ttk.Frame(left)
        f3.pack(fill="x", pady=4)
        ttk.Label(f3, text="Separation (higher = fewer clusters)").pack(anchor="w")
        scale3 = ttk.Scale(f3, from_=20, to=130, variable=self.separation, orient="horizontal")
        scale3.pack(fill="x")
        scale3.bind("<ButtonRelease-1>", self.on_slider_release)

        ttk.Checkbutton(left, text="Live Preview", variable=self.live_preview).pack(anchor="w", pady=8)

        ttk.Separator(left).pack(fill="x", pady=8)

        loop_frame = ttk.Frame(left)
        loop_frame.pack(pady=4)
        ttk.Label(loop_frame, text="Loops:").pack(side="left", padx=(0, 6))
        self.loop_spin = ttk.Spinbox(loop_frame, from_=1, to=9999, width=6, textvariable=self.max_loops)
        self.loop_spin.pack(side="left")

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=10)

        self.btn_plot = ttk.Button(btn_frame, text="F1 - Select Plot Area", command=self.start_select_plot, width=22)
        self.btn_plot.pack(pady=3)

        self.btn_button = ttk.Button(btn_frame, text="F3 - Select Submit Button", command=self.start_select_button, width=22)
        self.btn_button.pack(pady=3)

        self.btn_toggle = ttk.Button(btn_frame, text="F2 - Start / Stop", command=self.toggle_run, state="disabled", width=22)
        self.btn_toggle.pack(pady=3)

        self.btn_test = ttk.Button(btn_frame, text="TEST Submit Button", command=self.test_button_click, width=22)
        self.btn_test.pack(pady=3)

        self.btn_preview = ttk.Button(btn_frame, text="Manual Preview", command=self.preview_clusters, width=22)
        self.btn_preview.pack(pady=3)

        info = (
            "v7.0 – Large covering polygons\n"
            "matching your example style.\n\n"
            "Recommended:\n"
            "• Sensitivity 0.30 – 0.50\n"
            "• Min Size 1800 – 3500\n"
            "• Separation 45 – 70"
        )
        ttk.Label(left, text=info, justify="left").pack(pady=10)

        ttk.Label(left, text="Emergency stop: mouse to top-left corner",
                  font=("Segoe UI", 8), foreground="#666").pack(side="bottom")

        right = ttk.Frame(self.root, padding=8)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(right, text="Live Preview", font=("Segoe UI", 11, "bold")).pack()
        self.preview_label = ttk.Label(right, text="Select the plot area with F1")
        self.preview_label.pack(fill="both", expand=True)

        self.update_start_button_state()

    def on_slider_release(self, event=None):
        if self.live_preview.get() and self.region is not None:
            self.root.after(50, self.update_live_preview)

    def update_live_preview(self):
        if not self.region:
            return
        try:
            img = self.grab_plot()
            polygons = self.detect_clusters(img)

            preview = img.copy()
            colors = [(0, 255, 255), (0, 255, 0), (255, 255, 0), (255, 0, 255), (0, 165, 255)]

            for i, pts in enumerate(polygons):
                color = colors[i % len(colors)]
                cv2.polylines(preview, [pts], True, color, 2)
                for p in pts:
                    cv2.circle(preview, tuple(p), 3, color, -1)

            text = f"S:{self.sensitivity.get():.2f}  Size:{int(self.min_size.get())}  Sep:{int(self.separation.get())}  → {len(polygons)}"
            cv2.putText(preview, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

            preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            h, w = preview_rgb.shape[:2]
            scale = min(560 / w, 560 / h, 1.0)
            new_w, new_h = int(w * scale), int(h * scale)
            preview_rgb = cv2.resize(preview_rgb, (new_w, new_h))

            self.preview_photo = ImageTk.PhotoImage(Image.fromarray(preview_rgb))
            self.preview_label.configure(image=self.preview_photo, text="")
            self.status_var.set(f"Preview – {len(polygons)} clusters")
        except Exception as e:
            print("Preview error:", e)
            self.status_var.set(f"Error: {e}")

    def update_start_button_state(self):
        if self.region and self.button_pos:
            self.btn_toggle.config(state="normal")
            if not self.running:
                self.status_var.set("Ready – Press F2")
        else:
            self.btn_toggle.config(state="disabled")

    def setup_hotkeys(self):
        def on_press(key):
            try:
                if key == keyboard.Key.f1:
                    self.root.after(0, self.start_select_plot)
                elif key == keyboard.Key.f2:
                    self.root.after(0, self.toggle_run)
                elif key == keyboard.Key.f3:
                    self.root.after(0, self.start_select_button)
            except Exception:
                pass
        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()

    def start_select_plot(self):
        if self.running:
            return
        self.selecting_plot = True
        self.selecting_button = False
        self.click_count = 0
        self.temp_points = []
        self.status_var.set("F1: Click TOP-LEFT of the yellow plot")
        self.btn_plot.config(state="disabled")
        self.btn_button.config(state="disabled")
        self.btn_toggle.config(state="disabled")

        def on_click(x, y, button, pressed):
            if not pressed or not self.selecting_plot:
                return
            self.temp_points.append((x, y))
            self.click_count += 1
            if self.click_count == 1:
                self.status_var.set("F1: Click BOTTOM-RIGHT of the yellow plot")
            elif self.click_count == 2:
                self.finish_select_plot()
                return False

        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.start()

    def finish_select_plot(self):
        self.selecting_plot = False
        x1, y1 = self.temp_points[0]
        x2, y2 = self.temp_points[1]
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)

        if width < 80 or height < 80:
            self.status_var.set("Area too small")
            self.btn_plot.config(state="normal")
            self.btn_button.config(state="normal")
            return

        self.region = (left, top, width, height)
        self.region_var.set(f"Plot: {left},{top} ({width}x{height})")
        self.status_var.set("Plot saved – now press F3")
        self.btn_plot.config(state="normal")
        self.btn_button.config(state="normal")
        self.update_start_button_state()
        if self.live_preview.get():
            self.root.after(100, self.update_live_preview)

    def start_select_button(self):
        if self.running:
            return
        self.selecting_button = True
        self.selecting_plot = False
        self.status_var.set("F3: Click the middle of the Submit button")
        self.btn_plot.config(state="disabled")
        self.btn_button.config(state="disabled")
        self.btn_toggle.config(state="disabled")

        def on_click(x, y, button, pressed):
            if not pressed or not self.selecting_button:
                return
            self.button_pos = (int(x), int(y))
            self.button_var.set(f"Submit: ({x}, {y})")
            self.save_config()
            self.status_var.set("Submit button saved")
            self.selecting_button = False
            self.btn_plot.config(state="normal")
            self.btn_button.config(state="normal")
            self.update_start_button_state()
            return False

        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.start()

    def test_button_click(self):
        if not self.button_pos:
            messagebox.showwarning("Missing", "Set the Submit button first (F3)")
            return
        self.status_var.set("Testing Submit click...")
        self.root.update()
        self.click_saved_button()
        self.status_var.set("Test done")

    def preview_clusters(self):
        if not self.region:
            messagebox.showinfo("Missing", "Select plot area first (F1)")
            return
        self.update_live_preview()

    def toggle_run(self):
        if not self.region or not self.button_pos:
            messagebox.showinfo("Missing", "Set both Plot (F1) and Submit button (F3)")
            return
        if not self.running:
            self.running = True
            self.btn_toggle.config(text="F2 - STOP")
            self.status_var.set("RUNNING")
            for b in (self.btn_plot, self.btn_button, self.btn_test, self.btn_preview):
                b.config(state="disabled")
            self.loop_spin.config(state="disabled")
            threading.Thread(target=self.automation_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_toggle.config(text="F2 - Start / Stop")
            self.status_var.set("Stopped")
            for b in (self.btn_plot, self.btn_button, self.btn_test, self.btn_preview):
                b.config(state="normal")
            self.loop_spin.config(state="normal")

    def grab_plot(self):
        with MSS() as sct:
            mon = {"left": self.region[0], "top": self.region[1],
                   "width": self.region[2], "height": self.region[3]}
            img = np.array(sct.grab(mon))
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def detect_clusters(self, img):
        """Designed to produce large covering polygons like your examples."""
        sens = float(self.sensitivity.get())
        min_size = int(self.min_size.get())
        sep = int(self.separation.get())

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        v = hsv[:, :, 2].astype(np.float32)

        # Broad color ranges so pure blue is included
        warm = cv2.inRange(hsv, (0, 30, 30), (45, 255, 255))
        mid  = cv2.inRange(hsv, (45, 20, 20), (90, 255, 255))
        cool = cv2.inRange(hsv, (90, 10, 10), (155, 255, 255))

        density = np.zeros(img.shape[:2], dtype=np.float32)
        density[warm > 0] += 1.8
        density[mid > 0]  += 2.2
        density[cool > 0] += 2.8
        density += v / 255.0 * 1.9

        # Strong blur → larger regions
        blur = int(21 + (1.0 - sens) * 32) | 1
        density = cv2.GaussianBlur(density, (blur, blur), 0)
        density = cv2.normalize(density, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Lower threshold so more of the blue halo is kept
        thresh_val = int(22 + sens * 40)
        _, binary = cv2.threshold(density, thresh_val, 255, cv2.THRESH_BINARY)

        # Strong closing to expand and fill
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

        num, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        clusters = []
        for i in range(1, num):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < min_size:
                continue
            mask = (labels == i).astype(np.uint8) * 255
            clusters.append((mask, centroids[i], area))

        clusters.sort(key=lambda x: x[2], reverse=True)

        # Separation
        kept = []
        for mask, cent, area in clusters:
            cy, cx = cent
            too_close = False
            for _, (ky, kx), _ in kept:
                if np.sqrt((cy - ky)**2 + (cx - kx)**2) < sep:
                    too_close = True
                    break
            if not too_close:
                kept.append((mask, (cy, cx), area))

        polygons = []
        for mask, _, _ in kept[:6]:
            pts = self.mask_to_poly(mask)
            if pts is not None:
                polygons.append(pts)
        return polygons

    def mask_to_poly(self, mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) < 120:
            return None

        hull = cv2.convexHull(cnt)
        peri = cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, 0.016 * peri, True)
        pts = approx.reshape(-1, 2)

        if len(pts) < 3:
            return None

        if len(pts) > MAX_POINTS:
            dists = np.cumsum(np.sqrt(np.sum(np.diff(pts, axis=0, append=pts[:1])**2, axis=1)))
            total = dists[-1]
            if total < 1:
                return None
            samples = np.linspace(0, total, MAX_POINTS, endpoint=False)
            new_pts = [pts[np.searchsorted(dists, d) % len(pts)] for d in samples]
            pts = np.array(new_pts)

        c = pts.mean(axis=0)
        angles = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
        pts = pts[np.argsort(angles)]
        return pts.astype(int)

    def click_polygon(self, pts):
        left, top = self.region[0], self.region[1]
        for x, y in pts:
            if not self.running:
                return False
            pyautogui.moveTo(left + int(x), top + int(y), duration=MOVE_DURATION)
            time.sleep(0.04)
            pyautogui.click()
            time.sleep(CLICK_DELAY)
        pyautogui.moveTo(left + int(pts[0][0]), top + int(pts[0][1]), duration=MOVE_DURATION)
        pyautogui.click()
        time.sleep(AFTER_POLYGON_WAIT)
        return True

    def click_saved_button(self):
        if not self.button_pos:
            return False
        x, y = self.button_pos
        pyautogui.moveTo(x, y, duration=0.45)
        time.sleep(0.1)
        pyautogui.click()
        time.sleep(0.08)
        pyautogui.click()
        return True

    def automation_loop(self):
        max_loops = self.max_loops.get()
        cycle = 1
        while self.running and cycle <= max_loops:
            try:
                self.status_var.set(f"Loop {cycle}/{max_loops}")
                img = self.grab_plot()
                polygons = self.detect_clusters(img)

                if not polygons:
                    self.status_var.set(f"Loop {cycle} – no clusters")
                    time.sleep(2.2)
                    continue

                self.status_var.set(f"Loop {cycle} – {len(polygons)} clusters")
                for i, pts in enumerate(polygons):
                    if not self.running:
                        break
                    self.status_var.set(f"Loop {cycle} – cluster {i+1}/{len(polygons)}")
                    if not self.click_polygon(pts):
                        break

                if not self.running:
                    break

                time.sleep(AFTER_ALL_POLYGONS_WAIT)
                self.status_var.set(f"Loop {cycle} – SUBMIT")
                self.click_saved_button()
                time.sleep(AFTER_SUBMIT_WAIT)

                self.status_var.set(f"Loop {cycle} – Continue 1")
                self.click_saved_button()
                time.sleep(BETWEEN_CONTINUES)

                self.status_var.set(f"Loop {cycle} – Continue 2")
                self.click_saved_button()
                time.sleep(1.8)

                cycle += 1
                time.sleep(1.2)
            except Exception as e:
                print(e)
                self.status_var.set(f"Error: {e}")
                time.sleep(2)

        self.running = False
        self.root.after(0, lambda: self.btn_toggle.config(text="F2 - Start / Stop"))
        self.root.after(0, lambda: [b.config(state="normal") for b in (self.btn_plot, self.btn_button, self.btn_test, self.btn_preview)])
        self.root.after(0, lambda: self.loop_spin.config(state="normal"))
        self.root.after(0, lambda: self.status_var.set("Finished"))

    def on_close(self):
        self.running = False
        try:
            self.listener.stop()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print(f"Cluster Bot v{VERSION}")
    ClusterBot().run()
