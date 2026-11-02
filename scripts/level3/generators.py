"""Крок 7: завантаження п'яти моделей з відкритими вагами й генерація одного слова.

Кожна функція load_*() повертає (generate, info): generate(word, style) → PIL-зображення,
де style — запис із level3/styles/styles.json (+ шлях до теки стилю). Ваги й код — на
ревізіях із versions/pinned.json. Відхилення від офіційних скриптів позначено в info["deviations"].
"""

import json
import os
import re
import sys
import types
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "level12"))
from common import REPOS, WORK, pinned  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SD = "stable-diffusion-v1-5/stable-diffusion-v1-5"


def rev(model_id):
    return pinned(model_id)["sha"]


def hf(model_id, filename):
    from huggingface_hub import hf_hub_download
    return hf_hub_download(model_id, filename, revision=rev(model_id))


def _sd_parts():
    from diffusers import AutoencoderKL, DDIMScheduler
    vae = AutoencoderKL.from_pretrained(SD, subfolder="vae", revision=rev(SD)).to(DEVICE).eval()
    sched = DDIMScheduler.from_pretrained(SD, subfolder="scheduler", revision=rev(SD))
    return vae, sched


def _canine():
    from transformers import CanineModel, CanineTokenizer
    r = rev("google/canine-c")
    return CanineTokenizer.from_pretrained("google/canine-c", revision=r), CanineModel.from_pretrained("google/canine-c", revision=r)


def _strip_module(sd):
    """Прибирає всі сегменти DataParallel «module.»: у DiffusionPen обгорнуто і модель, і text_encoder."""
    return {re.sub(r"(^|\.)module\.", r"\1", k): v for k, v in sd.items()}


def _in_path(path):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# --- Українська DiffusionPen ------------------------------------------------------
def load_ukr_diffusionpen():
    space = REPOS / "UkrDiffusionPen-space"
    _in_path(space)
    import torchvision
    from feature_extractor import ImageEncoder
    from generate_sentence import detect_num_classes, generate_single_word, prepare_style_reference_image, strip_dp_prefix
    from unet import UNetModel
    from utils.word_dataset import char_classes

    repo = "kdonitz/diffusionpen-ukrainian"
    state = strip_dp_prefix(torch.load(hf(repo, "ema_ckpt.pt"), map_location="cpu"))
    tokenizer, canine = _canine()
    # Параметри — як у app.py:113–119 (load_models)
    unet = UNetModel(image_size=(64, 256), in_channels=4, model_channels=320, out_channels=4, num_res_blocks=2,
                     attention_resolutions=(1, 1), channel_mult=(1, 1), num_heads=4,
                     num_classes=detect_num_classes(state), context_dim=320, vocab_size=char_classes,
                     text_encoder=canine, args=types.SimpleNamespace(interpolation=False, mix_rate=None))
    unet.load_state_dict(state)
    unet.to(DEVICE).eval()
    vae, sched = _sd_parts()
    style_enc = ImageEncoder(model_name="mobilenetv2_100", num_classes=0, pretrained=False, trainable=False)
    sd = torch.load(hf(repo, "mixed_ukr_mobilenetv2_100.pth"), map_location="cpu")
    md = style_enc.state_dict()
    md.update({k: v for k, v in sd.items() if k in md and md[k].shape == v.shape})
    style_enc.load_state_dict(md)
    style_enc.to(DEVICE).eval()
    tf = torchvision.transforms.Compose([torchvision.transforms.ToTensor(),
                                         torchvision.transforms.Normalize((0.5,) * 3, (0.5,) * 3)])

    def style_ref(style):  # app.py:167–180 (_load_writer_style_ref)
        files = sorted((style["dir"] / "words").glob("*.png"))[:5]
        imgs = [tf(prepare_style_reference_image(Image.open(f).convert("RGB"), 64, 256)) for f in files]
        while len(imgs) < 5:
            imgs.append(imgs[0])
        return torch.stack(imgs)

    @torch.no_grad()
    def generate(word, style):
        return generate_single_word(word=word, unet=unet, vae=vae, style_extractor=style_enc, tokenizer=tokenizer,
                                    noise_scheduler=sched, style_ref=style_ref(style), writer_idx=style["ukr_writer_index"],
                                    device=torch.device(DEVICE), cfg_scale=5.0, img_height=64, img_width=256, text_max_len=40)

    return generate, {"weights": f"{repo}@{rev(repo)}", "code": "Space generate_sentence.generate_single_word",
                      "settings": "50 кроків DDIM, cfg_scale 5.0 (як у app.py)", "deviations": []}


