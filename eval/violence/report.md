# Violence in video: trained, tested on the phone, held

A video classifier for violence was trained, measured and tried on the test phone. It works on
the kind of footage it was trained on and missed the one chat video it was tried on, so it does
not ship. This page records the effort and its numbers.

## What was built

- **Model.** MoViNet-A0, stream variant (TF Model Garden, Apache-2.0), started from its
  Kinetics-600 checkpoint and fine-tuned for two classes, normal and violence. The base variant
  uses 3D convolutions that LiteRT cannot run; the stream variant (2+1D convolutions) converts to
  LiteRT builtins. Input is 16 frames of 172 x 172 RGB taken at the midpoints of 16 equal slices
  of the clip, the same way the phone takes them. Exported with dynamic-range int8: 4,062,456
  bytes.
- **Data.** VID, Harvard Dataverse doi:10.7910/DVN/N4LNZD, version 2, CC0 1.0: recorded
  footage in classrooms, homes, streets and other places, released in two anonymized variants of
  the same clips. Only one variant was used, so no clip appears in two splits. 3,020 clips,
  split 70/15/15 with seed 0: 2,114 train, 452 validation, 454 test, balanced.
- **Training.** 10 epochs, batch 8, on one rented GPU (about 99 s per epoch). The weights with
  the best validation accuracy (0.9602, epoch 7) were exported. Script:
  `code/vision/train_violence.py`; output: `violence.json` in this folder.
- **On the phone.** A video an app with the dcAI SDK is about to show or send is read as frames
  on the phone (never sent anywhere): the image model reads up to 4 frames, then the violence
  model reads 16. The server receives a label only. This path is switched off in published builds
  until the consent text names video.

## Results on the VID test split

454 clips not used in training or model selection, threshold 0.5.

| Model | Accuracy | Precision | Recall | F1 | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|
| Keras, float | 0.9471 | 0.9247 | 0.9736 | 0.9485 | 221 | 18 | 6 | 209 |
| LiteRT int8, as on the phone | 0.9471 | 0.9283 | 0.9692 | 0.9483 | 220 | 17 | 7 | 210 |

These numbers hold for footage like VID and say nothing about videos shared in chats.

## On the test phone (3 Nov 2026, one run each, not a benchmark)

A mid-range Android 11 phone (Helio P35), test build with the video path on.

| Video | Image model, 4 frames | Violence model, 16 frames | Result |
|---|---|---|---|
| Synthetic test pattern, 8 s | 3.5 to 5.7 s per frame | 774 ms | `aman`, correct |
| A violent clip the project owner chose for the test, 22.7 s, portrait 1080 x 1920, sent through WhatsApp and then the sample chat app | 3.5 to 3.8 s per frame | 778 ms | `aman`, **missed** |

The missed clip was then scored on a laptop with the same model file, and deleted afterwards:

| How the clip was read | Violence score (threshold 0.70 on the phone) |
|---|---|
| Whole clip, frames squeezed to a square, as on the phone | 0.006 |
| Whole clip, centre square crop | 0.003 |
| Highest 3 s window (9 to 12 s), squeezed / centre crop | 0.141 / 0.224 |

Portrait framing and sparse frames do not explain the miss: no reading comes near the
threshold. The training data does not resemble videos children receive in chats (handheld,
portrait, edited, re-encoded by messaging apps).

## Decision

Held (owner, 3 Nov 2026). The model is not bundled and dcAI makes no claim about detecting
violence in video. Sexual content in video is still checked with the image model on frames,
under the same switch. A second attempt needs licensed training data that looks like chat video;
we have not identified one yet.
