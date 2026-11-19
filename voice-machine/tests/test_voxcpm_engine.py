"""Adapter VoxCPM2 testowany na atrapach `torch` i `voxcpm` o prawdziwych sygnaturach (z źródeł 2.0.3).

Wagi modelu nie są dostępne w środowisku testowym, więc to sprawdza logikę adaptera i wywołania biblioteki,
a nie jakość mowy. Test kontraktowy na końcu porównuje użyte argumenty ze źródłami, jeśli ustawisz
SVM_VOXCPM_SOURCE_DIR na katalog z rozpakowanym wheel voxcpm 2.0.3.
"""

from __future__ import annotations

import ast
import base64
import inspect
import os
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from helpers import speechlike_wav, wait_until
from voice_machine.config import Settings
from voice_machine.engines import voxcpm as vx
from voice_machine.engines.base import EngineState, SynthParams, VoiceRef
from voice_machine.errors import E_ENGINE_FAILED, E_LANGUAGE, E_NOT_READY, VoiceMachineError
from voice_machine.service import Service


class StubTtsModel:
    sample_rate = 48_000
    device = "cuda:0"


class StubVoxCPM:
    instances: list["StubVoxCPM"] = []
    fail_with: BaseException | None = None
    output: Any = None

    def __init__(self) -> None:
        self.tts_model = StubTtsModel()
        self.calls: list[dict[str, Any]] = []
        self.init_args: dict[str, Any] = {}

    @classmethod
    def from_pretrained(  # noqa: PLR0913 - kopia sygnatury z voxcpm/core.py:104-116
        cls, hf_model_id="openbmb/VoxCPM2", load_denoiser=True, zipenhancer_model_id="iic/x", cache_dir=None,
        local_files_only=False, optimize=True, device=None, lora_config=None, lora_weights_path=None, **kwargs,
    ):
        if cls.fail_with is not None:
            raise cls.fail_with
        inst = cls()
        inst.init_args = {"hf_model_id": hf_model_id, "load_denoiser": load_denoiser, "optimize": optimize, "device": device}
        cls.instances.append(inst)
        return inst

    def _generate(  # noqa: PLR0913 - kopia sygnatury z voxcpm/core.py:180-196 (parametry po self)
        self, text, prompt_wav_path=None, prompt_text=None, reference_wav_path=None, cfg_value=2.0,
        inference_timesteps=10, min_len=2, max_len=4096, normalize=False, denoise=False, retry_badcase=True,
        retry_badcase_max_times=3, retry_badcase_ratio_threshold=6.0, streaming=False,
    ):
        raise NotImplementedError

    def generate(self, text, prompt_wav_path=None, prompt_text=None, reference_wav_path=None, cfg_value=2.0,
                 inference_timesteps=10, min_len=2, max_len=4096, normalize=False, denoise=False, retry_badcase=True,
                 retry_badcase_max_times=3, retry_badcase_ratio_threshold=6.0, streaming=False):
        self.calls.append({
            "text": text, "prompt_wav_path": prompt_wav_path, "prompt_text": prompt_text,
            "reference_wav_path": reference_wav_path, "cfg_value": cfg_value, "inference_timesteps": inference_timesteps,
            "normalize": normalize, "denoise": denoise,
        })
        if StubVoxCPM.output is not None:
            return StubVoxCPM.output
        return (0.1 * np.sin(np.linspace(0, 200, 48_000))).astype(np.float32)


class StubTorch(types.ModuleType):
    def __init__(self, cuda: bool = True) -> None:
        super().__init__("torch")
        self.__version__ = "9.9.9-stub"
        self.seeds: list[int] = []
        self.cuda_seeds: list[int] = []
        self.cuda = types.SimpleNamespace(
            is_available=lambda: cuda,
            manual_seed_all=self.cuda_seeds.append,
            empty_cache=lambda: None,
            get_device_properties=lambda i: types.SimpleNamespace(name="Stub GPU", total_memory=12 * 2**30),
        )

    def manual_seed(self, seed: int) -> None:
        self.seeds.append(seed)


@pytest.fixture
def stub_libs(monkeypatch: pytest.MonkeyPatch):
    StubVoxCPM.instances = []
    StubVoxCPM.fail_with = None
    StubVoxCPM.output = None
    torch = StubTorch()
    module = types.ModuleType("voxcpm")
    module.VoxCPM = StubVoxCPM  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "voxcpm", module)
    # Testy ładowania nie mogą zależeć od wersji Pythona, na której biegną (strażnik wersji ma własny test).
    monkeypatch.setattr(vx, "PYTHON_RANGE", ((3, 0), (4, 0)))
    return torch


