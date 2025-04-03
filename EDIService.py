"""
EDI 837P (Professional) Service Module

This module provides functionality to convert healthcare claim data from JSON format
to EDI 837P (Professional) format. It handles the conversion of billing provider,
subscriber, claim, and service line information into the standard EDI format.

The module includes validation for required fields and data formats, and provides
structured data classes for better type safety and data handling.
"""

import enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from pydantic import BaseModel, Field, validator

class SegmentHeader(enum.Enum):
    InterchangeControl = "ISA"
    FunctionalGroup = "GS"
    TransactionSetHeader = "ST"
    BeginningHierarchicalTransaction = "BHT"
    HierarchicalLevel = "HL"
    Provider = "PRV"
    Name = "NM1"
    ContactInformation = "PER"
    AddressLine1 = "N3"
    CityStatePostalCode = "N4"
    SubscriberInformation = "SBR"
    Reference = "REF"
    DateTimePeriod = "DTP"
    Demographics = "DMG"
    ServiceLine = "SV1"
    ServiceLineNumber = "LX"
    Claim = "CLM"
    HealthCareInformation = "HI"
    TransactionSetTrailer = "SE"
    FunctionalGroupTrailer = "GE"
    InterchangeControlTrailer = "IEA"
    Payer = "PR"

class ProviderType(enum.Enum):
    Billing = "BI"
    Performing = "PE"

class RelationshipToSubscriber(enum.Enum):
    Self = "18"
    Spouse = "01"
    Child = "19"
    Other = "21"

class EntityIdentifierCode(enum.Enum):
    Submitter = "41"
    Receiver = "40"
    BillingProvider = "85"
    Subscriber = "IL"
    Patient = "QC"

class ReferenceIdentificationQualifier(enum.Enum):
    TaxonomyCode = "PXC"
    NationalProviderIdentifier = "XX"
    MemberId = "MI"
    EmployerIdentificationNumber = "EI"

class ClaimFilingIndicatorCode(enum.Enum):
    BlueCrossBlueShield = "BL"
    Medicaid = "MC"
    Medicare = "MB"
    Commercial = "CI"
    Unknown = "ZZ"

class PaymentResponsibilityLevelCode(enum.Enum):
    Primary = "P"
    Secondary = "S"
    Tertiary = "T"

class HierarchicalLevelCode(enum.Enum):
    InformationSource = "20"
    Subscriber = "22"
    Dependent = "23"

