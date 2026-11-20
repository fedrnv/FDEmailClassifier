"""Bounded deterministic single-CUDA-device LoRA/QLoRA configuration."""
import math
from functools import lru_cache
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
from ingest_dataset import strict_json, reject_links


class TrainerError(ValueError):
    """Static codes, never input text or paths."""


def validate(value):
    fields = {"schema", "backend", "seed", "max_steps", "gradient_accumulation", "max_sequence_tokens", "learning_rate", "weight_decay", "max_grad_norm", "rank", "alpha", "checkpoint_interval"}
    if not isinstance(value, dict) or set(value) != fields or value["schema"] != "fdec-peft-trainer-config/v1" or value["backend"] not in ("lora", "qlora"):
        raise TrainerError("invalid_trainer_config")
    for field, minimum, maximum in (("seed", 0, 2**32-1), ("max_steps", 1, 100_000), ("gradient_accumulation", 1, 64), ("max_sequence_tokens", 128, 4096), ("rank", 1, 64), ("alpha", 1, 128), ("checkpoint_interval", 1, 100_000)):
        if type(value[field]) is not int or not minimum <= value[field] <= maximum:
            raise TrainerError("invalid_trainer_config")
    for field, minimum, maximum in (("learning_rate", 1e-8, .01), ("weight_decay", 0, 1), ("max_grad_norm", 1e-6, 100)):
        if type(value[field]) not in (int, float) or not math.isfinite(value[field]) or not minimum <= value[field] <= maximum:
            raise TrainerError("invalid_trainer_config")
    return value


def read(path):
    try:
        path = reject_links(path)
        if path.stat().st_size > 16384:
            raise ValueError()
        return validate(strict_json(path.read_text(encoding="utf-8-sig")))
    except Exception:
        raise TrainerError("invalid_trainer_config") from None


def record_index(seed, microstep, size):
    """A pure epoch shuffle makes the cursor reconstructible from global step."""
    if type(size) is not int or size < 1 or type(microstep) is not int or microstep < 0:
        raise TrainerError("invalid_training_cursor")
    epoch, offset = divmod(microstep, size)
    return epoch_order(seed, epoch, size)[offset]


@lru_cache(maxsize=4)
def epoch_order(seed, epoch, size):
    order = list(range(size))
    random.Random((seed << 32) + epoch).shuffle(order)
    return tuple(order)
