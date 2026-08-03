import ctypes
import math
from abc import ABC, abstractmethod
from pathlib import Path

from backend.simulations.contracts import ModelSpec
from backend.simulations.flight_script import TestPoint


class SimulationError(RuntimeError):
    pass


class SimulationAdapter(ABC):
    name = "unknown"

    @abstractmethod
    def simulate(self, point: TestPoint) -> list[dict[str, float]]:
        pass


def _row(time_s, altitude_m, speed_kmh, pitch_deg, roll_deg, x_m, y_m):
    return {
        "time_s": round(time_s, 3),
        "altitude_m": round(altitude_m, 3),
        "speed_kmh": round(speed_kmh, 3),
        "pitch_deg": round(pitch_deg, 3),
        "roll_deg": round(roll_deg, 3),
        "x_m": round(x_m, 3),
        "y_m": round(y_m, 3),
    }


class PythonMockAdapter(SimulationAdapter):
    def __init__(self, name="Python Mock v1.0"):
        self.name = name

    def simulate(self, point):
        if point.speed_kmh < 20:
            raise SimulationError("Trim failed: speed is below model valid range")

        dt = 0.5
        count = min(int(point.duration_s / dt) + 1, 1201)
        speed_ms = point.speed_kmh / 3.6
        rows = []

        for index in range(count):
            t = index * dt
            rows.append(
                _row(
                    t,
                    point.altitude_m + 12 * math.sin(t / 5),
                    point.speed_kmh + 3 * math.sin(t / 3),
                    point.pitch_deg + 1.8 * math.sin(t / 4),
                    point.roll_deg + 4 * math.sin(t / 6),
                    speed_ms * t,
                    20 * math.sin(t / 8),
                )
            )

        return rows


class NativeRow(ctypes.Structure):
    _fields_ = [
        ("time_s", ctypes.c_double),
        ("altitude_m", ctypes.c_double),
        ("speed_kmh", ctypes.c_double),
        ("pitch_deg", ctypes.c_double),
        ("roll_deg", ctypes.c_double),
        ("x_m", ctypes.c_double),
        ("y_m", ctypes.c_double),
    ]


class NativeLibraryAdapter(SimulationAdapter):
    def __init__(self, library_path: Path, name="Native Library v1.0", interface_version="1.0"):
        library_path = library_path.resolve()
        if interface_version != "1.0":
            raise SimulationError(f"Unsupported native interface version: {interface_version}")
        if not library_path.is_file():
            raise SimulationError(f"Native library does not exist: {library_path}")
        if library_path.suffix.lower() not in {".so", ".dll", ".dylib"}:
            raise SimulationError(f"Unsupported native library type: {library_path.suffix}")

        self.name = name
        self._library = ctypes.CDLL(str(library_path))
        self._simulate = self._library.simulate_point
        self._simulate.argtypes = [
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.POINTER(NativeRow),
            ctypes.c_int,
        ]
        self._simulate.restype = ctypes.c_int

    def simulate(self, point):
        dt = 0.5
        capacity = min(int(point.duration_s / dt) + 1, 1201)
        buffer = (NativeRow * capacity)()
        count = self._simulate(
            point.altitude_m,
            point.speed_kmh,
            point.duration_s,
            point.pitch_deg,
            point.roll_deg,
            dt,
            buffer,
            capacity,
        )

        if count == -2:
            raise SimulationError("Native trim failed: speed is below model valid range")
        if count < 0:
            raise SimulationError(f"Native algorithm returned error code {count}")

        return [
            _row(
                value.time_s,
                value.altitude_m,
                value.speed_kmh,
                value.pitch_deg,
                value.roll_deg,
                value.x_m,
                value.y_m,
            )
            for value in buffer[:count]
        ]


def create_adapter(model: ModelSpec):
    if model.model_type == "python_mock":
        return PythonMockAdapter(model.model_name)
    if model.model_type == "native":
        if not model.model_path:
            raise SimulationError("Native model requires model_path")
        return NativeLibraryAdapter(
            Path(model.model_path),
            name=model.model_name,
            interface_version=model.interface_version,
        )
    raise SimulationError(f"Unknown model type: {model.model_type}")
