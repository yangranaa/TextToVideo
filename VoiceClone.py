import platform
import re
from pathlib import Path
from typing import Tuple
import torch
import soundfile as sf

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QRunnable
from omegaconf import DictConfig, OmegaConf
from transformers import AutoTokenizer, AutoModelForCausalLM, Wav2Vec2FeatureExtractor, Wav2Vec2Model

from sparktts.utils.audio import load_audio
from sparktts.models.bicodec import BiCodec
from sparktts.utils.token_parser import TASK_TOKEN_MAP

def get_device():
    device = 0
    if platform.system() == "Darwin":
        # macOS with MPS support (Apple Silicon)
        device = torch.device(f"mps:{device}")

    elif torch.cuda.is_available():
        # System with CUDA support
        device = torch.device(f"cuda:{device}")

    else:
        # Fall back to CPU
        device = torch.device("cpu")

    return device


def load_config(config_path: Path) -> DictConfig:
    """Loads a configuration file and optionally merges it with a base configuration.

    Args:
    config_path (Path): Path to the configuration file.
    """
    # Load the initial configuration from the given path
    config = OmegaConf.load(config_path)

    # Check if there is a base configuration specified and merge if necessary
    if config.get("base_config", None) is not None:
        base_config = OmegaConf.load(config["base_config"])
        config = OmegaConf.merge(base_config, config)

    return config

class InitVoiceCloneModelThread(QThread):
    finished = pyqtSignal(bool)

    model_dir = "Spark-TTS-0.5B"

    def __init__(self, voice_clone):
        super().__init__()
        self.voice_clone = voice_clone

    def run(self):
        self.voice_clone.config = load_config(f"{self.model_dir}/config.yaml")
        self.voice_clone.device = get_device()
        self.voice_clone.tokenizer = AutoTokenizer.from_pretrained(f"{self.model_dir}/LLM")
        self.voice_clone.model = AutoModelForCausalLM.from_pretrained(f"{self.model_dir}/LLM").to(self.voice_clone.device )
        self.voice_clone.bicodec = BiCodec.load_from_checkpoint(f"{self.model_dir}/BiCodec").to(self.voice_clone.device)
        self.voice_clone.processor = Wav2Vec2FeatureExtractor.from_pretrained(f"{self.model_dir}/wav2vec2-large-xlsr-53")
        self.voice_clone.feature_extractor = Wav2Vec2Model.from_pretrained(f"{self.model_dir}/wav2vec2-large-xlsr-53").to(
            self.voice_clone.device)
        self.voice_clone.feature_extractor.config.output_hidden_states = True

        self.finished.emit(True)


