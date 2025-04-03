"""
JSON to EDI 837P Converter Script

This script provides a command-line interface for converting healthcare claim data
from JSON format to EDI 837P (Professional) format. It reads JSON input from a file,
validates the data, and generates a compliant EDI 837P file.

Usage:
    python json_to_edi.py <input_json_file> <output_edi_file>

Example:
    python json_to_edi.py ./examples/mojo_dojo_casa_house.json ./generated_edi.837

The script includes comprehensive error handling and will display detailed error
messages and stack traces if any issues occur during the conversion process.
"""

import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Optional, Any, List
from EDIService import (
    EDI837Builder, 
    ClaimFilingIndicatorCode,
    PaymentResponsibilityLevelCode
)

class EDI837Converter:
    """Handles the conversion of JSON data to EDI 837P format."""
    
    def __init__(self):
        """Initialize the converter with a new EDI builder instance."""
        self.builder = EDI837Builder()
    
    def convert(self, json_data: Dict[str, Any]) -> str:
        """
        Convert JSON data to EDI 837P format.
        
        Args:
            json_data: Dictionary containing the JSON data
            
        Returns:
            The EDI content as a string
        """
        # Process submitter information
        self._process_submitter(json_data.get("submitter"))
        
        # Process billing provider and get its index
        provider_idx = self._process_billing_provider(json_data.get("billing"))
        
        # Process subscriber information
        subscriber_idx = self._process_subscriber(json_data, provider_idx)
        
        # Process dependent if present
        if "dependent" in json_data:
            self._process_dependent(json_data["dependent"], json_data, provider_idx)
        
        # Process claim information
        if "claimInformation" in json_data:
            self._process_claim_information(json_data["claimInformation"], subscriber_idx)
        
        # Process rendering provider if present
        if "rendering" in json_data:
            self._process_rendering_provider(json_data["rendering"])
        
        return self.builder.build()
    
    def _process_submitter(self, submitter_data: Optional[Dict[str, Any]]) -> None:
        """Process submitter information."""
        if submitter_data:
            self.builder.add_submitter(
                contactInfo=submitter_data.get("contactInformation")
            )
    
    def _process_billing_provider(self, provider_data: Optional[Dict[str, Any]]) -> int:
        """Process billing provider information."""
        if not provider_data:
            raise ValueError("Billing provider information is required")
            
        return self.builder.add_billing_provider(
            npi=provider_data["npi"],
            taxonomy_code=provider_data["taxonomyCode"],
            employer_id=provider_data["employerId"],
            organization_name=provider_data.get("organizationName", ""),
            address=provider_data["address"],
            contactInfo=provider_data.get("contactInformation")
        )
    
    def _process_subscriber(self, data: Dict[str, Any], provider_idx: int) -> int:
        """Process subscriber information."""
        subscriber_data = data.get("subscriber")
        if not subscriber_data:
            raise ValueError("Subscriber information is required")
            
        payment_code = self._determine_payment_code(subscriber_data)
        claim_filing_code = self._determine_claim_filing_code(data)
        gender = subscriber_data.get("gender", "U")
        
        subscriber_idx = self.builder.add_subscriber(
            member_id=subscriber_data["memberId"],
            last_name=subscriber_data["lastName"],
            first_name=subscriber_data["firstName"],
            address=subscriber_data["address"],
            birth_date=subscriber_data["dateOfBirth"],
            gender=gender,
            billing_provider_index=provider_idx,
            payment_responsibility_code=payment_code,
            claim_filing_code=claim_filing_code,
            is_dependent=False,
            relationship_to_subscriber=subscriber_data.get("relationshipToSubscriberCode", "")
        )
        
        # Process payer if present
        if "receiver" in data and "organizationName" in data["receiver"]:
            self._process_payer(subscriber_idx, data["receiver"])
            
        return subscriber_idx
    
    def _process_dependent(self, dependent_data: Dict[str, Any], data: Dict[str, Any], provider_idx: int) -> None:
        """Process dependent subscriber information."""
        payment_code = self._determine_payment_code(dependent_data)
        claim_filing_code = self._determine_claim_filing_code(data)
        gender = dependent_data.get("gender", "U")
        
        self.builder.add_subscriber(
            member_id=dependent_data["memberId"],
            last_name=dependent_data["lastName"],
            first_name=dependent_data["firstName"],
            address=dependent_data["address"],
            birth_date=dependent_data["dateOfBirth"],
            gender=gender,
            billing_provider_index=provider_idx,
            payment_responsibility_code=payment_code,
            claim_filing_code=claim_filing_code,
            is_dependent=True,
            relationship_to_subscriber=dependent_data.get("relationshipToSubscriberCode", "")
        )
    
    def _process_claim_information(self, claim_data: Dict[str, Any], subscriber_idx: int) -> None:
        """Process claim information and service lines."""
        # Process diagnosis codes
        diagnosis_codes = self._extract_diagnosis_codes(claim_data)
        
        # Add claim information
        self.builder.add_claim_information(
            subscriber_index=subscriber_idx,
            patient_control_number=claim_data["patientControlNumber"],
            claim_charge_amount=float(claim_data["claimChargeAmount"]),
            place_of_service_code=claim_data["placeOfServiceCode"],
            claim_frequency_code=claim_data.get("claimFrequencyCode", "1"),
            signature_indicator=claim_data.get("signatureIndicator", "Y"),
            plan_participation_code=claim_data.get("planParticipationCode", "A"),
            release_info_code=claim_data.get("releaseInformationCode", "Y"),
            benefits_assignment=claim_data.get("benefitsAssignmentCertificationIndicator", "Y"),
            diagnosis_codes=diagnosis_codes
        )
        
        # Process prior authorization
        self._process_prior_authorization(claim_data)
        
        # Process service facility
        self._process_service_facility(claim_data)
        
        # Process service lines
        if "serviceLines" in claim_data:
            self._process_service_lines(claim_data["serviceLines"], subscriber_idx)
    
    def _process_rendering_provider(self, provider_data: Dict[str, Any]) -> None:
        """Process rendering provider information."""
        self.builder.add_rendering_provider(
            npi=provider_data["npi"],
            taxonomy_code=provider_data["taxonomyCode"],
            last_name=provider_data["lastName"],
            first_name=provider_data["firstName"],
            employer_id=provider_data["employerId"]
        )
    
    def _process_payer(self, subscriber_idx: int, receiver_data: Dict[str, Any]) -> None:
        """Process payer information."""
        payer_id = "WIMCD"  # This could be made configurable
        self.builder.add_payer(subscriber_idx, receiver_data["organizationName"], payer_id)
    
    def _process_prior_authorization(self, claim_data: Dict[str, Any]) -> None:
        """Process prior authorization information."""
        if "claimSupplementalInformation" in claim_data:
            supp_info = claim_data["claimSupplementalInformation"]
            if "priorAuthorizationNumber" in supp_info:
                self.builder.add_prior_authorization(supp_info["priorAuthorizationNumber"])
    
    def _process_service_facility(self, claim_data: Dict[str, Any]) -> None:
        """Process service facility location information."""
        if "serviceFacilityLocation" in claim_data:
            facility = claim_data["serviceFacilityLocation"]
            self.builder.add_service_facility_location(
                npi=facility["npi"],
                organization_name=facility["organizationName"],
                address=facility["address"]
            )
    
    def _process_service_lines(self, service_lines: List[Dict[str, Any]], subscriber_idx: int) -> None:
        """Process service lines information."""
        for service_line in service_lines:
            if "professionalService" in service_line:
                service = service_line["professionalService"]
                rendering_provider_idx = None
                
                # Process rendering provider if present
                if "renderingProvider" in service_line:
                    provider = service_line["renderingProvider"]
                    rendering_provider_idx = self.builder.add_rendering_provider(
                        npi=provider["npi"],
                        last_name=provider["lastName"],
                        first_name=provider["firstName"],
                        taxonomy_code=provider["taxonomyCode"],
                        employer_id=provider["employerId"]
                    )
                
                # Add the service line
                self.builder.add_service_line(
                    subscriber_index=subscriber_idx,
                    patient_index=None,
                    procedure_code=service["procedureCode"],
                    modifier_codes=[],
                    charge_amount=float(service["lineItemChargeAmount"]),
                    units=int(service["serviceUnitCount"]),
                    service_date=service_line["serviceDate"],
                    rendering_provider_index=rendering_provider_idx
                )
    
    def _determine_payment_code(self, subscriber_data: Dict[str, Any]) -> PaymentResponsibilityLevelCode:
        """Determine payment responsibility code from subscriber data."""
        code_map = {
            "P": PaymentResponsibilityLevelCode.Primary,
            "S": PaymentResponsibilityLevelCode.Secondary,
            "T": PaymentResponsibilityLevelCode.Tertiary
        }
        return code_map.get(subscriber_data.get("paymentResponsibilityLevelCode"), 
                          PaymentResponsibilityLevelCode.Primary)
    
    def _determine_claim_filing_code(self, data: Dict[str, Any]) -> ClaimFilingIndicatorCode:
        """Determine claim filing code from claim information."""
        if "claimInformation" in data and "claimFilingCode" in data["claimInformation"]:
            return ClaimFilingIndicatorCode(data["claimInformation"]["claimFilingCode"].upper())
        return ClaimFilingIndicatorCode.Unknown
    
    def _extract_diagnosis_codes(self, claim_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract diagnosis codes from claim data."""
        diagnosis_codes = []
        if "healthCareCodeInformation" in claim_data:
            for code_info in claim_data["healthCareCodeInformation"]:
                diagnosis_codes.append({
                    "diagnosisTypeCode": code_info["diagnosisTypeCode"],
                    "diagnosisCode": code_info["diagnosisCode"]
                })
        return diagnosis_codes

def convert_json_to_edi(json_file_path: str, output_file_path: Optional[str] = None) -> str:
    """
    Convert a JSON file to EDI 837 format.
    
    Args:
        json_file_path: Path to the JSON file
        output_file_path: Optional path to write the EDI output
        
    Returns:
        The EDI content as a string
    """
    # Load JSON data
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Convert using the converter class
    converter = EDI837Converter()
    edi_content = converter.convert(data)
    
    # Write to file if specified
    if output_file_path:
        with open(output_file_path, 'w') as file:
            file.write(edi_content)
    
    return edi_content

def main():
    """Main function to handle the JSON to EDI conversion process.
    
    This function:
    1. Validates command line arguments
    2. Reads and parses the input JSON file
    3. Converts the data to EDI 837P format
    4. Writes the EDI content to the output file
    
    The function includes comprehensive error handling and will display
    detailed error messages and stack traces if any issues occur.
    """
    if len(sys.argv) != 3:
        print("Usage: python json_to_edi.py <input_json_file> <output_edi_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        edi_content = convert_json_to_edi(input_file, output_file)
        print(f"EDI file generated successfully: {output_file}")
        
        # Optionally print the EDI content
        print("\nGenerated EDI content:")
        print(edi_content)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()