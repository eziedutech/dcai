"""Train the violence video classifier for the phone and export it to LiteRT (.tflite)
(ADR docs/proposals/on-device-behavior.md, WS2b).

Model: MoViNet-A0 stream variant (TensorFlow Model Garden, Apache-2.0), started from its
Kinetics-600 checkpoint, with a new two-class head ("normal", "kekerasan"). Data: the VID
video dataset (violent and non-violent clips of daily life); the dataset licence and its
blurred or masked variant are checked on the training box before use, and the clips never
enter the repo.

The numbers this script prints come from the held-out test split only. They are written to
violence.json next to the model; nothing else in dcAI may state an accuracy for it.

Steps (on a GPU box, see docs/log/2026-11-02.md section 6 for the Brev setup):

    uv venv -p 3.12 v && uv pip install -p v "tensorflow[and-cuda]==2.19.*" \
        "tf-keras==2.19.*" "tf-models-official==2.19.*" opencv-python-headless
    # Kinetics-600 checkpoint of MoViNet-A0 stream, published by the Model Garden
    curl -LO https://storage.googleapis.com/tf_model_garden/vision/movinet/movinet_a0_stream.tar.gz
    tar xf movinet_a0_stream.tar.gz  # a plain tar despite the name
    v/bin/python train_violence.py manifest --root VID --violent "*/Violence/*" \
        --normal "*/NonViolence/*" --out manifest.csv
    v/bin/python train_violence.py cache --manifest manifest.csv --cache cache --workers 10
    v/bin/python train_violence.py train --manifest manifest.csv \
        --checkpoint movinet_a0_stream --cache cache --out out

The globs depend on how the dataset unpacks; look at the tree first. A CPU-only check of the
whole path on synthetic clips (no dataset, no checkpoint): `train_violence.py smoke`.
"""

import argparse
import csv
import hashlib
import json
import random
import tempfile
from pathlib import Path

import numpy as np

LABELS = ["normal", "kekerasan"]
FRAMES = 16
SIZE = 172  # MoViNet-A0's training resolution
VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".mpg", ".mpeg"}


# ---------------------------------------------------------------- data


def build_manifest(root: Path, violent: str, normal: str, out: Path, seed: int = 0) -> dict:
    """path,label,split for every clip, split 70/15/15 per label with a fixed seed."""
    rows = []
    for label, pattern in ((1, violent), (0, normal)):
        clips = sorted(p for p in root.glob(pattern) if p.suffix.lower() in VIDEO_EXT)
        if not clips:
            raise SystemExit(f"no clips match {pattern!r} under {root}")
        random.Random(seed + label).shuffle(clips)  # noqa: S311 (a split, not a secret)
        n = len(clips)
        cut1, cut2 = int(n * 0.70), int(n * 0.85)
        for i, p in enumerate(clips):
            split = "train" if i < cut1 else "val" if i < cut2 else "test"
            rows.append((str(p.relative_to(root)), label, split))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "split"])
        w.writerows(rows)
    counts: dict[str, int] = {}
    for _, label, split in rows:
        key = f"{split}/{LABELS[label]}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def read_manifest(path: Path) -> tuple[Path, list[tuple[str, int, str]]]:
    with path.open(encoding="utf-8") as f:
        rows = [(r["path"], int(r["label"]), r["split"]) for r in csv.DictReader(f)]
    return path.parent, rows


def sample_frames(video: Path, frames: int = FRAMES, size: int = SIZE) -> np.ndarray:
    """`frames` frames at the midpoints of `frames` equal slices of the clip, RGB uint8
    [T, size, size, 3]. What the phone does (VideoPolicy.timesUs, then size x size)."""
    import cv2

    def small(frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)

    # Every frame is shrunk as it is read, so a long full-HD clip stays small in memory.
    cap = cv2.VideoCapture(str(video))
    decoded = []
    ok, frame = cap.read()
    while ok:
        decoded.append(small(frame))
        ok, frame = cap.read()
    cap.release()
    if not decoded:
        raise ValueError(f"no frames in {video}")
    total = len(decoded)
    idx = ((2 * np.arange(frames) + 1) * total) // (2 * frames)
    return np.stack([decoded[j] for j in idx])


