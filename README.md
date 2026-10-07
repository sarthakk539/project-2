# Wire Harness Checker (Streamlit)

Input: reference image + image to check + number of wires.
Output: RIGHT / WRONG + confidence (0-100 %), per-wire table and annotated images.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Deploy on Streamlit Community Cloud
1. Push this folder's contents to a GitHub repo (app.py + requirements.txt at the root).
2. https://share.streamlit.io -> Create app -> pick repo/branch, main file `app.py` -> Deploy.

## From code
    import cv2
    from backend.verdict import check_harness, public
    r = check_harness(cv2.imread("ref.png"), cv2.imread("test.png"), 6)
    print(public(r))   # {"verdict": "RIGHT", "confidence": 0.94, ...}

## From a backend (stdin/stdout JSON)
    echo '{"reference":"<b64>","input":"<b64>","expected_count":6}' | python -m backend.verdict

## Command line demo
    python examples/run_demo.py compare sample_images/reference_sample.png sample_images/test_sample.png 6

## Confidence (heuristic, not a calibrated probability)
- RIGHT: weakest wire decides (dE 5 -> ~97 %, dE 15 = at the tolerance -> 50 %), slightly reduced
  if the bundle width looks unusual.
- WRONG: how clearly a wire is off (dE 40 -> ~100 %). A wire-count mismatch scores 60-90 %.
- Below 75 % the result is flagged "needs review". Unreadable images give ~50 %.

## Tuning
`NOMINAL_WIRE_PX` (21) in backend/multi_pin_bfs.py: re-measure if camera distance changes.
`DEFAULT_MAX_DELTA_E` (15) in backend/reference.py, or the sidebar slider.
Assumes fixed camera, vertical wires, light background. Single strand only.