# --- DiffusionPen (оригінал, IAM) ------------------------------------------------------
IAM_LABELS = {"0000": 12, "0002": 1}  # номери авторів IAM з прикладів у train.py:302–303


def load_diffusionpen():
    repo_dir = REPOS / "DiffusionPen"
    _in_path(repo_dir)
    import torchvision
    from feature_extractor import ImageEncoder
    from unet import UNetModel
    from utils.auxilary_functions import centered_PIL, image_resize_PIL

    repo = "konnik/DiffusionPen"
    tokenizer, canine = _canine()
    # train.py:556–576 (типові аргументи) і :663 (побудова UNet); vocab_size = 80 (train.py:636)
    unet = UNetModel(image_size=(64, 256), in_channels=4, model_channels=320, out_channels=4, num_res_blocks=1,
                     attention_resolutions=(1, 1), channel_mult=(1, 1), num_heads=4, num_classes=339,
                     context_dim=320, vocab_size=80, text_encoder=canine,
                     args=types.SimpleNamespace(interpolation=False, mix_rate=None))
    unet.load_state_dict(_strip_module(torch.load(hf(repo, "diffusionpen_iam_model_path/models/ema_ckpt.pt"), map_location="cpu")))
    unet.to(DEVICE).eval()
    vae, sched = _sd_parts()
    style_enc = ImageEncoder(model_name="mobilenetv2_100", num_classes=0, pretrained=False, trainable=False)
    sd = _strip_module(torch.load(hf(repo, "style_models/iam_style_diffusionpen.pth"), map_location="cpu"))
    md = style_enc.state_dict()
    md.update({k: v for k, v in sd.items() if k in md and md[k].shape == v.shape})
    style_enc.load_state_dict(md)
    style_enc.to(DEVICE).eval()
    tf = torchvision.transforms.Compose([torchvision.transforms.ToTensor(),
                                         torchvision.transforms.Normalize((0.5,) * 3, (0.5,) * 3)])

    def prep(img):  # train.py:357–370
        w, h = img.size
        img = img.resize((int(w * 64 / h), 64))
        w, h = img.size
        if w < 256:
            return ImageOps.pad(img, size=(256, 64), color="white")
        while w > 256:
            img = image_resize_PIL(img, width=w - 20)
            w, h = img.size
        return centered_PIL(img, (64, 256), border_value=255.0)

    @torch.no_grad()
    def generate(word, style):  # train.py:255–430 (Diffusion.sampling) з нашими зразками стилю
        files = sorted((style["dir"] / "words").glob("*.png"))[:5]
        style_images = torch.stack([tf(prep(Image.open(f).convert("RGB"))) for f in files]).to(DEVICE)
        style_features = style_enc(style_images.reshape(-1, 3, 64, 256)).to(DEVICE)
        text = tokenizer(word, padding="max_length", truncation=True, return_tensors="pt", max_length=40).to(DEVICE)
        labels = torch.tensor([IAM_LABELS[style["id"]]], device=DEVICE)
        x = torch.randn((1, 4, 64 // 8, 256 // 8), device=DEVICE)
        sched.set_timesteps(50)
        for time in sched.timesteps:
            t = (torch.ones(1) * time.item()).long().to(DEVICE)
            residual = unet(x, t, text, labels, original_images=style_images, mix_rate=None, style_extractor=style_features)
            x = sched.step(residual, time, x).prev_sample
        image = vae.decode(x / 0.18215).sample
        image = (image / 2 + 0.5).clamp(0, 1)
        return torchvision.transforms.ToPILImage()(image[0].cpu()).convert("L")

    return generate, {"weights": f"{repo}@{rev(repo)}", "code": "train.py Diffusion.sampling (відтворено)",
                      "settings": "50 кроків DDIM, без CFG (як у train.py)",
                      "deviations": ["Зразки стилю — наші 5 слів замість 5 випадкових слів автора IAM (IAM для запуску не потрібен)",
                                     "Мітка автора IAM фіксована: 12 для стилю 0000, 1 для 0002 (train.py:302–303)"]}


# --- Emuru -------------------------------------------------------------------------
def load_emuru():
    from torchvision.transforms import functional as F
    from transformers import AutoModel
    repo = "blowing-up-groundhogs/emuru"
    model = AutoModel.from_pretrained(repo, trust_remote_code=True, revision=rev(repo)).to(DEVICE).eval()

    def style_tensor(style):  # картка моделі: висота 64, нормалізація [-1, 1]
        img = Image.open(style["dir"] / "line.png").convert("RGB")
        img = img.resize((img.width * 64 // img.height, 64))
        return F.normalize(F.to_tensor(img), [0.5], [0.5]).to(DEVICE)

    @torch.no_grad()
    def generate(word, style):
        return model.generate(style_text=style["transcription"], gen_text=word,
                              style_img=style_tensor(style), max_new_tokens=64)

    return generate, {"weights": f"{repo}@{rev(repo)}", "code": "AutoModel (trust_remote_code), model.generate",
                      "settings": "max_new_tokens 64 (картка моделі)",
                      "deviations": ["Стиль — наш рядок із 5 слів, складених з окремих зображень, і його транскрипція"]}


# --- Eruku -------------------------------------------------------------------------
ERUKU_MAX_NEW_TOKENS = 64  # відхилення від типових 512, див. info["deviations"]


def load_eruku():
    from transformers import AutoModel
    repo = "Blowing-Up-Groundhogs/Eruku"
    model = AutoModel.from_pretrained(repo, trust_remote_code=True, revision=rev(repo)).to(DEVICE).eval()

    @torch.no_grad()
    def generate(word, style):
        return model.generate_handwriting(style_image=Image.open(style["dir"] / "line.png").convert("RGB"),
                                          gen_text=word, style_text=style["transcription"], cfg_scale=1.25,
                                          max_new_tokens=ERUKU_MAX_NEW_TOKENS)

    return generate, {"weights": f"{repo}@{rev(repo)}", "code": "AutoModel (trust_remote_code), generate_handwriting",
                      "settings": f"cfg_scale 1.25 (картка моделі), max_new_tokens {ERUKU_MAX_NEW_TOKENS}",
                      "deviations": ["Стиль — наш рядок із 5 слів і його транскрипція",
                                     f"max_new_tokens {ERUKU_MAX_NEW_TOKENS} замість типових 512 (modeling_eruku.py, "
                                     "generate_handwriting): на кириличних словах модель не видає кінця генерації й "
                                     "доходить до межі (4088 px, ~141 с/зобр. на T4); 64 токени = 512 px, як у прикладі "
                                     "картки Emuru (max_new_tokens=64) — досить для одного слова; відрізано лише хвіст "
                                     "після 512 px"]}


# --- VATr з розширеним алфавітом -------------------------------------------------------
VATR_DRIVE_ID = "1cn0t_I3mUDjKSx9Na0dNHB0nPa0fDf1I"  # vatr.pth у теці ваг із README


def load_vatr(extra_chars):
    repo_dir = REPOS / "VATr"
    _in_path(repo_dir)
    cwd = os.getcwd()
    os.chdir(repo_dir)  # VATr відкриває files/… відносними шляхами
    try:
        import generator as vg
        from models.unifont_module import UnifontModule
        if DEVICE == "cpu":  # models/model.py:128 бере типовий device='cuda'
            UnifontModule.__init__.__defaults__ = ("cpu",) + UnifontModule.__init__.__defaults__[1:]
        args = vg.FakeArgs()
        args.device = DEVICE
        base = args.alphabet + args.special_alphabet
        added = "".join(sorted({c for c in extra_chars if c not in base and not c.isspace()}))
        # vocab_size лишається від стандартного алфавіту (generator.py:69): голови OCR і класифікаторів
        # мають ту саму форму, і checkpoint завантажується без змін; нові символи отримують гліфи Unifont
        args.alphabet = args.alphabet + added
        ckpt = WEIGHTS / "vatr.pth"
        if not ckpt.exists():
            import gdown
            ckpt.parent.mkdir(parents=True, exist_ok=True)
            gdown.download(id=VATR_DRIVE_ID, output=str(ckpt), quiet=True)
        writer = vg.VATr_writer(str(ckpt), args)
    finally:
        os.chdir(cwd)

    @torch.no_grad()
    def generate(word, style):
        os.chdir(repo_dir)
        try:
            writer.set_style_folder(str(style["dir"] / "vatr15"), num_examples=15)
            fake = writer.generate([word])[0]
        finally:
            os.chdir(cwd)
        return Image.fromarray(fake)

    import hashlib
    return generate, {"weights": f"Google Drive {VATR_DRIVE_ID} (vatr.pth), sha256 {hashlib.sha256(ckpt.read_bytes()).hexdigest()}",
                      "code": f"aimagelab/VATr@{pinned('VATr')['commit'][:12]} generator.py VATr_writer",
                      "settings": f"алфавіт розширено на {len(added)} символів: {added}",
                      "deviations": ["15 зразків стилю — 5 слів, кожне тричі (FolderDataset бере 15 без повторень)"]}


WEIGHTS = WORK / "weights"

LOADERS = {
    "ukr_diffusionpen": load_ukr_diffusionpen,
    "diffusionpen": load_diffusionpen,
    "emuru": load_emuru,
    "eruku": load_eruku,
    "vatr_extended": load_vatr,
}
