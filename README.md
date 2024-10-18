
# 🎮 **FCore-OCR** 🏆  
*Seamlessly Capturing, Analyzing, and Presenting Game Data*

Welcome to **FCore-OCR** — your ultimate companion for game performance analysis and report generation! Whether you're a competitive gamer, coach, or simply someone who enjoys crunching the numbers, this tool is designed with **precision** and **efficiency** in mind. 

---

## ⚡ **What Is FCore-OCR?**

Imagine a tool that:
- 🖼️ Automatically **captures screenshots** during your matches.
- 🤖 Analyzes the **screenshot data** using **OCR (Optical Character Recognition)**.
- 📊 Extracts **match performance stats**, **player ratings**, and more.
  

---

## 🚀 **How It Works**

1. **Take Screenshots**:  
   Just hit `F12` during or after your game to capture match screens like `Player Performance`, `Match Facts`, and `Simulated Match Facts`.

2. **Automated Data Extraction**:  
   We leverage the power of **PaddleOCR** (with GPU support, of course!) to extract critical stats — from player ratings to detailed match stats. You get the data, we handle the hard part!

3. **Overlay at Your Fingertips**:  
   A customizable, semi-transparent overlay sits on top of everything, giving you live feedback on your screenshots and displaying stats in a neat table format. 📊

4. **Error Handling & Usability**:  
   If the OCR ever stumbles, don't worry! You'll get a friendly message asking for a retry, because hey, even robots aren't perfect!

---

## 💻 **Tech Stack & Tools**
- **Python 3.11** 🐍 (or higher)
- **PaddleOCR** for fast and accurate Optical Character Recognition
- **OpenCV** for image preprocessing and manipulation
- **PyWin32** for seamless interaction with Windows API (keyboard events, window handling, etc.)
- **Tons of Windows API magic** via **ctypes** 💥

---

## ⚙️ **Installation Instructions**

Let’s get you set up in no time. Follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/jaaniles/fcore-ocr.git
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Ensure you have PaddleOCR installed**:
    ```bash
    pip install paddleocr
    ```

4. **Run the app**:
    ```bash
    python run.py
    ```

🎉 That's it! You're ready to start capturing and analyzing your game like a pro.


---

## 🛠️ **Contributing**

Do you have an idea to make this better? 🧠 Feel free to open an issue or fork the repository and submit a pull request!

### **How to Contribute**:
1. **Fork the repo** and create your branch:
   ```bash
   git checkout -b my-feature-branch
   ```
2. **Make your changes**, commit, and push:
   ```bash
   git commit -m "My awesome feature"
   git push origin my-feature-branch
   ```
3. **Create a Pull Request** and let's collaborate!

---

## 🔍 **Known Issues & Limitations**

- **Full-screen apps**: Some full-screen applications may prevent our overlay from showing properly on top. Consider running your game in windowed or borderless mode for best results.
- **Edge cases in OCR**: While the OCR processing works for the vast majority of cases, there may be a few edge cases where text isn't detected correctly. We're constantly refining the process, though!

---

## 🛡️ **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

## 🙌 **Show Your Support**

If you love this tool, feel free to:
- ⭐ **Star this repo** on GitHub — it really helps!
- 🐛 **Report bugs** and suggest improvements.
- ☕ **Buy me a coffee** — because every good project deserves caffeine! 😄

---

That’s it! I hope **FCore-OCR** makes your gaming analysis smarter, faster, and just plain fun!

Happy gaming! 🎮👾

---

