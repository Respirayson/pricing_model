# =========================================================

# 1) Customer List / Fuzzy Search

# =========================================================

```python
@dataclass
class SearchCustomersInput:
    name_contains: Optional[str] = None
    customer_ids: Optional[List[str]] = None
    is_enterprise: Optional[bool] = None
    region_code: Optional[str] = None
    page: int = 1
    page_size: int = 20

@dataclass
class SearchCustomersOutput:
    total: int
    customer_ids: List[str]
    names: List[str]
    is_enterprise_flags: List[bool]
    star_levels: List[Optional[int]]
    region_codes: List[str]
```

# =========================================================

# 2) Customer Star Level Query

# =========================================================

```python
@dataclass
class GetCustomerStarInput:
    customer_id: str

@dataclass
class GetCustomerStarOutput:
    customer_id: str
    star_level: Optional[int]
    updated_at: Optional[str]  # ISO8601
```

# =========================================================

# 3) Customer Document Information Query

# =========================================================

```python
@dataclass
class GetCustomerDocumentInfoInput:
    customer_id: Optional[str] = None
    doc_type: Optional[Literal["ID_CARD","PASSPORT","BIZ_LICENSE"]] = None
    doc_no: Optional[str] = None

@dataclass
class GetCustomerDocumentInfoOutput:
    customer_id: Optional[str]
    doc_type: Optional[str]
    doc_no: Optional[str]
    name: Optional[str]
    verified: Optional[bool]
    expire_date: Optional[str]  # YYYY-MM-DD
```

# =========================================================

# 4) Key Person Details

# =========================================================

```python
@dataclass
class GetKeyPersonDetailInput:
    customer_id: Optional[str] = None
    person_id: Optional[str] = None

@dataclass
class GetKeyPersonDetailOutput:
    person_id: Optional[str]
    name: Optional[str]
    role: Optional[str]
    mobile: Optional[str]
    email: Optional[str]
```

# =========================================================

# 5) Contact List

# =========================================================

```python
@dataclass
class ListContactsInput:
    customer_id: str
    page: int = 1
    page_size: int = 50

@dataclass
class ListContactsOutput:
    total: int
    contact_ids: List[str]
    names: List[str]
    mobiles: List[Optional[str]]
    emails: List[Optional[str]]
    roles: List[Optional[str]]
```

# =========================================================

# 6) Participant List

# =========================================================

```python
@dataclass
class ListParticipantsInput:
    customer_id: str
    page: int = 1
    page_size: int = 50

@dataclass
class ListParticipantsOutput:
    total: int
    participant_ids: List[str]
    names: List[str]
    roles: List[Optional[str]]
    mobiles: List[Optional[str]]
    emails: List[Optional[str]]
```

# =========================================================

# 7) Group Device List

# =========================================================

```python
@dataclass
class ListGroupDevicesInput:
    customer_id: str
    page: int = 1
    page_size: int = 50

@dataclass
class ListGroupDevicesOutput:
    total: int
    device_ids: List[str]
    device_types: List[Optional[str]]
    msisdns: List[Optional[str]]
    statuses: List[Optional[str]]  # e.g., ACTIVE/SUSPENDED
    remarks: List[Optional[str]]
```

# =========================================================

# 8) Priority Customer Information

# =========================================================

```python
@dataclass
class GetPriorityCustomerInfoInput:
    customer_id: str

@dataclass
class GetPriorityCustomerInfoOutput:
    customer_id: str
    is_priority: bool
    priority_level: Optional[str]  # e.g., GOLD/PLATINUM
    effective_since: Optional[str] # ISO8601
    notes: Optional[str]
```

# =========================================================

# 9) Public Network Document Verification

# =========================================================

```python
@dataclass
class VerifyDocumentPublicNetInput:
    doc_type: Literal["ID_CARD","PASSPORT","BIZ_LICENSE"]
    doc_no: str
    name: str

@dataclass
class VerifyDocumentPublicNetOutput:
    passed: bool
    score: Optional[float]
    reason: Optional[str]
    verified_at: Optional[str]  # ISO8601
```

# =========================================================

# 10) Real-Name Authentication Status Query

# =========================================================

```python
@dataclass
class CheckRealNameStatusInput:
    customer_id: Optional[str] = None
    msisdn: Optional[str] = None

@dataclass
class CheckRealNameStatusOutput:
    is_real_named: bool
    method: Optional[str]          # e.g., OCR+LIVENESS
    verified_at: Optional[str]     # ISO8601
    verifier: Optional[str]        # Channel / institution
```

# =========================================================

# 11) Precheck One-ID-Five-Numbers

# =========================================================

```python
@dataclass
class PrecheckOneIdFiveNumbersInput:
    id_card_no: str
    name: Optional[str] = None

@dataclass
class PrecheckOneIdFiveNumbersOutput:
    hit: bool
    numbers: List[str]             # 0~5 matched numbers
    risk_level: Optional[str]      # LOW/MEDIUM/HIGH
    checked_at: str                # ISO8601
```

# =========================================================

# 12) Query One-ID-Five-Numbers Information

# =========================================================

```python
@dataclass
class QueryOneIdFiveNumbersInput:
    id_card_no: str

@dataclass
class QueryOneIdFiveNumbersOutput:
    numbers: List[str]
    activation_states: List[Optional[str]]  # aligned with numbers, e.g., ACTIVE/SUSPENDED
    since_dates: List[Optional[str]]        # aligned with numbers, YYYY-MM-DD
```

# =========================================================

# 13) Industry One-ID-Multi-SIM Check

# =========================================================

```python
@dataclass
class IndustryOneIdMultiSIMCheckInput:
    id_card_no: str
    industry_code: Optional[str] = None  # optional industry identifier

@dataclass
class IndustryOneIdMultiSIMCheckOutput:
    valid: bool
    count: int
    carrier_codes: List[str]             # e.g., ["CMCC","CUCC"]
    reason: Optional[str]
```

# =========================================================

# 14) Onboarding Photo Information

# =========================================================

```python
@dataclass
class GetOnboardingPhotoInfoInput:
    customer_id: str
    limit: int = 10

@dataclass
class GetOnboardingPhotoInfoOutput:
    photo_ids: List[str]
    taken_at: List[str]                  # ISO8601, aligned with photo_ids
    channels: List[Optional[str]]        # capture channels, aligned with photo_ids
    notes: List[Optional[str]]
```

