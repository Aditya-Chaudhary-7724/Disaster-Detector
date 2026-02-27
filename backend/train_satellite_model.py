"""Train satellite CNN model.

Dataset folders expected:
- backend/dataset/earthquake/{safe,pre_disaster}
- backend/dataset/flood/{safe,pre_disaster}
- backend/dataset/landslide/{safe,pre_disaster}

If missing, placeholder synthetic images are generated.
"""

from __future__ import annotations

from satellite_predictor import train_satellite_model


if __name__ == "__main__":
    result = train_satellite_model(epochs=3)
    print(result)
