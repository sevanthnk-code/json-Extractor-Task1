import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EducationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    institution: str | None = Field(
        default=None,
        description="School, college, or institution name; null if not stated.",
    )
    degree: str | None = Field(
        default=None,
        description="Degree or qualification exactly as stated; null if absent.",
    )
    field_of_study: str | None = Field(
        default=None,
        description="Field or subject studied; null if absent.",
    )
    start_date: str | None = Field(
        default=None,
        description="Education start date or period as stated; null if absent.",
    )
    end_date: str | None = Field(
        default=None,
        description="Education end or graduation date as stated; null if absent.",
    )


class WorkExperienceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    job_title: str | None = Field(
        default=None,
        description="Position title exactly as stated; null if absent.",
    )
    employer: str | None = Field(
        default=None,
        description="Employer or organization name; null if absent.",
    )
    location: str | None = Field(
        default=None,
        description="Work location as stated; null if absent.",
    )
    start_date: str | None = Field(
        default=None,
        description="Employment start date or period as stated; null if absent.",
    )
    end_date: str | None = Field(
        default=None,
        description="Employment end date or period as stated; null if absent.",
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Responsibilities explicitly listed for this role; empty when none are stated.",
    )
    achievements: list[str] = Field(
        default_factory=list,
        description="Achievements explicitly listed for this role; empty when none are stated.",
    )


class ResumeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    full_name: str | None = Field(
        default=None,
        description="Candidate's full name exactly as stated; null if absent.",
    )
    email: str | None = Field(
        default=None,
        description="Candidate's email address exactly as stated; null if absent.",
    )
    phone: str | None = Field(
        default=None,
        description="Candidate's phone number exactly as stated; null if absent.",
    )
    location: str | None = Field(
        default=None,
        description="Candidate's location exactly as stated; null if absent.",
    )
    professional_summary: str | None = Field(
        default=None,
        description="Professional summary from the resume; null if not provided.",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Skills explicitly listed in the resume; empty when none are stated.",
    )
    education: list[EducationSchema] = Field(
        default_factory=list,
        description="Education entries explicitly present in the resume; empty when none are stated.",
    )
    experience: list[WorkExperienceSchema] = Field(
        default_factory=list,
        description="Work experience entries explicitly present in the resume; empty when none are stated.",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Certifications explicitly listed in the resume; empty when none are stated.",
    )
    projects: list[str] = Field(
        default_factory=list,
        description="Projects explicitly listed in the resume; empty when none are stated.",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("email must be a valid email address")
        return value
