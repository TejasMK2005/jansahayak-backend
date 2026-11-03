import os
import uuid
import logging
from datetime import datetime, timezone
from app.config import settings
from app.services.database import get_db, in_memory_store
from app.services.auth_service import hash_password
from rag.ingestion.loader import document_loader
from rag.processing.chunker import chunker
from rag.retrieval.vectorstore import vector_store

logger = logging.getLogger("jansahayak.seeder")

VERIFIED_SCHEMES = [
    {
        "id": "pm_kisan_001",
        "schemeName": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "description": "Income support scheme by Government of India providing ₹6,000 per year directly to eligible landholding farmer families across India in three equal 4-monthly installments.",
        "category": "Agriculture",
        "governmentDepartment": "Department of Agriculture & Farmers Welfare, Ministry of Agriculture & Farmers Welfare, GoI",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 100,
            "minIncome": 0,
            "maxIncome": 10000000,
            "eligibleOccupations": ["Farmer", "Agriculture"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": True,
            "maxLandArea": 50.0,
            "categoryRequired": ["All"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Must be an individual farmer family owning cultivable land records in their name.",
            "Valid Aadhaar and land RTC/Pahani required.",
            "Must not be an institutional landholder, income tax payer, constitutional post holder, or retired government officer (excluding Class IV)."
        ],
        "benefits": {
            "financial": "₹6,000 per year in 3 equal installments of ₹2,000 directly via DBT into Aadhaar-seeded bank accounts.",
            "details": [
                "Installment 1: April - July (₹2,000)",
                "Installment 2: August - November (₹2,000)",
                "Installment 3: December - March (₹2,000)",
                "Aadhaar-based direct electronic benefit transfer without intermediaries."
            ]
        },
        "requiredDocuments": [
            "Aadhaar Card of all family members",
            "Cultivable Land Record (RTC / Pahani / 7/12 extract / Khata)",
            "Active Bank Account mapped with Aadhaar & NPCI DBT",
            "Active Mobile Number linked to Aadhaar for e-KYC"
        ],
        "applicationProcedure": [
            "Visit the official portal https://pmkisan.gov.in and click on 'New Farmer Registration'.",
            "Select Rural Farmer or Urban Farmer, enter your Aadhaar and mobile number, and submit OTP.",
            "Enter land ownership details including Survey Number, Khasra Number, and land area.",
            "Complete mandatory e-KYC via Aadhaar OTP or Biometric at any CSC center."
        ],
        "importantConditions": [
            "e-KYC is mandatory for receiving installments.",
            "Land records must be updated in the state revenue records.",
            "Income tax payers of previous assessment years are strictly excluded."
        ],
        "officialURL": "https://pmkisan.gov.in",
        "sourceReferences": {
            "portal": "myScheme & PM-KISAN Portal",
            "documentTitle": "PM-KISAN Operational Guidelines 2026"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "raitha_siri_002",
        "schemeName": "Karnataka Raitha Siri Scheme (ರೈತ ಸಿರಿ ಯೋಜನೆ)",
        "description": "Government of Karnataka scheme offering direct financial assistance of ₹10,000 per hectare to promote the cultivation of minor millets (Siri Dhanya) in rainfed and drought-prone taluks.",
        "category": "Agriculture",
        "governmentDepartment": "Department of Agriculture, Government of Karnataka",
        "state": "Karnataka",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 100,
            "minIncome": 0,
            "maxIncome": 10000000,
            "eligibleOccupations": ["Farmer", "Agriculture"],
            "eligibleStates": ["Karnataka"],
            "landOwnershipRequired": True,
            "maxLandArea": 5.0,
            "categoryRequired": ["All"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Resident farmer of Karnataka cultivating minor millets (Navane, Same, Haraka, Oodalu, Baragu, Korale).",
            "Must own cultivable agricultural land in Karnataka.",
            "Must be registered on Karnataka FRUITS portal with valid FID.",
            "Crop must be verified through the Government of Karnataka Crop Survey."
        ],
        "benefits": {
            "financial": "₹10,000 per hectare (up to a maximum of 2 hectares / ₹20,000 per farmer family) credited directly via DBT.",
            "details": [
                "Supports 6 designated minor millets (Siri Dhanya).",
                "Direct credit into Aadhaar-linked bank account based on Crop Survey verification."
            ]
        },
        "requiredDocuments": [
            "Karnataka FRUITS ID (FID)",
            "Land RTC / Pahani document",
            "Aadhaar Card linked to Mobile number",
            "Crop Survey (Bele Darshini) confirmation entry",
            "Aadhaar-seeded Bank Passbook"
        ],
        "applicationProcedure": [
            "Obtain your Farmer ID (FID) on fruits.karnataka.gov.in.",
            "Cultivate designated minor millets during Kharif/Rabi season.",
            "Ensure the crop is recorded during the Department's Joint Crop Survey.",
            "Visit the local Raitha Samparka Kendra (RSK) or submit details on Seva Sindhu.",
            "Incentive is sanctioned by Assistant Director of Agriculture and transferred via DBT."
        ],
        "importantConditions": [
            "Restricted to maximum 2 hectares (₹20,000).",
            "Only designated minor millets qualify; major millets like Ragi and Jowar have separate minimum support price schemes."
        ],
        "officialURL": "https://raitamitra.karnataka.gov.in",
        "sourceReferences": {
            "portal": "Karnataka Raitha Mitra & Seva Sindhu",
            "documentTitle": "Karnataka Agriculture Budget Policy"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "kcc_scheme_003",
        "schemeName": "Kisan Credit Card (KCC) Scheme",
        "description": "Comprehensive institutional credit facility providing subsidized crop loans up to ₹3 Lakhs at 4% effective interest rate to farmers, tenant cultivators, and allied livestock/fishery entrepreneurs.",
        "category": "Agriculture",
        "governmentDepartment": "Ministry of Agriculture & Farmers Welfare / NABARD / RBI",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 75,
            "minIncome": 0,
            "maxIncome": 10000000,
            "eligibleOccupations": ["Farmer", "Agriculture"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": False,
            "maxLandArea": 100.0,
            "categoryRequired": ["All"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Owner cultivators, tenant farmers, sharecroppers, and oral lessees.",
            "Age between 18 and 75 years (co-borrower required if age above 60).",
            "Farmers involved in animal husbandry, dairy, poultry, or fisheries."
        ],
        "benefits": {
            "financial": "Subsidized short-term crop loans up to ₹3,00,000 at 4% effective interest rate (with 3% prompt repayment incentive). Collateral-free up to ₹1,60,000.",
            "details": [
                "Revolving cash credit account with RuPay KCC card.",
                "Flexible repayment linked to harvest and marketing seasons.",
                "Inbuilt crop insurance under PMFBY."
            ]
        },
        "requiredDocuments": [
            "Simplified KCC Application Form",
            "Aadhaar Card / Voter ID / PAN",
            "Land Record (RTC / Pahani / 7/12 extract) or tenancy agreement",
            "Cropping pattern and area declaration"
        ],
        "applicationProcedure": [
            "Download the simplified one-page KCC form from pmkisan.gov.in or visit any bank branch.",
            "Fill in land survey numbers, cropping pattern, and attach Aadhaar and Pahani.",
            "Submit to any Commercial, RRB, or Cooperative bank branch.",
            "Bank is mandated to process and issue RuPay KCC card within 14 working days."
        ],
        "importantConditions": [
            "Prompt repayment required to avail the 3% interest subvention benefit.",
            "Collateral is waived for loans up to ₹1.60 Lakh."
        ],
        "officialURL": "https://www.myscheme.gov.in/schemes/kcc",
        "sourceReferences": {
            "portal": "myScheme & NABARD",
            "documentTitle": "Master Circular - Kisan Credit Card Scheme"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "ssp_postmatric_004",
        "schemeName": "Karnataka State Scholarship Portal (SSP) - Post-Matric Scholarship",
        "description": "Comprehensive scholarship portal providing tuition fee waivers, examination fee reimbursements, and maintenance allowances for SC, ST, OBC, and Minority students studying in PUC, Degree, Engineering, and PG courses.",
        "category": "Education",
        "governmentDepartment": "Social Welfare, Backward Classes Welfare (BCWD) & Minorities Welfare Departments, Govt of Karnataka",
        "state": "Karnataka",
        "eligibilityRules": {
            "minAge": 15,
            "maxAge": 35,
            "minIncome": 0,
            "maxIncome": 250000,
            "eligibleOccupations": ["Student"],
            "eligibleStates": ["Karnataka"],
            "landOwnershipRequired": False,
            "educationRequired": ["Post-Matric (11th & 12th / PUC)", "Diploma / ITI", "Undergraduate", "Postgraduate", "PhD / Research"],
            "categoryRequired": ["SC", "ST", "OBC", "Minority", "EWS"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Domicile of Karnataka State.",
            "Passed Class 10 (SSLC) and enrolled in recognized Post-Matric course (PUC, Diploma, Degree, Engg, Medical, PG).",
            "Family annual income: SC/ST up to ₹2.5 Lakhs; OBC Category-1 up to ₹2.5 Lakhs; OBC 2A/3A/3B up to ₹1.0 Lakh (or ₹2.5L for fee concession).",
            "Minimum 75% attendance in enrolled institution."
        ],
        "benefits": {
            "financial": "Full or partial reimbursement of College Tuition & Exam fees plus monthly maintenance allowance up to ₹15,000/year (hosteller).",
            "details": [
                "Full tuition fee waiver for eligible SC/ST/Cat-1 students.",
                "Vidyasiri food and accommodation stipend (₹1,500/month) for students without government hostel seat."
            ]
        },
        "requiredDocuments": [
            "Student Aadhaar and Parent Aadhaar",
            "SATS ID / College Registration (USN) Number",
            "Caste and Income Certificate RD Number (from Nadakacheri)",
            "College Fee Receipt",
            "Aadhaar-seeded Bank Account (NPCI mapped)"
        ],
        "applicationProcedure": [
            "Register on https://ssp.postmatric.karnataka.gov.in using Aadhaar.",
            "Enter Caste & Income RD numbers (automatically verified against Nadakacheri database).",
            "Select college, university, and enrolled degree.",
            "Submit e-Attestation request for college officer verification.",
            "Scholarship is sanctioned and released via DBT."
        ],
        "importantConditions": [
            "Only one post-matric scholarship per student can be availed.",
            "Must be studying in recognized government or private affiliated college."
        ],
        "officialURL": "https://ssp.postmatric.karnataka.gov.in",
        "sourceReferences": {
            "portal": "Karnataka SSP Portal",
            "documentTitle": "Post-Matric Scholarship Guidelines Karnataka"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "pmegp_msme_005",
        "schemeName": "Prime Minister's Employment Generation Programme (PMEGP)",
        "description": "Credit-linked capital subsidy scheme assisting prospective entrepreneurs to set up new micro-enterprises in manufacturing (up to ₹50 Lakh) and service sectors (up to ₹20 Lakh) with up to 35% government subsidy.",
        "category": "Business",
        "governmentDepartment": "Ministry of Micro, Small and Medium Enterprises (MSME), GoI / KVIC",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 65,
            "minIncome": 0,
            "maxIncome": 10000000,
            "eligibleOccupations": ["Business Owner", "Unemployed", "Self-Employed", "Daily Wage / Unorganized"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": False,
            "categoryRequired": ["All"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Any Indian citizen aged 18 years and above.",
            "Minimum 8th standard pass for manufacturing projects above ₹10 Lakh and service projects above ₹5 Lakh.",
            "Only for NEW units; existing units or units already availing government subsidies are not eligible."
        ],
        "benefits": {
            "financial": "Capital subsidy of 15% to 35% of project cost (up to ₹17.5 Lakh in rural areas). Maximum project cost ₹50 Lakh for manufacturing, ₹20 Lakh for services.",
            "details": [
                "Rural areas: 25% subsidy for General category, 35% for Special (SC/ST/OBC/Women/Minority).",
                "Urban areas: 15% subsidy for General category, 25% for Special.",
                "Bank finances remaining 60% to 75% as term loan & working capital."
            ]
        },
        "requiredDocuments": [
            "Aadhaar Card and PAN Card",
            "Detailed Project Report (DPR)",
            "Educational Qualification Certificate (8th pass or higher)",
            "Caste / Category Certificate (for claiming special subsidy)",
            "Rural Area Certificate from Gram Panchayat (for rural subsidy rate)"
        ],
        "applicationProcedure": [
            "Apply online at https://www.kviconline.gov.in/pmegpeportal/.",
            "Fill in sponsor agency (DIC, KVIC, or KVIB) and upload DPR and KYC.",
            "District Task Force Committee (DTFC) reviews and recommends to the selected bank.",
            "Bank appraises credit and sanctions loan.",
            "Complete mandatory online Entrepreneurship Development Programme (EDP) training."
        ],
        "importantConditions": [
            "Subsidy is locked in a Term Deposit Receipt (TDR) for 3 years before being adjusted against loan principal.",
            "Beneficiary must contribute 5% to 10% own equity."
        ],
        "officialURL": "https://www.kviconline.gov.in/pmegpeportal/",
        "sourceReferences": {
            "portal": "KVIC & Ministry of MSME",
            "documentTitle": "PMEGP Scheme Guidelines 2026"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "mudra_yojana_006",
        "schemeName": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "description": "Collateral-free institutional loan scheme up to ₹20 Lakhs for micro and small non-farm enterprises in manufacturing, processing, trading, and services.",
        "category": "Business",
        "governmentDepartment": "Department of Financial Services, Ministry of Finance, GoI",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 65,
            "minIncome": 0,
            "maxIncome": 10000000,
            "eligibleOccupations": ["Business Owner", "Self-Employed", "Daily Wage / Unorganized"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": False,
            "categoryRequired": ["All"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Any Indian citizen planning or running a non-farm income-generating micro-business.",
            "No collateral security required.",
            "Applicant must not have defaulted with any bank."
        ],
        "benefits": {
            "financial": "100% collateral-free loans in 4 tiers: Shishu (up to ₹50,000), Kishore (₹50,001 to ₹5 Lakh), Tarun (₹5 Lakh to ₹10 Lakh), and Tarun Plus (up to ₹20 Lakh).",
            "details": [
                "Backed by Credit Guarantee Fund for Micro Units (CGFMU).",
                "RuPay MUDRA debit card issued for working capital overdraft."
            ]
        },
        "requiredDocuments": [
            "Identity Proof (Aadhaar / Voter ID / PAN)",
            "Address Proof (Aadhaar / Utility Bill)",
            "Business registration / Udyam Certificate (if existing)",
            "Quotations for machinery/tools to be purchased"
        ],
        "applicationProcedure": [
            "Apply online via udyamimitra.in or walk into any commercial, RRB, or small finance bank branch.",
            "Submit standardized MUDRA application form with project details.",
            "Bank verifies credit history and sanctions loan without collateral.",
            "Funds disbursed directly to equipment suppliers or credited as overdraft."
        ],
        "importantConditions": [
            "Applicable only for non-farm income generating activities.",
            "No processing fee for Shishu and Kishore loans."
        ],
        "officialURL": "https://www.mudra.org.in",
        "sourceReferences": {
            "portal": "MUDRA & Udyami Mitra",
            "documentTitle": "PMMY Operational Guidelines"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "gruha_lakshmi_007",
        "schemeName": "Karnataka Gruha Lakshmi Scheme (ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ)",
        "description": "Flagship Karnataka Government social welfare scheme providing direct financial assistance of ₹2,000 per month (₹24,000 annually) to the female head of every eligible household.",
        "category": "Women",
        "governmentDepartment": "Department of Women and Child Development, Government of Karnataka",
        "state": "Karnataka",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 100,
            "minIncome": 0,
            "maxIncome": 500000,
            "eligibleOccupations": ["Homemaker", "Daily Wage / Unorganized", "Self-Employed", "Farmer", "Unemployed"],
            "eligibleStates": ["Karnataka"],
            "landOwnershipRequired": False,
            "categoryRequired": ["All"],
            "genderRequired": "Female",
            "rationCardRequired": ["BPL", "AAY", "APL"]
        },
        "eligibilityCriteria": [
            "Woman designated as the 'Head of the Family' in the Karnataka State Ration Card (AAY, BPL, or APL).",
            "Resident of Karnataka State.",
            "The woman or her husband must NOT be an Income Tax payer or GST filer."
        ],
        "benefits": {
            "financial": "Direct cash transfer of ₹2,000 per month (₹24,000 per year) credited directly via DBT into the Aadhaar-linked bank account.",
            "details": [
                "Unrestricted direct cash support to empower household financial independence.",
                "Continuous monthly disbursement on scheduled dates."
            ]
        },
        "requiredDocuments": [
            "Karnataka Ration Card Number (Food & Civil Supplies Department)",
            "Aadhaar Card of the woman head of family",
            "Aadhaar Card of the husband",
            "Aadhaar-seeded Bank Account (NPCI mapped)",
            "Mobile number linked to Aadhaar"
        ],
        "applicationProcedure": [
            "Visit https://sevasindhu.karnataka.gov.in or any Grama One, Karnataka One, or Bangalore One center.",
            "Enter Ration Card number to automatically retrieve family data.",
            "Authenticate via Aadhaar OTP or biometric scan.",
            "Confirm bank account details and submit.",
            "Receive application acknowledgment and monthly DBT credit."
        ],
        "importantConditions": [
            "Only ONE woman per ration card is eligible.",
            "Income tax paying or GST filing families are strictly excluded."
        ],
        "officialURL": "https://sevasindhu.karnataka.gov.in",
        "sourceReferences": {
            "portal": "Seva Sindhu Karnataka",
            "documentTitle": "Gruha Lakshmi Government Order 2026"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "ayushman_pmjay_008",
        "schemeName": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) / Arogya Karnataka",
        "description": "World's largest health assurance scheme providing up to ₹5 Lakh cashless hospitalization cover per family per year across empaneled public and private hospitals.",
        "category": "Healthcare",
        "governmentDepartment": "National Health Authority (NHA) & Suvarna Arogya Suraksha Trust (SAST), Karnataka",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 0,
            "maxAge": 115,
            "minIncome": 0,
            "maxIncome": 300000,
            "eligibleOccupations": ["All"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": False,
            "categoryRequired": ["All"],
            "genderRequired": "All",
            "rationCardRequired": ["BPL", "AAY", "APL"]
        },
        "eligibilityCriteria": [
            "Deprived rural and urban households identified under SECC 2011.",
            "All BPL and Antyodaya ration cardholders in Karnataka.",
            "All senior citizens aged 70 years and above are eligible for exclusive ₹5 Lakh cover without income ceiling."
        ],
        "benefits": {
            "financial": "Cashless hospitalization coverage up to ₹5,00,000 per family per year for secondary and tertiary care.",
            "details": [
                "Covers pre-existing diseases from day one.",
                "Covers 3 days pre-hospitalization and 15 days post-hospitalization medicines and diagnostic tests.",
                "Karnataka ArK integration provides 100% free care for BPL and 30% co-payment for APL."
            ]
        },
        "requiredDocuments": [
            "Aadhaar Card",
            "Ration Card (BPL / Antyodaya / APL)",
            "Active Mobile number for OTP e-KYC"
        ],
        "applicationProcedure": [
            "Check eligibility on beneficiary.nha.gov.in or arogya.karnataka.gov.in.",
            "Visit any government hospital or empaneled private hospital Ayushman Mitra desk.",
            "Complete Aadhaar e-KYC and download Ayushman PVC Card.",
            "Show Ayushman Card for instant cashless admission."
        ],
        "importantConditions": [
            "Applicable only for inpatient hospitalization requiring at least 24 hours stay or designated day-care surgeries.",
            "Outpatient (OPD) consultation alone is not covered."
        ],
        "officialURL": "https://pmjay.gov.in",
        "sourceReferences": {
            "portal": "NHA & Arogya Karnataka",
            "documentTitle": "AB-PMJAY Guidelines"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "pmay_gramin_009",
        "schemeName": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        "description": "Rural housing programme providing direct financial grants of ₹1.2 Lakh to ₹1.3 Lakh plus MGNREGA wages and toilet assistance for constructing a disaster-resilient pucca house.",
        "category": "Housing",
        "governmentDepartment": "Ministry of Rural Development, GoI & Rajiv Gandhi Housing Corporation (RGHCL), Karnataka",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 100,
            "minIncome": 0,
            "maxIncome": 180000,
            "eligibleOccupations": ["Daily Wage / Unorganized", "Farmer", "Unemployed", "Homemaker"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": False,
            "categoryRequired": ["All"],
            "genderRequired": "All",
            "rationCardRequired": ["BPL", "AAY"]
        },
        "eligibilityCriteria": [
            "Houseless families or families living in kutcha/dilapidated houses in rural areas.",
            "Must not own a pucca house anywhere in India.",
            "Must not own motorized vehicle or agricultural equipment."
        ],
        "benefits": {
            "financial": "Direct unit grant of ₹1,20,000 (plain) or ₹1,30,000 (difficult areas) + ₹12,000 for toilet under SBM + 90 days MGNREGA wages (~₹28,000). Total benefit ~ ₹1.6 Lakh+.",
            "details": [
                "Phased installment DBT linked to geotagged construction milestones (Foundation, Lintel, Roof, Finishing).",
                "Includes free LPG connection under Ujjwala and electricity under Saubhagya."
            ]
        },
        "requiredDocuments": [
            "Aadhaar Card of all family members",
            "MGNREGA Job Card Number",
            "Land possession certificate / Hakku Patra / Gram Panchayat site allotment",
            "Aadhaar-seeded Bank Account passbook"
        ],
        "applicationProcedure": [
            "Eligible households are identified through Awaas+ survey and validated by Gram Sabha.",
            "Panchayat Development Officer (PDO) conducts geotagged photo inspection using AwaasApp.",
            "Sanction order issued by Zilla Panchayat / RGHCL.",
            "Installments released progressively via DBT upon verified milestone photo uploads."
        ],
        "importantConditions": [
            "House size must be at least 25 sq. meters including a hygienic cooking area.",
            "Contractors or middlemen are strictly prohibited; beneficiary builds the house."
        ],
        "officialURL": "https://pmayg.nic.in",
        "sourceReferences": {
            "portal": "PMAY-G & Ashraya Karnataka",
            "documentTitle": "PMAY-G Framework for Implementation"
        },
        "lastVerifiedAt": "October 2026"
    },
    {
        "id": "atal_pension_010",
        "schemeName": "Atal Pension Yojana (APY)",
        "description": "Government-backed guaranteed monthly pension scheme of ₹1,000 to ₹5,000 for unorganized sector workers starting at age 60, with lifetime continuation for spouse and corpus return to nominee.",
        "category": "Pension",
        "governmentDepartment": "PFRDA, Ministry of Finance, Government of India",
        "state": "All India",
        "eligibilityRules": {
            "minAge": 18,
            "maxAge": 40,
            "minIncome": 0,
            "maxIncome": 500000,
            "eligibleOccupations": ["All"],
            "eligibleStates": ["All India"],
            "landOwnershipRequired": False,
            "categoryRequired": ["All"],
            "genderRequired": "All"
        },
        "eligibilityCriteria": [
            "Any Indian citizen aged between 18 and 40 years.",
            "Must have a savings bank account or post office account with auto-debit facility.",
            "Must NOT be an income tax payer."
        ],
        "benefits": {
            "financial": "Guaranteed minimum monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000, or ₹5,000 per month for life starting at age 60.",
            "details": [
                "Identical pension continues to spouse for life after subscriber's demise.",
                "Full accumulated pension corpus (up to ₹8.5 Lakh) returned to nominee after both subscriber and spouse pass away."
            ]
        },
        "requiredDocuments": [
            "Aadhaar Card",
            "Active Savings Bank Account with auto-debit consent",
            "Mobile number linked to Aadhaar",
            "Spouse and Nominee details"
        ],
        "applicationProcedure": [
            "Visit your bank branch or log in to netbanking/mobile banking.",
            "Fill in the simple 1-page APY registration form.",
            "Choose pension slab (₹1,000 to ₹5,000) and set auto-debit frequency (monthly/quarterly).",
            "e-PRAN card generated instantly via npscra.nsdl.co.in."
        ],
        "importantConditions": [
            "Entry age must be between 18 and 40 years.",
            "Contributions must be maintained until age 60."
        ],
        "officialURL": "https://www.npscra.nsdl.co.in",
        "sourceReferences": {
            "portal": "PFRDA & myScheme",
            "documentTitle": "Atal Pension Yojana Scheme Details"
        },
        "lastVerifiedAt": "October 2026"
    }
]

async def seed_initial_data():
    """Seed demo accounts, verified schemes, and initial RAG vector index."""
    db = get_db()
    logger.info("Initializing demo accounts and verified government scheme registry...")

    # 1. Seed Demo Accounts
    demo_users = [
        {
            "id": "demo_citizen_user",
            "name": "Basavaraj Patil",
            "email": "citizen@demo.in",
            "passwordHash": hash_password("citizen123"),
            "role": "citizen",
            "createdAt": datetime.now(timezone.utc)
        },
        {
            "id": "demo_admin_user",
            "name": "Dr. Ramesh Rao (Admin)",
            "email": "admin@jansahayak.gov.in",
            "passwordHash": hash_password("admin123"),
            "role": "admin",
            "createdAt": datetime.now(timezone.utc)
        }
    ]

    for u in demo_users:
        in_memory_store["users"][u["id"]] = u
        if db is not None:
            try:
                await db.users.update_one(
                    {"email": u["email"]},
                    {"$set": u},
                    upsert=True
                )
            except Exception:
                pass

    # 2. Seed Verified Schemes
    for s in VERIFIED_SCHEMES:
        in_memory_store["schemes"][s["id"]] = s
        if db is not None:
            try:
                await db.schemes.update_one(
                    {"schemeName": s["schemeName"]},
                    {"$set": s},
                    upsert=True
                )
            except Exception:
                pass

    # 3. Seed Initial Demo Citizen Profile (Raichur Farmer, 35y, 2ac)
    farmer_profile = {
        "userId": "demo_citizen_user",
        "fullName": "Basavaraj Patil",
        "age": 35,
        "gender": "Male",
        "state": "Karnataka",
        "district": "Raichur",
        "annualIncome": 150000.0,
        "occupation": "Farmer",
        "category": "OBC",
        "disabilityStatus": "No",
        "landOwnership": "Owner",
        "landArea": 2.0,
        "irrigationType": "Rainfed",
        "educationLevel": "High School",
        "institutionType": "Government",
        "isCurrentStudent": "No",
        "businessType": "None",
        "udyamRegistered": "No",
        "annualTurnover": 0.0,
        "employmentStatus": "Self-Employed",
        "rationCardType": "BPL",
        "updatedAt": datetime.now(timezone.utc)
    }
    in_memory_store["profiles"]["demo_citizen_user"] = farmer_profile
    if db is not None:
        try:
            await db.profiles.update_one(
                {"userId": "demo_citizen_user"},
                {"$set": farmer_profile},
                upsert=True
            )
        except Exception:
            pass

    # 4. Ingest Scheme Documents into Vector Store if not already indexed
    if vector_store.count() == 0:
        logger.info("Vector database empty. Ingesting verified scheme documents into ChromaDB...")
        schemes_dir = settings.SCHEMES_DATA_PATH
        if os.path.exists(schemes_dir):
            for root, _, files in os.walk(schemes_dir):
                for f in files:
                    if f.lower().endswith((".pdf", ".md", ".txt")):
                        fp = os.path.join(root, f)
                        try:
                            pages = document_loader.load_file(fp)
                            chunks = []
                            for p in pages:
                                chunks.extend(chunker.chunk_document(p["text"], p["metadata"]))
                            vector_store.add_documents(chunks)
                            
                            first_meta = pages[0]["metadata"] if pages else {}
                            rec = {
                                "id": str(uuid.uuid4()),
                                "documentName": f,
                                "schemeName": first_meta.get("schemeName", f),
                                "category": first_meta.get("category", "General"),
                                "state": first_meta.get("state", "All India"),
                                "governmentDepartment": first_meta.get("governmentDepartment", ""),
                                "sourceURL": first_meta.get("sourceURL", ""),
                                "localFilePath": fp,
                                "processingStatus": "Vectorized",
                                "chunkCount": len(chunks),
                                "uploadedAt": datetime.now(timezone.utc),
                                "verifiedAt": "October 2026"
                            }
                            in_memory_store["documents"][rec["id"]] = rec
                        except Exception as e:
                            logger.error(f"Error seeding document {f}: {e}")

    logger.info(f"Database and Knowledge Base ready. Total chunks indexed: {vector_store.count()}")
