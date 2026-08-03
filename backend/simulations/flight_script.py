from dataclasses import dataclass
from typing import Any


class ScriptValidationError(ValueError):
    def __init__(self, message, path="$"):
        super().__init__(message)
        self.path = path


@dataclass(frozen=True)
class TestPoint:
    point_id: str
    altitude_m: float
    speed_kmh: float
    duration_s: float
    pitch_deg: float = 2.0
    roll_deg: float = 0.0

    @classmethod
    def from_dict(cls, value: dict[str, Any], index: int):
        if not isinstance(value, dict):
            raise ScriptValidationError(f"Test point #{index + 1} must be an object", f"$.test_points[{index}]")

        initial = value.get("initial_conditions", {})
        if not isinstance(initial, dict):
            raise ScriptValidationError(
                f"Invalid initial_conditions in test point #{index + 1}",
                f"$.test_points[{index}].initial_conditions",
            )

        try:
            point = cls(
                point_id=str(value.get("id", "")).strip(),
                altitude_m=float(initial["altitude_m"]),
                speed_kmh=float(initial["speed_kmh"]),
                duration_s=float(value.get("duration_s", 0)),
                pitch_deg=float(initial.get("pitch_deg", 2.0)),
                roll_deg=float(initial.get("roll_deg", 0.0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ScriptValidationError(
                f"Invalid altitude, speed or duration in test point #{index + 1}",
                f"$.test_points[{index}]",
            ) from exc

        if not point.point_id:
            raise ScriptValidationError(f"Test point #{index + 1} requires id", f"$.test_points[{index}].id")
        if not 0 <= point.altitude_m <= 30000:
            raise ScriptValidationError(
                f"{point.point_id} altitude must be between 0 and 30000 m",
                f"$.test_points[{index}].initial_conditions.altitude_m",
            )
        if not 1 <= point.speed_kmh <= 3000:
            raise ScriptValidationError(
                f"{point.point_id} speed must be between 1 and 3000 km/h",
                f"$.test_points[{index}].initial_conditions.speed_kmh",
            )
        if not 1 <= point.duration_s <= 600:
            raise ScriptValidationError(
                f"{point.point_id} duration must be between 1 and 600 s",
                f"$.test_points[{index}].duration_s",
            )

        return point


@dataclass(frozen=True)
class FlightScript:
    schema_version: str
    subject_code: str
    subject_name: str
    test_points: tuple[TestPoint, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]):
        if not isinstance(value, dict):
            raise ScriptValidationError("Flight script root must be a JSON object")

        schema_version = str(value.get("schema_version", ""))
        if schema_version != "1.0":
            raise ScriptValidationError("Only FlightScript JSON 1.0 is supported", "$.schema_version")

        subject = value.get("subject", {})
        if not isinstance(subject, dict):
            raise ScriptValidationError("subject must be an object", "$.subject")

        points = value.get("test_points", [])
        if not isinstance(points, list) or not points:
            raise ScriptValidationError("At least one test point is required", "$.test_points")
        if len(points) > 100:
            raise ScriptValidationError("A simulation can include at most 100 test points", "$.test_points")

        parsed = tuple(TestPoint.from_dict(point, index) for index, point in enumerate(points))
        point_ids = [point.point_id for point in parsed]
        if len(point_ids) != len(set(point_ids)):
            raise ScriptValidationError("Test point id must be unique", "$.test_points")

        return cls(
            schema_version=schema_version,
            subject_code=str(subject.get("code", "")).strip() or "custom",
            subject_name=str(subject.get("name", "")).strip() or "Unnamed flight subject",
            test_points=parsed,
        )
