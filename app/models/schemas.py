from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "citizen"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    createdAt: Optional[datetime] = None

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

class CitizenProfileSchema(BaseModel):
    fullName: Optional[str] = ""
    age: Optional[int] = None
    gender: Optional[str] = "Male"
    state: Optional[str] = "Karnataka"
    district: Optional[str] = "Raichur"
    annualIncome: Optional[float] = 0.0
    occupation: Optional[str] = "Farmer"
    category: Optional[str] = "General"
    disabilityStatus: Optional[str] = "No"
    
    # Farmer specific
    landOwnership: Optional[str] = "Owner"
    landArea: Optional[float] = 0.0
    irrigationType: Optional[str] = "Rainfed"
    
    # Student specific
    educationLevel: Optional[str] = "Undergraduate"
    institutionType: Optional[str] = "Government"
    isCurrentStudent: Optional[str] = "Yes"
    
    # Business specific
    businessType: Optional[str] = "Micro Enterprise"
    udyamRegistered: Optional[str] = "No"
    annualTurnover: Optional[float] = 0.0
    
    # Livelihood / Household
    employmentStatus: Optional[str] = "Self-Employed"
    rationCardType: Optional[str] = "BPL"

class SchemeRules(BaseModel):
    minAge: Optional[int] = None
    maxAge: Optional[int] = None
    minIncome: Optional[float] = None
    maxIncome: Optional[float] = None
    eligibleOccupations: Optional[List[str]] = ["All"]
    eligibleStates: Optional[List[str]] = ["All India"]
    landOwnershipRequired: Optional[bool] = False
    maxLandArea: Optional[float] = None
    educationRequired: Optional[List[str]] = []
    categoryRequired: Optional[List[str]] = ["All"]
    genderRequired: Optional[str] = "All"
    rationCardRequired: Optional[List[str]] = []
    specialConditions: Optional[List[str]] = []

class SchemeModel(BaseModel):
    id: Optional[str] = None
    schemeName: str
    description: str
    category: str
    governmentDepartment: str
    state: str
    eligibilityRules: Optional[SchemeRules] = None
    eligibilityCriteria: Optional[List[str]] = []
    benefits: Optional[Dict[str, Any]] = None
    requiredDocuments: Optional[List[str]] = []
    applicationProcedure: Optional[List[str]] = []
    importantConditions: Optional[List[str]] = []
    officialURL: str
    sourceReferences: Optional[Dict[str, Any]] = None
    lastVerifiedAt: Optional[str] = "October 2026"

class RagQueryRequest(BaseModel):
    question: str
    category: Optional[str] = None
    state: Optional[str] = None
    language: Optional[str] = "English"

class RagSourceItem(BaseModel):
    schemeName: str
    documentName: Optional[str] = ""
    category: Optional[str] = ""
    state: Optional[str] = ""
    officialURL: Optional[str] = ""
    snippet: Optional[str] = ""
    score: Optional[float] = 0.0

class RagQueryResponse(BaseModel):
    answer: str
    sources: List[RagSourceItem]
    followUpQuestions: Optional[List[str]] = []

class EligibilityCheckRequest(BaseModel):
    profile: Dict[str, Any]
    schemeId: Optional[str] = None

class EligibilityCheckResult(BaseModel):
    status: str  # POTENTIALLY ELIGIBLE | NOT ELIGIBLE | INSUFFICIENT INFORMATION
    satisfiedConditions: List[str]
    unsatisfiedConditions: List[str]
    missingInformation: List[str]
    score: float

class DocumentRecord(BaseModel):
    id: Optional[str] = None
    documentName: str
    schemeId: Optional[str] = None
    schemeName: Optional[str] = None
    category: str
    state: str
    governmentDepartment: Optional[str] = ""
    sourceURL: str
    localFilePath: Optional[str] = ""
    processingStatus: str = "vectorized"
    chunkCount: Optional[int] = 0
    uploadedAt: Optional[datetime] = None
    verifiedAt: Optional[str] = "October 2026"