def clip_array(root: Path, rel: str, cache: Path | None) -> np.ndarray:
    if cache is None:
        return sample_frames(root / rel)
    key = cache / (hashlib.sha256(rel.encode()).hexdigest() + ".npy")
    if key.exists():
        return np.load(key)
    arr = sample_frames(root / rel)
    cache.mkdir(parents=True, exist_ok=True)
    np.save(key, arr)
    return arr


def _cache_one(job: tuple[str, str, str]) -> str | None:
    root, rel, cache = job
    try:
        clip_array(Path(root), rel, Path(cache))
        return None
    except ValueError:
        return rel


def precache(manifest: Path, cache: Path, workers: int) -> None:
    """Decodes every clip once, in parallel, so training reads small arrays."""
    from multiprocessing import Pool

    root, rows = read_manifest(manifest)
    jobs = [(str(root), p, str(cache)) for p, _, _ in rows]
    with Pool(workers) as pool:
        bad = [r for r in pool.imap_unordered(_cache_one, jobs, chunksize=4) if r]
    print(f"cached {len(jobs) - len(bad)} clips, unreadable {len(bad)}")


def dataset(root, rows, split, cache, batch, shuffle):
    import tensorflow as tf

    items = [(p, y) for p, y, s in rows if s == split]

    def gen():
        order = list(items)
        if shuffle:
            random.shuffle(order)
        for p, y in order:
            try:
                yield clip_array(root, p, cache).astype(np.float32) / 255.0, y
            except ValueError:
                continue  # an unreadable clip is skipped, and counted by evaluate()

    spec = (
        tf.TensorSpec([FRAMES, SIZE, SIZE, 3], tf.float32),
        tf.TensorSpec([], tf.int32),
    )
    ds = tf.data.Dataset.from_generator(gen, output_signature=spec)
    return ds.batch(batch).prefetch(2), len(items)


# ---------------------------------------------------------------- model


def build_model(checkpoint: Path | None):
    """MoViNet-A0 with the Kinetics-600 weights, then a fresh two-class head."""
    import tensorflow as tf
    from official.projects.movinet.modeling import movinet, movinet_model

    # The phone-friendly variant (the Model Garden's TFLite setup): causal, with each 3D
    # convolution split into 2D + 1D, which LiteRT runs. The clip still goes in whole.
    backbone = movinet.Movinet(
        model_id="a0",
        causal=True,
        conv_type="2plus1d",
        se_type="2plus3d",
        activation="hard_swish",
        gating_activation="hard_sigmoid",
        use_positional_encoding=False,
        use_external_states=False,
    )
    backbone.trainable = True
    if checkpoint is not None:
        kinetics = movinet_model.MovinetClassifier(backbone=backbone, num_classes=600)
        kinetics.build([1, 1, 1, 1, 3])
        found = tf.train.latest_checkpoint(str(checkpoint))
        if found is None:
            raise SystemExit(f"no checkpoint in {checkpoint}")
        tf.train.Checkpoint(model=kinetics).restore(found).expect_partial()
    model = movinet_model.MovinetClassifier(
        backbone=backbone, num_classes=len(LABELS), dropout_rate=0.3
    )
    model.build([1, FRAMES, SIZE, SIZE, 3])
    return model


def metrics(y_true: list[int], p_violent: list[float], threshold: float = 0.5) -> dict:
    tp = sum(1 for y, p in zip(y_true, p_violent, strict=True) if y == 1 and p >= threshold)
    fp = sum(1 for y, p in zip(y_true, p_violent, strict=True) if y == 0 and p >= threshold)
    fn = sum(1 for y, p in zip(y_true, p_violent, strict=True) if y == 1 and p < threshold)
    tn = sum(1 for y, p in zip(y_true, p_violent, strict=True) if y == 0 and p < threshold)
    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": n,
        "threshold": threshold,
        "accuracy": round((tp + tn) / n, 4) if n else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