def make_engine(tmp_path: Path, **settings: Any) -> vx.VoxCpmEngine:
    return vx.VoxCpmEngine(Settings(data_dir=tmp_path / "data", engine="voxcpm", **settings))


def load(engine: vx.VoxCpmEngine) -> None:
    engine.start_loading()
    wait_until(lambda: engine.info().state is not EngineState.LOADING)


def cloned(tmp_path: Path, transcript: str | None = None) -> VoiceRef:
    sample = tmp_path / "s0.wav"
    sample.write_bytes(b"RIFF")
    return VoiceRef(kind="cloned", voice_id="v_abcdefabcdef", name="Kuba", fingerprint="ab" * 32, sample_paths=(sample,), transcript=transcript, language="pl")


BUILTIN = VoiceRef(kind="builtin", voice_id=f"builtin:{vx.BUILTIN_VOICE}", name=vx.BUILTIN_VOICE, fingerprint="cd" * 32)


def test_loading_uses_safe_defaults_and_reports_state(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    assert engine.info().state is EngineState.IDLE and engine.info().builtin_voices == ()
    load(engine)
    info = engine.info()
    assert info.state is EngineState.READY and info.error is None
    assert info.id == "voxcpm2" and info.sample_rate == 48_000 and info.device == "cuda:0"
    assert info.reference_sample_rate == 16_000 and "pl" in info.languages and len(info.languages) == 30
    assert info.builtin_voices == (vx.BUILTIN_VOICE,)
    assert info.capabilities == {"speed": False, "temperature": False, "seed": True}
    assert info.reference.max_files == 1 and info.reference.transcript == "optional"
    init = StubVoxCPM.instances[0].init_args
    assert init == {"hf_model_id": "openbmb/VoxCPM2", "load_denoiser": False, "optimize": False, "device": None}


def test_environment_overrides_and_bad_values(tmp_path: Path, stub_libs, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SVM_VOXCPM_MODEL", "C:\\modele\\VoxCPM2")
    monkeypatch.setenv("SVM_VOXCPM_OPTIMIZE", "1")
    monkeypatch.setenv("SVM_VOXCPM_TIMESTEPS", "16")
    monkeypatch.setenv("SVM_VOXCPM_CFG", "2,5")
    monkeypatch.setenv("SVM_VOXCPM_CHUNK_CHARS", "9999")  # poza zakresem
    engine = make_engine(tmp_path, device="cuda:1")
    load(engine)
    assert StubVoxCPM.instances[0].init_args == {"hf_model_id": "C:\\modele\\VoxCPM2", "load_denoiser": False, "optimize": True, "device": "cuda:1"}
    assert engine.max_chunk_chars("pl") == vx.DEFAULT_CHUNK_CHARS
    assert any("SVM_VOXCPM_CHUNK_CHARS" in note for note in engine.info().notes)
    engine.synthesize("Test.", "pl", BUILTIN, SynthParams())
    call = StubVoxCPM.instances[0].calls[0]
    assert call["inference_timesteps"] == 16 and call["cfg_value"] == 2.5


def test_cloned_voice_without_transcript_uses_reference_mode(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    load(engine)
    ref = cloned(tmp_path)
    engine.synthesize("Dzień dobry.", "pl", ref, SynthParams())
    call = StubVoxCPM.instances[0].calls[0]
    assert call["reference_wav_path"] == str(ref.sample_paths[0])
    assert call["prompt_wav_path"] is None and call["prompt_text"] is None
    assert call["normalize"] is False and call["denoise"] is False
    assert call["cfg_value"] == vx.DEFAULT_CFG_VALUE and call["inference_timesteps"] == vx.DEFAULT_TIMESTEPS


def test_cloned_voice_with_transcript_uses_ultimate_cloning(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    load(engine)
    ref = cloned(tmp_path, transcript="Dzień dobry wszystkim.")
    engine.synthesize("Dzień dobry.", "pl", ref, SynthParams())
    call = StubVoxCPM.instances[0].calls[0]
    path = str(ref.sample_paths[0])
    assert call["prompt_wav_path"] == path and call["reference_wav_path"] == path and call["prompt_text"] == "Dzień dobry wszystkim."


def test_builtin_voice_has_no_reference(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    load(engine)
    engine.synthesize("Tekst.", "pl", BUILTIN, SynthParams())
    call = StubVoxCPM.instances[0].calls[0]
    assert call["reference_wav_path"] is None and call["prompt_wav_path"] is None and call["prompt_text"] is None


def test_seed_is_applied_to_torch_before_generation(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    load(engine)
    engine.synthesize("A.", "pl", BUILTIN, SynthParams(seed=7))
    engine.synthesize("B.", "pl", BUILTIN, SynthParams())
    assert stub_libs.seeds == [7] and stub_libs.cuda_seeds == [7]


def test_output_is_validated_and_returned_with_the_model_rate(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    load(engine)
    clip = engine.synthesize("Tekst.", "pl", BUILTIN, SynthParams())
    assert clip.sample_rate == 48_000 and clip.samples.dtype == np.float32 and clip.samples.ndim == 1
    for bad in (np.zeros(0, dtype=np.float32), np.array([0.1, np.nan, 0.2], dtype=np.float32)):
        StubVoxCPM.output = bad
        with pytest.raises(VoiceMachineError) as exc:
            engine.synthesize("Tekst.", "pl", BUILTIN, SynthParams())
        assert exc.value.code == E_ENGINE_FAILED
    StubVoxCPM.output = np.full((1, 480), 0.1, dtype=np.float32)  # 2-D z wymiarem wsadu jest spłaszczane
    assert engine.synthesize("Tekst.", "pl", BUILTIN, SynthParams()).samples.shape == (480,)


def test_not_ready_and_language_validation(tmp_path: Path, stub_libs) -> None:
    engine = make_engine(tmp_path)
    with pytest.raises(VoiceMachineError) as exc:
        engine.synthesize("Tekst.", "pl", BUILTIN, SynthParams())
    assert exc.value.code == E_NOT_READY
    for ok in ("pl", "PL", " pl-PL ", "zh-cn"):
        assert engine.validate_language(ok) in vx.LANGUAGES
    with pytest.raises(VoiceMachineError) as bad:
        engine.validate_language("xx")
    assert bad.value.code == E_LANGUAGE


def test_missing_dependencies_become_an_error_state_with_install_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "voxcpm", None)  # import zgłosi ImportError
    monkeypatch.setitem(sys.modules, "torch", StubTorch())
    monkeypatch.setattr(vx, "PYTHON_RANGE", ((3, 0), (4, 0)))
    engine = make_engine(tmp_path)
    load(engine)
    info = engine.info()
    assert info.state is EngineState.ERROR and "pip install" in (info.error or "") and "voxcpm" in (info.error or "")


def test_unsupported_python_is_reported_before_importing_anything(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stub_libs) -> None:
    monkeypatch.setattr(vx, "PYTHON_RANGE", ((3, 0), (3, 1)))  # nadpisuje zakres z fixture'a: żadna wersja nie pasuje
    engine = make_engine(tmp_path)
    load(engine)
    assert engine.info().state is EngineState.ERROR and "3.10-3.12" in (engine.info().error or "")
    assert StubVoxCPM.instances == []


@pytest.mark.parametrize(
    "exc, expected",
    [
        (RuntimeError("CUDA out of memory. Tried to allocate 2 GiB"), "Za mało pamięci karty graficznej"),
        (OSError("Max retries exceeded with url: /openbmb/VoxCPM2"), "Hugging Face"),
        (ValueError("coś innego"), "ValueError: coś innego"),
    ],
)
def test_load_failures_are_explained(tmp_path: Path, stub_libs, exc: BaseException, expected: str) -> None:
    StubVoxCPM.fail_with = exc
    engine = make_engine(tmp_path)
    load(engine)
    assert engine.info().state is EngineState.ERROR and expected in (engine.info().error or "")


def test_implausible_sample_rate_is_rejected(tmp_path: Path, stub_libs, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(StubTtsModel, "sample_rate", 123)
    engine = make_engine(tmp_path)
    load(engine)
    assert engine.info().state is EngineState.ERROR and "częstotliwość" in (engine.info().error or "")


def test_cpu_only_gets_a_visible_warning(tmp_path: Path, stub_libs, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(StubTtsModel, "device", "cpu")
    engine = make_engine(tmp_path)
    load(engine)
    assert "bez karty graficznej" in engine.info().notes[0]


def test_diagnose_reports_gpu_and_missing_pieces(tmp_path: Path, stub_libs, monkeypatch: pytest.MonkeyPatch) -> None:
    def not_installed(name: str) -> str:
        raise vx.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(vx.metadata, "version", not_installed)
    rows = {label: (value, ok) for label, value, ok in make_engine(tmp_path).diagnose()}
    assert rows["PyTorch"] == ("9.9.9-stub", True)
    assert rows["karta CUDA"][1] is True and "Stub GPU" in rows["karta CUDA"][0] and "12.0 GB" in rows["karta CUDA"][0]
    assert rows["voxcpm"][1] is False and "pip install" in rows["voxcpm"][0]
    assert "model w pamięci podręcznej" in rows
    monkeypatch.setattr(vx.metadata, "version", lambda name: "9.9.9")
    rows = {label: (value, ok) for label, value, ok in make_engine(tmp_path).diagnose()}
    assert rows["voxcpm"][1] is True and "sprawdzono tylko z 2.0.3" in rows["voxcpm"][0]


def test_full_job_through_the_service_with_a_cloned_voice(tmp_path: Path, stub_libs) -> None:
    settings = Settings(data_dir=tmp_path / "data", engine="voxcpm")
    engine = vx.VoxCpmEngine(settings)
    service = Service(settings, engine)
    try:
        load(engine)
        begin = service.upload_begin("Kuba", "pl", True, 1, "Mam 5 złotych.")
        blob = speechlike_wav(8.0, rate=16_000)
        service.upload_chunk(begin["upload_id"], 0, 0, base64.b64encode(blob).decode("ascii"))
        voice = service.upload_commit(begin["upload_id"])["voice"]
        job = service.speak(voice["id"], "Zapłacę 12,50 zł o 14:30.", None, 1.0, 0.7, 5)
        wait_until(lambda: service.job_status(job["job_id"])["status"] in ("done", "failed"))
        snap = service.job_status(job["job_id"])
        assert snap["status"] == "done", snap
        assert snap["result"]["sample_rate"] == 48_000
        call = StubVoxCPM.instances[0].calls[0]
        assert call["text"] == "Zapłacę dwanaście złotych pięćdziesiąt groszy o czternastej trzydzieści."
        assert call["prompt_text"] == "Mam pięć złotych."
        assert Path(call["reference_wav_path"]).is_file() and call["reference_wav_path"] == call["prompt_wav_path"]
        assert stub_libs.seeds == [5]
        assert service.status()["engine"]["reference"]["max_files"] == 1
    finally:
        service.close()


# --- kontrakt ze źródłami voxcpm 2.0.3 (opcjonalny) -------------------------------------------------------------------
SOURCE_DIR = os.environ.get("SVM_VOXCPM_SOURCE_DIR")
needs_source = pytest.mark.skipif(not SOURCE_DIR, reason="ustaw SVM_VOXCPM_SOURCE_DIR na katalog z rozpakowanym wheel voxcpm 2.0.3")


def _class_functions(path: Path, class_name: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return {f.name: f for f in cls.body if isinstance(f, ast.FunctionDef)}


def _arg_defaults(func: ast.FunctionDef) -> dict[str, Any]:
    args = func.args.args
    defaults = [None] * (len(args) - len(func.args.defaults)) + list(func.args.defaults)
    return {a.arg: (ast.literal_eval(d) if d is not None else inspect.Parameter.empty) for a, d in zip(args, defaults)}


@needs_source
def test_adapter_arguments_exist_in_the_real_signatures() -> None:
    funcs = _class_functions(Path(SOURCE_DIR) / "voxcpm" / "core.py", "VoxCPM")
    from_pretrained = _arg_defaults(funcs["from_pretrained"])
    generate = _arg_defaults(funcs["_generate"])
    assert set(vx.FROM_PRETRAINED_KWARGS) <= set(from_pretrained)
    assert set(vx.GENERATE_KWARGS) <= set(generate)
    assert from_pretrained["hf_model_id"] == vx.MODEL_ID
    assert generate["cfg_value"] == vx.DEFAULT_CFG_VALUE and generate["inference_timesteps"] == vx.DEFAULT_TIMESTEPS


@needs_source
def test_the_stub_mirrors_the_real_signatures() -> None:
    funcs = _class_functions(Path(SOURCE_DIR) / "voxcpm" / "core.py", "VoxCPM")
    real_generate = [a for a in _arg_defaults(funcs["_generate"]) if a != "self"]
    real_from_pretrained = [a for a in _arg_defaults(funcs["from_pretrained"]) if a != "cls"]
    assert list(inspect.signature(StubVoxCPM._generate).parameters)[1:] == real_generate
    assert list(inspect.signature(StubVoxCPM.generate).parameters)[1:] == real_generate
    stub_params = inspect.signature(StubVoxCPM.from_pretrained).parameters  # klasowa metoda: bez cls
    assert list(stub_params)[:-1] == real_from_pretrained
    assert list(stub_params.values())[-1].kind is inspect.Parameter.VAR_KEYWORD


@needs_source
def test_audio_rates_assumed_by_the_adapter_match_the_vae_config() -> None:
    tree = ast.parse((Path(SOURCE_DIR) / "voxcpm" / "modules" / "audiovae" / "audio_vae_v2.py").read_text(encoding="utf-8"))
    cfg = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AudioVAEConfig")
    values = {n.target.id: ast.literal_eval(n.value) for n in cfg.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None}
    assert values["sample_rate"] == vx.REFERENCE_SAMPLE_RATE and values["out_sample_rate"] == vx.EXPECTED_OUTPUT_RATE
