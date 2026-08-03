from typing import Literal

from pydantic import BaseModel, Field, field_validator


OutputParameter = Literal[
    "time_s",
    "altitude_m",
    "speed_kmh",
    "pitch_deg",
    "roll_deg",
    "x_m",
    "y_m",
]


class SubmitSimulationRequest(BaseModel):
    script_code: str = Field(..., min_length=1)
    report_template_code: str = "standard"
    output_parameters: list[OutputParameter] = Field(default_factory=list)
    timeout_seconds: int = Field(3600, ge=1, le=86400)

    @field_validator("script_code")
    @classmethod
    def normalize_script_code(cls, value):
        return value.strip().upper()

    @field_validator("report_template_code")
    @classmethod
    def validate_report_template_code(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("report_template_code cannot be empty")
        return value
