from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional, Literal, Union
from uuid import UUID
import math

class JobLog(BaseModel):
    id: UUID
    work_request_id: Optional[UUID] = None
    worker_id: UUID
    
    work_type: str
    # Alternativt: Literal hvis du vil begrense til kjente verdier
    # work_type: Literal["bccof_utomhus", "bccof_rigg", "buk_flasker", "gjersjoen_invoiceable", "annet_jobbhvit", ...]
    
    date_completed: date
    hours_worked: float
    
    # units_completed og unit_rate er ofte NaN → vi lar dem være Optional[float]
    units_completed: Optional[float] = None
    unit_rate: Optional[float] = None
    
    comments: Optional[str] = None
    # rating kan være 5.0, nan eller None
    rating: Optional[float] = None
    
    created_at: datetime
    organization_id: UUID
    
    work_leader: Optional[str] = None
    hourly_rate: float
    
    reviewed: Literal["unreviewed", "approved", "rejected", "invoiced"] = "unreviewed"
    
    worker_first_name: str
    worker_last_name: str

    # Valgfri convenience property
    @property
    def worker_full_name(self) -> str:
        return f"{self.worker_first_name} {self.worker_last_name}".strip()

    @property
    def has_rating(self) -> bool:
        return self.rating is not None and not math.isnan(self.rating)

    @property
    def cost(self) -> float:
        """Enkel beregning av kostnad hvis hourly_rate og hours_worked finnes"""
        if self.hours_worked is None or self.hourly_rate is None:
            return 0.0
        return round(self.hours_worked * self.hourly_rate, 2)

    # Håndterer NaN-verdier fra JSON/pandas
    @field_validator("units_completed", "unit_rate", "rating", mode="before")
    @classmethod
    def empty_nan_to_none(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

class User(BaseModel):
    id: UUID
    user_id: UUID               # ser ut til å være duplikat av 'id' – beholdes likevel
    first_name: str
    last_name: Optional[str] = None   # de fleste har, men støtt manglende
    
    phone: Optional[str] = None       # kan være tom streng eller None
    role: Literal["member", "admin", "other", "parent"] = "member"
    
    availability_notes: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    organization_id: UUID
    
    monthly_goal: Optional[float] = None     # ser ut som int i data, men float er tryggere
    
    date_of_birth: Optional[date] = None
    age_category: Literal["U16", "U18", "O18", "Unknown", "U14", "Senior"] = "Unknown"
    
    bank_account_number: Optional[str] = None   # norsk kontonummer som streng (med/uten punktum)
    
    # custom_id har både int/float og nan → vi konverterer nan → None
    custom_id: Optional[int] = None
    
    email: Optional[EmailStr] = None
    
    # Convenience properties
    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name.strip()

    @property
    def age(self) -> Optional[int]:
        """Enkel alder-beregning basert på dagens dato (2026-02-24)"""
        if not self.date_of_birth:
            return None
        today = date(2026, 2, 24)
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

    # Håndter nan i custom_id
    @field_validator("custom_id", mode="before")
    @classmethod
    def nan_to_none(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return None
        if isinstance(v, float) and v.is_integer():
            return int(v)
        return v

    # Valgfri: normaliser phone (f.eks. fjern mellomrom, men her holder vi det enkelt)
    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, v):
        if v == "":
            return None
        return v

class WorkRequest(BaseModel):
    id: UUID
    
    requester_id: UUID           # Den som opprettet forespørselen (ofte admin/koordinator)
    title: str
    description: str
    location: str
    
    payment_type: Literal["hourly", "fixed", "unit_based", "other"] = "hourly"
    
    # Betalingsdetaljer – ofte None i hourly-jobbene
    hourly_rate: Optional[float] = None
    fixed_fee: Optional[float] = None
    base_fee: Optional[float] = None
    unit_name: Optional[str] = None
    unit_rate: Optional[float] = None
    
    estimated_hours: Optional[float] = None
    
    desired_start_date: date     # 'YYYY-MM-DD' streng parses til date
    
    status: Literal[
        "draft", "pending", "approved", "assigned", "in_progress", 
        "completed", "cancelled", "rejected"
    ] = "pending"
    
    is_priority: bool = False
    needs_coordinator: bool = False
    assigned_to: Optional[UUID] = None          # worker_id hvis tildelt én person?
    
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    organization_id: UUID
    
    is_full: bool = False                       # Ser ut til å bety "fullt besatt" / ingen flere plasser
    
    contact_person: Optional[str] = None
    contact_person_id: Optional[UUID] = None    # Ofte samme som requester_id eller annen person
    
    completed_at: Optional[datetime] = None
    
    # Aldersfordeling – estimert antall arbeidere per kategori
    estimated_u16_workers: int = 0
    estimated_u18_workers: int = 0
    estimated_o18_workers: int = 0

    # # Valgfri: total estimert antall arbeidere
    # @property
    # def total_estimated_workers(self) -> int:
    #     return self.estimated_u16_workers + self.estimated_u18_workers + self.estimated_o18_workers

    # # Valgfri: enkel status-indikator
    # @property
    # def is_active(self) -> bool:
    #     return self.status in ("approved", "assigned", "in_progress")

    # # Håndter eventuelle rare verdier (f.eks. hvis noe kommer som streng eller None)
    # @field_validator("estimated_hours", mode="before")
    # @classmethod
    # def validate_estimated_hours(cls, v):
    #     if v is None or (isinstance(v, float) and v != v):  # nan
    #         return None
    #     return float(v)

class HistoricalJobEntry(BaseModel):
    date_completed: datetime                    # Kun dato-delen (uten tid, siden alle er midnatt)
    worker_name: str                        # Fullt navn som én streng
    comments: Optional[str] = None
    hours_worked: float                     # Kan være ~1.0 (rundingsfeil fra float)
    units_completed: Optional[int] = None # Ofte None eller 0
    
    date_of_birth: Optional[date] = None    # NaT → None
    bank_account_number: Optional[str] = None  # Ofte None, ellers streng (ikke float)
    email: Optional[str] = None
    
    role: Literal["genf", "mentor", "hjelpementor"] = "genf"  #
    work_type: str                          # Eks: bccof_vask, bccof_rigg, ...
    season: str                             # Format: '23/24', '24/25' osv.

    # Valgfri: normaliserte/berikede egenskaper
    @property
    def is_recent(self) -> bool:
        """Eksempel: jobb fra inneværende eller forrige sesong (basert på 2026-02-24)"""
        current_year = 2026
        try:
            start, end = map(int, self.season.split("/"))
            return start >= current_year - 2
        except:
            return False

    @property
    def hours_rounded(self) -> float:
        """Runder til nærmeste 0.25 eller 0.5 – typisk for timeregistrering"""
        return round(self.hours_worked * 4) / 4

    # Håndter NaN / NaT / rare verdier fra pandas-eksport
    @field_validator("date_completed", mode="before")
    @classmethod
    def parse_date(cls, v):
        if hasattr(v, "to_pydatetime"):  # pandas Timestamp
            return v.date()
        if isinstance(v, datetime):
            return v.date()
        return v

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def nat_to_none(cls, v):
        if v is None or (hasattr(v, "isna") and v.isna()) or (isinstance(v, float) and math.isnan(v)):
            return None
        if hasattr(v, "to_pydatetime"):
            return v.date()
        if isinstance(v, datetime):
            return v.date()
        return v

    @field_validator("bank_account_number", mode="before")
    @classmethod
    def normalize_bank_account(cls, v):
        if v is None:
            return None
        
        # pandas → float
        if isinstance(v, float):
            if math.isnan(v) or v == 0:
                return None
            # Bruk str() først – mye tryggere enn int(float)
            s = f"{v:.0f}"              # fjerner .0 og vitenskapelig notasjon
            return s if s.isdigit() else None
        
        # Hvis det allerede er int eller streng
        if isinstance(v, int):
            return str(v)
        
        if isinstance(v, str):
            # Fjern punktum/mellomrom osv om ønskelig
            cleaned = v.replace(".", "").replace(" ", "")
            return cleaned if cleaned.isdigit() else v.strip()
        
        return str(v).strip()

    @field_validator("units_completed", "hours_worked", mode="before")
    @classmethod
    def nan_to_none_or_zero(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return None if cls.__name__ == "units_completed" else 0.0
        return v
    
    @field_validator("units_completed", mode="before")
    @classmethod
    def clean_units(cls, v):
        # Debug – fjern senere
        # print(f"units raw: {type(v).__name__} {v!r}")

        if v is None:
            return None

        if hasattr(v, 'isna') and v.isna():   # pandas NA / NaT
            return None

        if isinstance(v, float):
            if math.isnan(v):
                return None
            # Bare aksepter hvis det er et "ekte" heltall
            if v.is_integer() and abs(v) < 2**63:  # for å unngå rare float-greier
                return int(v)
            return None   # ← viktig: IKKE kast feil, bare None

        if isinstance(v, int):
            return v

        # alt annet – prøv å konvertere, ellers None
        try:
            f = float(v)
            if math.isnan(f):
                return None
            if f.is_integer():
                return int(f)
        except Exception:
            pass

        return None

    # Fjern den gamle kombinerte validatoren for units_completed + hours_worked
    # eller behold kun for hours_worked hvis du vil
    @field_validator("hours_worked", mode="before")
    @classmethod
    def clean_hours(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return 0.0
        return v