import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

# Add the project root to sys.path to allow backend imports
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Import core logic from your repository
from backend.verdict import check_harness, REVIEW_BELOW
from backend.reference import DEFAULT_MAX_DELTA_E
from backend.visualize import annotate

class WireHarnessCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wire Harness Checker (Desktop)")
        self.root.geometry("1100x900")
        
        self.ref_path = None
        self.test_path = None
        self.tk_ref_img = None
        self.tk_test_img = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top Settings Frame
        settings_frame = ttk.LabelFrame(self.root, text="Settings & Inputs", padding=(15, 10))
        settings_frame.pack(fill="x", padx=20, pady=15)
        
        # Buttons for image selection
        ttk.Button(settings_frame, text="1. Select Reference Image", command=self.select_reference).grid(row=0, column=0, padx=5, pady=8, sticky="ew")
        self.ref_label = ttk.Label(settings_frame, text="No reference selected", foreground="gray")
        self.ref_label.grid(row=0, column=1, columnspan=2, padx=10, pady=8, sticky="w")
        
        ttk.Button(settings_frame, text="2. Select Test Image", command=self.select_test).grid(row=1, column=0, padx=5, pady=8, sticky="ew")
        self.test_label = ttk.Label(settings_frame, text="No test selected", foreground="gray")
        self.test_label.grid(row=1, column=1, columnspan=2, padx=10, pady=8, sticky="w")
        
        ttk.Button(settings_frame, text="Use Sample Images", command=self.use_samples).grid(row=2, column=0, padx=5, pady=8, sticky="ew")
        
        # Number of wires
        ttk.Label(settings_frame, text="Number of Wires:").grid(row=3, column=0, padx=5, pady=8, sticky="e")
        self.wires_var = tk.IntVar(value=6)
        ttk.Spinbox(settings_frame, from_=1, to=40, textvariable=self.wires_var, width=5).grid(row=3, column=1, padx=10, pady=8, sticky="w")
        
        # Color tolerance (Delta E)
        ttk.Label(settings_frame, text="Colour tolerance (Delta E):").grid(row=4, column=0, padx=5, pady=8, sticky="e")
        self.delta_e_var = tk.DoubleVar(value=DEFAULT_MAX_DELTA_E)
        
        slider_frame = ttk.Frame(settings_frame)
        slider_frame.grid(row=4, column=1, columnspan=2, padx=10, pady=8, sticky="ew")
        ttk.Scale(slider_frame, from_=5.0, to=40.0, variable=self.delta_e_var, orient="horizontal").pack(side="left", fill="x", expand=True)
        self.delta_e_val_label = ttk.Label(slider_frame, text=f"{DEFAULT_MAX_DELTA_E:.1f}", width=5)
        self.delta_e_val_label.pack(side="right", padx=(10, 0))
        
        self.delta_e_var.trace_add("write", lambda *args: self.delta_e_val_label.config(text=f"{self.delta_e_var.get():.1f}"))
        
        # Run Button
        run_frame = ttk.Frame(self.root)
        run_frame.pack(pady=10)
        self.run_btn = ttk.Button(run_frame, text="Check Harness", command=self.run_check)
        self.run_btn.pack()
        
        # Results Frame
        self.results_frame = ttk.LabelFrame(self.root, text="Results", padding=(15, 10))
        self.results_frame.pack(fill="x", padx=20, pady=10)
        
        self.verdict_label = ttk.Label(self.results_frame, text="Verdict: -", font=("Arial", 18, "bold"))
        self.verdict_label.pack()
        
        self.confidence_label = ttk.Label(self.results_frame, text="Confidence: -", font=("Arial", 12))
        self.confidence_label.pack()
        
        self.reason_label = ttk.Label(self.results_frame, text="", font=("Arial", 10), wraplength=800)
        self.reason_label.pack(pady=5)
        
        # Images Frame
        self.images_frame = ttk.Frame(self.root)
        self.images_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.ref_img_label = ttk.Label(self.images_frame)
        self.ref_img_label.pack(side="left", fill="both", expand=True, padx=10)
        
        self.test_img_label = ttk.Label(self.images_frame)
        self.test_img_label.pack(side="right", fill="both", expand=True, padx=10)
        
        # Table Frame (Per-Wire Details)
        self.table_frame = ttk.LabelFrame(self.root, text="Per-Wire Details", padding=(10, 5))
        self.table_frame.pack(fill="x", padx=20, pady=(5, 20))
        
        self.tree = ttk.Treeview(self.table_frame, columns=("Wire", "Expected", "Detected", "Delta E", "Match chance", "Result"), show="headings", height=4)
        for col in ("Wire", "Expected", "Detected", "Delta E", "Match chance", "Result"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.pack(fill="x", expand=False)
        
    def select_reference(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.ref_path = path
            self.ref_label.config(text=os.path.basename(path), foreground="black")
            
    def select_test(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.test_path = path
            self.test_label.config(text=os.path.basename(path), foreground="black")
            
    def use_samples(self):
        sample_dir = os.path.join(APP_DIR, "sample_images")
        ref_path = os.path.join(sample_dir, "reference_sample.png")
        test_path = os.path.join(sample_dir, "test_sample.png")
        
        if os.path.exists(ref_path) and os.path.exists(test_path):
            self.ref_path = ref_path
            self.ref_label.config(text="reference_sample.png", foreground="black")
            self.test_path = test_path
            self.test_label.config(text="test_sample.png", foreground="black")
            messagebox.showinfo("Samples Loaded", "Sample images have been loaded.")
        else:
            messagebox.showerror("Error", "Could not find sample images in 'sample_images' folder.")
            
    def display_image(self, label, cv2_img):
        # Resize to fit screen
        max_w, max_h = 450, 500
        h, w = cv2_img.shape[:2]
        ratio = min(max_w / w, max_h / h)
        if ratio < 1:
            cv2_img = cv2.resize(cv2_img, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)
            
        # Convert BGR to RGB and then to PIL Image for Tkinter
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        
        tk_img = ImageTk.PhotoImage(image=pil_img)
        label.configure(image=tk_img)
        label.image = tk_img  # Keep a reference to prevent garbage collection
        
    def run_check(self):
        if not self.ref_path or not self.test_path:
            messagebox.showerror("Error", "Please select both reference and test images.")
            return
            
        ref_img = cv2.imread(self.ref_path)
        test_img = cv2.imread(self.test_path)
        
        if ref_img is None or test_img is None:
            messagebox.showerror("Error", "Could not read one of the selected images.")
            return
            
        n_wires = self.wires_var.get()
        max_de = self.delta_e_var.get()
        
        # Update UI to show processing
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            res = check_harness(ref_img, test_img, n_wires, max_delta_e=max_de)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during checking:\n{e}")
            self.root.config(cursor="")
            return
            
        self.root.config(cursor="")
        
        verdict = res["verdict"]
        conf = res["confidence"]
        reason = res["reason"]
        
        if res.get("reference_error"):
            self.verdict_label.config(text="⚠️ REFERENCE PROBLEM", foreground="orange")
        elif verdict == "RIGHT":
            self.verdict_label.config(text="✅ RIGHT", foreground="green")
        else:
            self.verdict_label.config(text="❌ WRONG", foreground="red")
            
        conf_text = f"Confidence: {conf * 100:.0f}%"
        if res["needs_review"]:
            conf_text += f"  (Needs Review - Below {REVIEW_BELOW * 100:.0f}%)"
        self.confidence_label.config(text=conf_text)
        self.reason_label.config(text=reason)
        
        # Clear Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Populate Treeview
        rows = res.get("wires")
        if rows:
            for r in rows:
                self.tree.insert("", "end", values=(
                    r["wire"], r["expected"], r["detected"],
                    r["delta_e"], f"{r['match_probability'] * 100:.0f}%",
                    "OK" if r["match"] else "FAIL"
                ))
        
        # Display annotated images
        try:
            ann_ref = annotate(ref_img, res["_ref_colors"], res["_ref_dbg"])
            ann_test = annotate(test_img, res["_test_colors"], res["_test_dbg"], res.get("wires"))
            
            self.display_image(self.ref_img_label, ann_ref)
            self.display_image(self.test_img_label, ann_test)
        except Exception as e:
            messagebox.showerror("Warning", f"Could not generate annotated images:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WireHarnessCheckerApp(root)
    root.mainloop()