class EDI837Builder:
    """
    A class for building EDI 837 healthcare claim files.
    
    This class provides a structured way to create an EDI 837 transaction set
    for healthcare claim submissions.
    """
    
    def __init__(self, 
                 version: str = "005010X222A1"):
        """
        Initialize an EDI 837 builder with required identification information.
        
        Args:
            sender_id: Trading partner ID of the sender
            sender_name: Name of the sender
            receiver_id: Trading partner ID of the receiver
            receiver_name: Name of the receiver
            is_production: Whether this is a production or test file
            version: The version of the 837 specification (default is 005010X222A1 for Professional)
        """

        self.version = version
        
        # Segment terminators and delimiters
        self.segment_terminator = "~"
        self.element_separator = "*"
        self.sub_element_separator = ">"
        
        # Initialize claims data
        self.submitter = {}
        self.billing_providers = []
        self.subscribers = []
        self.patients = []
        self.service_lines = []
        self.rendering_providers = []
            
        # Tracking for hierarchical levels
        self.hl_count = 0

        # Contact information
        self.contact_info_map = {}
        self.segment_count = 1

        #Provider Maps
        self.provider_map = {}
        self.has_dependents = False

    def add_billing_provider(self, 
                           npi: str,
                           taxonomy_code: str,
                           employer_id: str,
                           address: Dict[str, str],
                           organization_name: Optional[str] = None,
                           last_name: Optional[str] = None,
                           first_name: Optional[str] = None,
                           contactInfo: Optional[Dict] = None) -> int:
        """
        Add a billing provider to the EDI file.
        
        Args:
            npi: National Provider Identifier
            taxonomy_code: Healthcare Provider Taxonomy Code
            employer_id: Employer Identification Number (Tax ID)
            address: Dict containing address1, city, state, postalCode
            organization_name: Name if provider is an organization
            last_name: Last name if provider is an individual
            first_name: First name if provider is an individual
            
        Returns:
            int: Index of the billing provider in the internal list
        """
        provider = {
            "npi": npi,
            "taxonomyCode": taxonomy_code,
            "employerId": employer_id,
            "address": address
        }
        
        if organization_name:
            provider["organizationName"] = organization_name
        else:
            provider["lastName"] = last_name
            provider["firstName"] = first_name

        if contactInfo: 
            
            name = contactInfo.get("name", "")
            phone_number = contactInfo.get("phoneNumber", "")
            key_to_check = f"{name}_{phone_number})"
            if not  key_to_check in self.contact_info_map: 
                self.contact_info_map[key_to_check] = "billing"
                provider["contactInfo"] = contactInfo
                
        self.billing_providers.append(provider)
        return len(self.billing_providers) - 1
    
    def add_subscriber(self, 
                     member_id: str,
                     last_name: str,
                     first_name: str,
                     address: Dict[str, str], 
                     birth_date: str,
                     gender: str,
                     billing_provider_index: int,
                     payment_responsibility_code: PaymentResponsibilityLevelCode = PaymentResponsibilityLevelCode.Primary,
                     claim_filing_code: ClaimFilingIndicatorCode = ClaimFilingIndicatorCode.Unknown,
                     is_dependent: bool = False,
                     relationship_to_subscriber: str ='') -> int:
        """
        Add a subscriber (insurance policy holder) to the EDI file.
        
        Args:
            member_id: Member identification number
            last_name: Subscriber's last name
            first_name: Subscriber's first name
            address: Dict containing address1, city, state, postalCode
            birth_date: Date of birth in YYYYMMDD format
            gender: Gender code (M/F)
            billing_provider_index: Index of the associated billing provider
            payment_responsibility_code: Code indicating payer responsibility
            claim_filing_code: Code indicating claim filing indicator
            
        Returns:
            int: Index of the subscriber in the internal list
        """
        if is_dependent: 
            self.has_dependents = True
        
        subscriber = {
            "memberId": member_id,
            "lastName": last_name,
            "firstName": first_name,
            "address": address,
            "birthDate": birth_date,
            "gender": gender,
            "billingProviderIndex": billing_provider_index,
            "paymentResponsibilityLevelCode": payment_responsibility_code.value,
            "claimFilingCode": claim_filing_code.value,
            "is_dependent": is_dependent,
            "relationship_to_subscriber" : relationship_to_subscriber
        }
        
        self.subscribers.append(subscriber)
        return len(self.subscribers) - 1
    
    def add_submitter(self,  
                      contactInfo: Optional[Dict] = None):

        # We use this to start building a discrete list of contactInfos for providers.
        self.submitter =  contactInfo;
        if contactInfo:
            name = contactInfo.get("name", "")
            phone_number = contactInfo.get("phoneNumber", "")
            key_to_check = f"{name}_{phone_number})"
            if not  key_to_check in self.contact_info_map: 
                self.contact_info_map[key_to_check] = "submitter"
            
    def add_payer(self, 
             subscriber_index: int, 
             payer_name: str, 
             payer_id: str) -> 'EDI837Builder':
        """
        Add payer information for a specific subscriber.
        
        Args:
            subscriber_index: Index of the subscriber this payer is associated with
            payer_name: Name of the payer (insurance company)
            payer_id: Payer identifier
        
        Returns:
            The builder instance for method chaining
        """
        # Initialize payer_info dictionary if it doesn't exist
        if not hasattr(self, 'payer_info'):
            self.payer_info = {}
        
        # Store payer information indexed by subscriber
        self.payer_info = {
            'organizationName': payer_name,
            'payerId': payer_id
        }
  
    def add_service_facility_location(self,
                                    npi: str,
                                    organization_name: str,
                                    address: Dict[str, str]) -> 'EDI837Builder':
        """
        Add service facility location to the claim.
        
        Args:
            npi: National Provider Identifier for the facility
            organization_name: Name of the facility
            address: Dictionary containing address details with keys:
                    - address1: First line of address
                    - address2: Second line of address (optional)
                    - city: City name
                    - state: State code
                    - postalCode: ZIP/Postal code
        
        Returns:
            The builder instance for method chaining
        """
        self.service_facility = {
            "npi": npi,
            "organizationName": organization_name,
            "address": address
        }

    def add_prior_authorization(self, prior_auth_number: str) -> 'EDI837Builder':
        """
        Add prior authorization reference to the claim.
        
        Args:
            prior_auth_number: Prior authorization number
        
        Returns:
            The builder instance for method chaining
        """
        self.prior_authorization = prior_auth_number
    
    def add_claim_information(self,
                                subscriber_index: int,
                                patient_control_number: str,
                                claim_charge_amount: float,
                                place_of_service_code: str,
                                claim_frequency_code: str = "1",
                                signature_indicator: str = "Y",
                                plan_participation_code: str = "A",
                                release_info_code: str = "Y",
                                benefits_assignment: str = "Y",
                                diagnosis_codes: List[Dict[str, str]] = None) -> 'EDI837Builder':
        """
        Add claim information to the EDI file.
        
        Args:
            subscriber_index: Index of the subscriber this claim is for
            patient_control_number: Patient account or control number
            claim_charge_amount: Total monetary amount charged for the claim
            place_of_service_code: Code indicating where service was provided (e.g., "11" for office)
            claim_frequency_code: Code indicating claim frequency (default "1" for original)
            signature_indicator: Indicator for provider signature on file (default "Y")
            plan_participation_code: Provider participation code (default "A" for Assigned)
            release_info_code: Release of information code (default "Y")
            benefits_assignment: Benefits assignment certification indicator (default "Y")
            diagnosis_codes: List of diagnosis code dictionaries with keys:
                            - diagnosisTypeCode: Code indicating diagnosis type
                            - diagnosisCode: The actual diagnosis code
        
        Returns:
            The builder instance for method chaining
        """
        claim_info = {
            "subscriberIndex": subscriber_index,
            "patientControlNumber": patient_control_number,
            "claimChargeAmount": claim_charge_amount,
            "placeOfServiceCode": place_of_service_code,
            "claimFrequencyCode": claim_frequency_code,
            "signatureIndicator": signature_indicator,
            "planParticipationCode": plan_participation_code,
            "releaseInfoCode": release_info_code,
            "benefitsAssignment": benefits_assignment,
            "diagnosisCodes": diagnosis_codes or []
        }
        
        self.claim_information = claim_info

    def add_service_line(self,
                        subscriber_index: int,
                        patient_index: Optional[int],
                        procedure_code: str,
                        modifier_codes: List[str],
                        charge_amount: float,
                        units: int,
                        service_date: str,
                        rendering_provider_index: Optional[int] = None) -> int:
        """
        Add a service line to the EDI file.
        
        Args:
            subscriber_index: Index of the subscriber
            patient_index: Index of the patient (if not the subscriber)
            procedure_code: Procedure code (CPT/HCPCS)
            modifier_codes: List of modifier codes
            charge_amount: Charge amount for the service
            units: Units of service
            service_date: Date of service in YYYYMMDD format
            rendering_provider_index: Index of the rendering provider (optional)
                
        Returns:
            int: Index of the service line in the internal list
        """
        service_line = {
            "subscriberIndex": subscriber_index,
            "patientIndex": patient_index,
            "procedureCode": procedure_code,
            "modifierCodes": modifier_codes,
            "chargeAmount": charge_amount,
            "units": units,
            "serviceDate": service_date,
            "renderingProviderIndex": rendering_provider_index
        }
            
        self.service_lines.append(service_line)
        return len(self.service_lines) - 1

    def add_rendering_provider(self,
                                npi: str,
                                taxonomy_code: str,
                                last_name: str,
                                first_name: str,
                                employer_id:  str) -> int:
        """
        Add a rendering provider to the EDI file.
        
        Args:
            npi: National Provider Identifier
            last_name: Provider's last name
            first_name: Provider's first name
            taxonomy_code: Healthcare Provider Taxonomy Code
                
        Returns:
            int: Index of the rendering provider in the internal list
        """
        if not hasattr(self, 'rendering_providers'):
            self.rendering_providers = []
                
        provider = {
            "npi": npi,
            "lastName": last_name,
            "firstName": first_name,
            "taxonomyCode": taxonomy_code,
            "employerId": employer_id
        }
            
        self.rendering_providers.append(provider)
        return len(self.rendering_providers) - 1

    def _create_header(self) -> List[str]:
        """Return the hardcoded header segments of the EDI file with proper name segments."""
        # First part of the header with ISA, GS, ST, BHT segments
        
        interchange_control_header = "ISA*00*          *00*          *ZZ*AV09311993     *01*030240928      *240702*1531*^*00501*415133923*0*P*>~"
        function_group_header = "GS*HC*1923294*030240928*20240702*1533*415133923*X*005010X222A1~"
        transaction_set_header = "ST*837*415133923*005010X222A1~"
        bht_header = "BHT*0019*00*1*20240702*1531*CH~"
        submitter_name_segment = "NM1*41*2*Mattel Industries*****46*1234567890~"
        submitter_contact_info_segment = "PER*IC*Ruth Handler*TE*8458130000~"
        reciever_segment = "NM1*40*2*AVAILITY 5010*****46*030240928~"

        hardcoded_header = [
            interchange_control_header,
            function_group_header,
            transaction_set_header,
            bht_header,
            submitter_name_segment,
            submitter_contact_info_segment,
            reciever_segment
        ]
        return hardcoded_header
    
    def _create_billing_provider_loop(self, provider_index: int) -> List[str]:
        """Create segments for a billing provider loop."""
        provider = self.billing_providers[provider_index]
        hardcoded_billing_provider_hl = "HL*1**20*1~"
        # Use hardcoded Hierarchical Level
        segments = [
            hardcoded_billing_provider_hl,
            f"{SegmentHeader.Provider.value}*{ProviderType.Billing.value}*{ReferenceIdentificationQualifier.TaxonomyCode.value}*{provider['taxonomyCode']}~",
        ]

        # Using the simplified name segment method with just entity data and context
        name_segment = self._create_name_segment(
            entity_data=provider,
            context='billing_provider'
        )
        if name_segment: 
            segments.append(name_segment)
            # Address segments
            address2 = ""
            if 'address2' in provider['address']:
                address2 = provider['address']['address2']
            segments.append(f"{SegmentHeader.AddressLine1.value}*{provider['address']['address1']}*{address2}~")
            segments.append(
                f"{SegmentHeader.CityStatePostalCode.value}*{provider['address']['city']}*{provider['address']['state']}*{provider['address']['postalCode']}~"
            )
        
        # Tax ID
        segments.append(
            f"{SegmentHeader.Reference.value}*{ReferenceIdentificationQualifier.EmployerIdentificationNumber.value}*{provider['employerId']}~"
        )
        
        # Contact Info  
        if "contactInfo" in provider: 
            contactInfo = provider["contactInfo"] 
            name = contactInfo.get("name", "")
            phone_number = contactInfo.get("phoneNumber", "")
            segments.append(
                f"{SegmentHeader.ContactInformation.value}*IC*{name}*TE*{phone_number}~"
            )
        return segments

    def _create_subscriber_loop(self, subscriber_index: int) -> List[str]:
        """Create segments for a subscriber loop."""
        subscriber = self.subscribers[subscriber_index]
        subscriber_count = len (self.subscribers) - 1
        is_dependent = subscriber["is_dependent"]
    
        relationship = ''
        # Subscriber Name using the new method
        name_segment = self._create_name_segment(
            entity_data=subscriber,
            context='subscriber'
        )
        segments = []

        if is_dependent:
            hardcoded_subscriber_hl = f"HL*3*2*23*0~"
            segments.append(hardcoded_subscriber_hl)
            responsibility_code =  PaymentResponsibilityLevelCode(subscriber['paymentResponsibilityLevelCode'])
            # Patient Name
            if responsibility_code == PaymentResponsibilityLevelCode.Primary:
                segments.append(f"PAT*01~")
                segments.append(f"NM1*QC*1*{subscriber["lastName"]}*{subscriber["firstName"]}~")
            
            segments.append(
                f"{SegmentHeader.AddressLine1.value}*{subscriber['address']['address1']}~"
            )
            segments.append(
                f"{SegmentHeader.CityStatePostalCode.value}*{subscriber['address']['city']}*{subscriber['address']['state']}*{subscriber['address']['postalCode']}~"
            )
            # Demographics
            segments.append(f"DMG*D8*{subscriber['birthDate']}*{subscriber['gender']}~")
        else:           
            hardcoded_subscriber_hl = f"HL*2*1*22*{subscriber_count}~"
            segments.append(hardcoded_subscriber_hl)
            relationship = '' if subscriber_count > 0 else RelationshipToSubscriber.Self.value
            
            # Add the subscriber header segment
            segments.append(
                f"{SegmentHeader.SubscriberInformation.value}*{subscriber['paymentResponsibilityLevelCode']}*{relationship}*******{subscriber['claimFilingCode']}~"
            )
            # Subscriber Name
            segments.append(name_segment)
            if subscriber_count == 0: 
                segments.append(
                        f"{SegmentHeader.AddressLine1.value}*{subscriber['address']['address1']}~"
                    )
                segments.append(
                    f"{SegmentHeader.CityStatePostalCode.value}*{subscriber['address']['city']}*{subscriber['address']['state']}*{subscriber['address']['postalCode']}~"
                )
                # Demographics
                segments.append(f"DMG*D8*{subscriber['birthDate']}*{subscriber['gender']}~")


        return segments
   
    def _create_claim_information_loop(self) -> List[str]:
        """Create segments for claim information."""
        if not hasattr(self, 'claim_information'):
            return []
        
        claim = self.claim_information
        segments = []
        # Harcoding the facility code is B for professional and dental
        facility_code_qualifier = "B"
        # CLM segment
        claim_segment = f"CLM*{claim['patientControlNumber']}*{claim['claimChargeAmount']}***"
        claim_segment += f"{claim['placeOfServiceCode']}>{facility_code_qualifier}>{claim['claimFrequencyCode']}*"
        claim_segment += f"{claim['signatureIndicator']}*{claim['planParticipationCode']}*"
        claim_segment += f"{claim['releaseInfoCode']}*{claim['benefitsAssignment']}~"
        segments.append(claim_segment)
        
        # Add prior authorization if present
        if hasattr(self, 'prior_authorization'):
            segments.append(f"REF*G1*{self.prior_authorization}~")
        
        # Add diagnosis codes if present
        if claim['diagnosisCodes']:
            diag_codes = []
            for diag in claim['diagnosisCodes']:
                diag_codes.append(f"{diag['diagnosisTypeCode']}>{diag['diagnosisCode']}")
            segments.append(f"HI*{'>'.join(diag_codes)}~")
        
        # Add service facility if present
        if hasattr(self, 'service_facility'):
            segments.extend(self._create_service_facility_segments())
            
        return segments
    
    def _create_service_lines(self) -> List[str]:
        """Create segments for service lines."""
        if not self.service_lines:
            return []
        
        segments = []
        
        for i, service in enumerate(self.service_lines):
            # Service line number
            segments.append(f"LX*{i+1}~")
            
            # Service line detail
            sv1_segment = f"SV1*HC>{service['procedureCode']}"
            if service.get('modifierCodes'):
                for mod in service['modifierCodes']:
                    sv1_segment += f":{mod}"
            
            sv1_segment += f"*{service['chargeAmount']}*UN*{service['units']}.0***1~"
            segments.append(sv1_segment)
            
            # Service date
            if service.get('serviceDate'):
                segments.append(f"DTP*472*D8*{service['serviceDate']}~")
            
            # Add rendering provider if present
            if hasattr(self, 'rendering_providers') and service.get('renderingProviderIndex') is not None:
                provider_idx = service['renderingProviderIndex']
                if 0 <= provider_idx < len(self.rendering_providers):
                    provider = self.rendering_providers[provider_idx]
                    name_segment = self._create_name_segment(
                        entity_data=provider,
                        context='rendering_provider'
                    )
                    if name_segment:
                        segments.append(name_segment)
                        segments.append(
                            f"PRV*PE*PXC*{provider['taxonomyCode']}~"
                        )
        
        return segments
    
    def _create_service_facility_segments(self) -> List[str]:
        """Create segments for service facility."""
        segments = []
        if not hasattr(self, 'service_facility'):
            return segments
        facility = self.service_facility
        
        # Service Facility Name - using simplified method
        name_segment = self._create_name_segment(
                entity_data=facility,
                context='service_facility'
            )
        if name_segment: 
            segments = []
            segments.append(name_segment)
            # Address
            if 'address1' in facility['address']:
                addr_line = f"N3*{facility['address']['address1']}"
                if facility['address'].get('address2'):
                    addr_line += f"*{facility['address']['address2']}"
                segments.append(addr_line + "~")

            # City, State, ZIP
            if all(k in facility['address'] for k in ('city', 'state', 'postalCode')):
                segments.append(
                    f"N4*{facility['address']['city']}*{facility['address']['state']}*{facility['address']['postalCode']}~"
                )
            return segments
        else:
            return segments
    
    def _create_name_segment(
        self,
        entity_data: Dict[str, Any],
        context: str
    ) -> str:
        """
        Creates a properly formatted NM1 (name) segment for the EDI 837 file.
        This simplified version determines all necessary details based on context and entity data.
        
        Args:
            entity_data: Dictionary containing entity information. Expected keys vary based on entity type:
                - For persons: 'lastName', 'firstName', 'middleName', 'namePrefix', 'nameSuffix'
                - For organizations: 'organizationName'
                - Common: 'npi', 'memberId', 'payerId', 'taxonomyCode', etc.
            context: String indicating the context of this name segment:
                - 'billing_provider': Billing provider (85)
                - 'rendering_provider': Rendering provider (82)
                - 'subscriber': Subscriber/member (IL)
                - 'patient': Patient (QC)
                - 'payer': Payer/insurance company (PR)
                - 'service_facility': Service facility location (77)
                - 'submitter': Submitter (41)
                - 'receiver': Receiver (40)
        
        Returns:
            A formatted NM1 segment string ending with a segment terminator (~)
        """
        # 1. Determine entity identifier code based on context
        
        entity_identifier_code = self._get_entity_identifier_code(context)
        
        
        # 2. Determine if entity is a person or organization
        entity_type_qualifier = self._determine_entity_type(entity_data, context)
        
        proceed = self._can_create_provider(entity_data, context)
        if proceed: 
            # 3. Determine identification details (code and qualifier)
            id_code, id_qualifier = self._get_identification_details(entity_data, context)
            
            # 4. Build the name segment
            segment = f"{SegmentHeader.Name.value}*{entity_identifier_code}*{entity_type_qualifier}*"
            
            # 5. Add name details based on entity type
            if entity_type_qualifier == "1":  # Person
                segment += (
                    f"{entity_data.get('lastName', '')}*"
                    f"{entity_data.get('firstName', '')}*"
                    f"{entity_data.get('middleName', '')}*"
                    f"{entity_data.get('namePrefix', '')}*"
                    f"{entity_data.get('nameSuffix', '')}*"
                )
            else:  # Non-person entity
                segment += f"{entity_data.get('organizationName', '')}*****"
            
            # 6. Add identification code qualifier and code
            segment += f"{id_qualifier}*{id_code}"
            
            # 7. Add segment terminator
            segment += "~"
            return segment
        else:
            return None

    def _get_entity_identifier_code(self, context: str) -> str:
        """Get the entity identifier code based on context."""
        context_map = {
            'billing_provider': EntityIdentifierCode.BillingProvider.value,
            'subscriber': EntityIdentifierCode.Subscriber.value,
            'patient': EntityIdentifierCode.Patient.value,
            'submitter': EntityIdentifierCode.Submitter.value,
            'receiver': EntityIdentifierCode.Receiver.value,
            'rendering_provider': "82",  # Rendering Provider
            'payer': "PR",               # Payer
            'service_facility': "77",    # Service Facility
        }
        
        return context_map.get(context, EntityIdentifierCode.BillingProvider.value)

    def _determine_entity_type(self, entity_data: Dict[str, Any], context: str) -> str:
        """
        Determine if an entity is a person (1) or non-person entity (2).
        
        Some contexts have a default entity type regardless of the data structure.
        """
        # These contexts are always non-person entities
        if context in ['submitter', 'receiver', 'payer', 'service_facility']:
            return "2"
        
        # These contexts are always person entities
        if context in ['patient']:
            return "1"
        
        # For other contexts, determine based on data structure
        return "2" if "organizationName" in entity_data else "1"

    def _can_create_provider(self, entity_data: Dict[str, Any], context: str) -> bool:
        """ function to check if the provider npi was created before """
        if context not in ["billing_provider", "rendering_provider", "service_facility"]:
            return True
        else: 
            npi = entity_data.get("npi", '')
            if not npi:  
                return False
            if npi in self.provider_map:
                return False
            else: 
                self.provider_map[npi] = entity_data
                return True

    def _get_identification_details(
        self, 
        entity_data: Dict[str, Any],
        context: str,
    ) -> Tuple[str, str]:
        """Get the identification code and qualifier based on context and entity type."""
        # Map contexts to their identification details: (data_key, qualifier)
        context_id_map = {
            'billing_provider': ("npi", ReferenceIdentificationQualifier.NationalProviderIdentifier.value),
            'rendering_provider': ("npi", ReferenceIdentificationQualifier.NationalProviderIdentifier.value),
            'service_facility': ("npi", ReferenceIdentificationQualifier.NationalProviderIdentifier.value),
            'subscriber': ("memberId", ReferenceIdentificationQualifier.MemberId.value),
            'patient': (None, None),  # Patients typically don't need identification
            'payer': ("payerId", "PI"),  # Payer ID
            'submitter': (None, "46"),   # Submitter ID
            'receiver': (None, "46"),    # Receiver ID
        }
        
        # Get the appropriate field name and qualifier for this context
        field_name, qualifier = context_id_map.get(context, (None, None))
        
        # For submitter and receiver, the ID is usually in a different field
        if context in ['submitter', 'receiver']:
            code = entity_data.get('id', '')
            return code, qualifier
        else:
            # Extract the identification code from the entity data if field name is known
            code = entity_data.get(field_name, '') if field_name else ''
            return code, qualifier

    def _create_patient_loop(self, patient_index: int) -> List[str]:
        """Create segments for a patient loop."""
        patient = self.patients[patient_index]
        
        name_segment = self._create_name_segment(
            entity_data=patient,
            context='patient'
        )
        segments = [
            # No hierarchical level here since we're using a fixed structure
            # Patient Name
            name_segment,
            # Patient Address
            f"{SegmentHeader.AddressLine1.value}*{patient['address']['address1']}~",
            f"{SegmentHeader.CityStatePostalCode.value}*{patient['address']['city']}*{patient['address']['state']}*{patient['address']['postalCode']}~",
            # Demographics
            f"DMG*D8*{patient['birthDate']}*{patient['gender']}~"
        ]
        
        return segments
    
    def _create_payer(self) -> str: 
        """Create Payer Segment"""
        payer_name = self.payer_info.get("organizationName", "")
        payer_id = self.payer_info.get("payerId","")
        payer_segment = f"{SegmentHeader.Name.value}*{SegmentHeader.Payer.value}*2*{payer_name}*****PI*{payer_id}~"
        
        return payer_segment

    def _create_rendering_provider_segments(self) -> List[str]:
        segments = []
        for rp in self.rendering_providers: 
            name_segment = self._create_name_segment(
                entity_data=rp,
                context='rendering_provider'
            )
            if name_segment: 
                segments.append(name_segment)
                # Creating Rendering Provider Specialty Information
                segments.append(f"PRV*PE*PXC*{rp.get("taxonomyCode")}~")
        
        return segments
    
    def _create_trailer(self, segment_count: int) -> List[str]:
        """Return the hardcoded trailer segments of the EDI file."""
        # Using hardcoded trailer as specified
        se_segment = f"SE*{segment_count}*415133923~"
        return [
            se_segment,
            "GE*1*415133923~",
            "IEA*1*415133923~"
        ]
    
    def build(self) -> str:
        """
        Build the complete EDI 837 file with enhanced claim information.
        
        Returns:
            str: The complete EDI 837 file as a string
        """
        segments = self._create_header()
        
        # Process billing providers and their related subscribers
        for provider_idx, _ in enumerate(self.billing_providers):
            provider_segments = self._create_billing_provider_loop(provider_idx)
            segments.extend(provider_segments)
            
            # Add subscribers related to this billing provider
            for sub_idx, subscriber in enumerate(self.subscribers):
                if subscriber["billingProviderIndex"] == provider_idx:
                    segments.extend(self._create_subscriber_loop(sub_idx))
                    if self.payer_info and sub_idx == 0:
                        segments.append(self._create_payer())
            
            # Add claim information and service facility 
            segments.extend(self._create_claim_information_loop())

            # Add sercices lines
            segments.extend(self._create_service_lines()) 
            # Add rendering provider
            if len(self.rendering_providers) > 0: 
                # Creating rendering providers            
                segments.extend(self._create_rendering_provider_segments())  
            
        # Add trailer segments with hardcoded values
        segments.extend(self._create_trailer(len(segments) -1 ))
        segments = "\n".join(segments)
        
        return segments
    
    def to_file(self, filename: str) -> None:
        """
        Write the EDI 837 file to disk.
        
        Args:
            filename: Path to the output file
        """
        with open(filename, 'w') as f:
            f.write(self.build())