class VoiceClone:

    device = None
    save_path = ''
    voice_clone_path = None
    load_model_thread = None

    @classmethod
    def release(cls):
        if cls.load_model_thread:
            cls.load_model_thread.quit()
            cls.load_model_thread.wait()
            cls.load_model_thread = None

        cls.device = None
        cls.tokenizer = None
        cls.model = None
        cls.bicodec = None
        cls.processor = None
        cls.feature_extractor = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @classmethod
    def load_model_in_thread(cls, load_cb):
        if cls.device is None:
            cls.load_model_thread = InitVoiceCloneModelThread(cls)
            cls.load_model_thread.finished.connect(load_cb)
            cls.load_model_thread.start()

    @classmethod
    def get_ref_clip(cls, wav: np.ndarray) -> np.ndarray:
        """Get reference audio clip for speaker embedding."""
        ref_segment_length = (
                int(cls.config["sample_rate"] * cls.config["ref_segment_duration"])
                // cls.config["latent_hop_length"]
                * cls.config["latent_hop_length"]
        )
        wav_length = len(wav)

        if ref_segment_length > wav_length:
            # Repeat and truncate to handle insufficient length
            wav = np.tile(wav, ref_segment_length // wav_length + 1)

        return wav[:ref_segment_length]

    @classmethod
    def process_audio(cls, wav_path: Path) -> Tuple[np.ndarray, torch.Tensor]:
        """load auido and get reference audio from wav path"""
        wav = load_audio(
            wav_path,
            sampling_rate=cls.config["sample_rate"],
            volume_normalize=cls.config["volume_normalize"],
        )

        wav_ref = cls.get_ref_clip(wav)

        wav_ref = torch.from_numpy(wav_ref).unsqueeze(0).float()
        return wav, wav_ref

    @classmethod
    def extract_wav2vec2_features(cls, wavs: torch.Tensor) -> torch.Tensor:
        """extract wav2vec2 features"""
        inputs = cls.processor(
            wavs,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
            output_hidden_states=True,
        ).input_values
        feat = cls.feature_extractor(inputs.to(cls.feature_extractor.device))
        feats_mix = (
            feat.hidden_states[11] + feat.hidden_states[14] + feat.hidden_states[16]
        ) / 3

        return feats_mix

    @classmethod
    def tokenize(cls, audio_path: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """tokenize the audio"""
        wav, ref_wav = cls.process_audio(audio_path)
        feat = cls.extract_wav2vec2_features(wav)
        batch = {
            "wav": torch.from_numpy(wav).unsqueeze(0).float().to(cls.device),
            "ref_wav": ref_wav.to(cls.device),
            "feat": feat.to(cls.device),
        }
        semantic_tokens, global_tokens = cls.bicodec.tokenize(batch)

        return global_tokens, semantic_tokens
    
    @classmethod
    def detokenize(cls, global_tokens: torch.Tensor, semantic_tokens: torch.Tensor) -> np.array:
        """detokenize the tokens to waveform

        Args:
            global_tokens: global tokens. shape: (batch_size, global_dim)
            semantic_tokens: semantic tokens. shape: (batch_size, latent_dim)

        Returns:
            wav_rec: waveform. shape: (batch_size, seq_len) for batch or (seq_len,) for single
        """
        global_tokens = global_tokens.unsqueeze(1)
        wav_rec = cls.bicodec.detokenize(semantic_tokens, global_tokens)
        return wav_rec.detach().squeeze().cpu().numpy()



    
    @classmethod
    def prompt_tokenize(cls, prompt_speech_path):
        cls.global_token_ids, cls.semantic_token_ids = cls.tokenize(
            prompt_speech_path
        )

        cls.global_tokens = "".join(
            [f"<|bicodec_global_{i}|>" for i in cls.global_token_ids.squeeze()]
        )


    @classmethod
    def gen_speech(cls, text, idx, top_k: float = 50, top_p: float = 0.95, temperature: float = 0.8):
        inputs = [
            TASK_TOKEN_MAP["tts"],
            "<|start_content|>",
            text,
            "<|end_content|>",
            "<|start_global_token|>",
            cls.global_tokens,
            "<|end_global_token|>",
        ]

        inputs = "".join(inputs)

        model_inputs = cls.tokenizer([inputs], return_tensors="pt").to(cls.device)

        generated_ids = cls.model.generate(
            **model_inputs,
            max_new_tokens=3000,
            do_sample=True,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
        )

        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        predicts = cls.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        pred_semantic_ids = (
            torch.tensor([int(token) for token in re.findall(r"bicodec_semantic_(\d+)", predicts)])
            .long()
            .unsqueeze(0)
        )

        wav = cls.detokenize(
            cls.global_token_ids.to(cls.device).squeeze(0),
            pred_semantic_ids.to(cls.device),
        )

        file_name = f'{cls.save_path}/{text}_{idx}.wav'
        sf.write(file_name, wav, 16000)

class VoiceCloneSignals(QObject):
    """定义信号的类"""
    finished = pyqtSignal(dict)

class GenVoiceCloneTask(QRunnable):

    def __init__(self, text, idx):
        super().__init__()
        self.text = text
        self.idx = idx
        self.signals = VoiceCloneSignals()

    def run(self):
        try:
            VoiceClone.gen_speech(self.text, self.idx)
        except Exception as e:
            self.signals.finished.emit({'sucess': False, 'msg': f'{e}'})
        else:
            self.signals.finished.emit({'sucess': True, 'idx':self.idx})