def export_tflite(model, out: Path) -> bytes:
    """Fixed input [1, FRAMES, SIZE, SIZE, 3] in 0..1, softmax output [1, 2]; dynamic-range
    int8 weights, as the image model."""
    import tensorflow as tf

    @tf.function(
        input_signature=[tf.TensorSpec([1, FRAMES, SIZE, SIZE, 3], tf.float32, name="frames")]
    )
    def probs(frames):
        return tf.nn.softmax(model(frames, training=False), axis=-1)

    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [probs.get_concrete_function()], model
    )
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    blob = converter.convert()
    out.write_bytes(blob)
    return blob


def tflite_probs(model_file: Path, clips: list[np.ndarray]) -> list[float]:
    import tensorflow as tf

    interpreter = tf.lite.Interpreter(model_path=str(model_file))
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]["index"]
    out = interpreter.get_output_details()[0]["index"]
    result = []
    for clip in clips:
        interpreter.set_tensor(inp, (clip.astype(np.float32) / 255.0)[None])
        interpreter.invoke()
        result.append(float(interpreter.get_tensor(out)[0, 1]))
    return result


# ---------------------------------------------------------------- commands


def train(args) -> None:
    import tensorflow as tf
    import tf_keras  # the Model Garden builds on Keras 2

    tf_keras.utils.set_random_seed(args.seed)
    root, rows = read_manifest(args.manifest)
    cache = args.cache
    train_ds, n_train = dataset(root, rows, "train", cache, args.batch, shuffle=True)
    val_ds, _ = dataset(root, rows, "val", cache, args.batch, shuffle=False)

    model = build_model(args.checkpoint)
    steps = max(1, n_train // args.batch) * args.epochs
    schedule = tf_keras.optimizers.schedules.CosineDecay(args.lr, steps)
    model.compile(
        optimizer=tf_keras.optimizers.RMSprop(
            schedule, rho=0.9, momentum=0.9, epsilon=1.0, clipnorm=1.0
        ),
        loss=tf_keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=["accuracy"],
    )
    args.out.mkdir(parents=True, exist_ok=True)
    best = args.out / "best.weights.h5"
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        steps_per_epoch=args.max_steps or None,
        validation_steps=args.max_steps or None,
        callbacks=[
            tf_keras.callbacks.ModelCheckpoint(
                str(best), monitor="val_accuracy", save_best_only=True, save_weights_only=True
            )
        ],
        verbose=2,
    )
    if best.exists():
        model.load_weights(str(best))

    # Held-out test split, once, after the choice of weights.
    test = [(p, y) for p, y, s in rows if s == "test"]
    clips, ys, skipped = [], [], 0
    for p, y in test[: args.max_test or None]:
        try:
            clips.append(clip_array(root, p, cache))
            ys.append(y)
        except ValueError:
            skipped += 1
    keras_p = [
        float(tf.nn.softmax(model(c[None].astype(np.float32) / 255.0, training=False))[0, 1])
        for c in clips
    ]
    model_file = args.out / "violence.tflite"
    blob = export_tflite(model, model_file)
    lite_p = tflite_probs(model_file, clips)
    parity = max((abs(a - b) for a, b in zip(keras_p, lite_p, strict=True)), default=0.0)

    meta = {
        "source": "MoViNet-A0 stream (TF Model Garden, Apache-2.0), Kinetics-600 start"
        if args.checkpoint
        else "MoViNet-A0 stream, random start (smoke run, not for the phone)",
        "data": str(args.data_name),
        "labels": LABELS,
        "frames": FRAMES,
        "size": SIZE,
        "layout": "NTHWC",
        "range": "0..1",
        "quant": "litert dynamic-range int8",
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "parity_max_abs": round(parity, 4),
        "test_skipped_unreadable": skipped,
        "test_keras": metrics(ys, keras_p),
        "test_tflite": metrics(ys, lite_p),
        "epochs": args.epochs,
        "seed": args.seed,
    }
    (args.out / "violence.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("bytes", "parity_max_abs", "test_tflite")}, indent=1))


def smoke(args) -> None:
    """The whole path on CPU with made-up clips: a moving square (normal) and a flashing,
    jumping one (kekerasan). Proves the code runs; the numbers mean nothing."""
    import cv2

    work = Path(tempfile.mkdtemp(prefix="violence-smoke-"))
    rng = np.random.default_rng(0)
    for label in ("Violence", "NonViolence"):
        for i in range(8):
            path = work / "data" / label / f"clip{i}.mp4"
            path.parent.mkdir(parents=True, exist_ok=True)
            vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 15, (96, 96))
            for t in range(30):
                img = np.zeros((96, 96, 3), np.uint8)
                if label == "Violence":
                    x, y = rng.integers(0, 70, 2)
                    img[:] = (0, 0, 255) if t % 2 else (0, 0, 0)
                else:
                    x, y = 2 * t, 40
                cv2.rectangle(
                    img, (int(x), int(y)), (int(x) + 20, int(y) + 20), (255, 255, 255), -1
                )
                vw.write(img)
            vw.release()
    counts = build_manifest(
        work / "data", "Violence/*", "NonViolence/*", work / "data" / "manifest.csv"
    )
    print("smoke manifest", counts)
    args.manifest = work / "data" / "manifest.csv"
    args.checkpoint = None
    args.cache = work / "cache"
    args.out = work / "out"
    args.epochs, args.batch, args.max_steps, args.max_test = 1, 2, 2, 4
    args.data_name = "synthetic smoke clips"
    train(args)
    print(f"smoke output in {work}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("manifest", help="list clips with label and split")
    m.add_argument("--root", type=Path, required=True)
    m.add_argument("--violent", required=True, help="glob under root for violent clips")
    m.add_argument("--normal", required=True, help="glob under root for non-violent clips")
    m.add_argument("--out", type=Path, required=True, help="CSV; clip paths are relative to root")

    c = sub.add_parser("cache", help="decode every clip once, in parallel")
    c.add_argument("--manifest", type=Path, required=True)
    c.add_argument("--cache", type=Path, required=True)
    c.add_argument("--workers", type=int, default=8)

    for name in ("train", "smoke"):
        t = sub.add_parser(name)
        t.add_argument("--manifest", type=Path)
        t.add_argument(
            "--checkpoint", type=Path, help="Kinetics-600 MoViNet-A0 stream checkpoint dir"
        )
        t.add_argument("--cache", type=Path, help="directory for decoded clips (.npy)")
        t.add_argument("--out", type=Path)
        t.add_argument("--data-name", default="VID")
        t.add_argument("--epochs", type=int, default=10)
        t.add_argument("--batch", type=int, default=8)
        t.add_argument("--lr", type=float, default=1e-3)
        t.add_argument("--seed", type=int, default=0)
        t.add_argument("--max-steps", type=int, default=0, help="cap steps per epoch (debug)")
        t.add_argument("--max-test", type=int, default=0, help="cap test clips (debug)")

    args = ap.parse_args()
    if args.cmd == "manifest":
        # The manifest sits next to the clips' root so train can resolve relative paths.
        print(build_manifest(args.root, args.violent, args.normal, args.out))
    elif args.cmd == "cache":
        precache(args.manifest, args.cache, args.workers)
    elif args.cmd == "train":
        if not (args.manifest and args.out):
            raise SystemExit("train needs --manifest and --out")
        train(args)
    else:
        smoke(args)


if __name__ == "__main__":
    main()
