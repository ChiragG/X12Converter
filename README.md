# X12Converter

A Python-based tool that converts healthcare claim data from JSON format to EDI 837P (Professional) format. This converter is designed to handle healthcare provider claims data and generate compliant EDI 837P files that follow industry standards.

## Features

- Converts healthcare claim data from JSON to EDI 837P format
- Handles billing provider information
- Processes subscriber and patient details
- Supports claim information and service lines
- Includes rendering provider details
- Handles service facility locations
- Supports prior authorization information
- Processes payer information
- Supports multiple procedures in a single claim
- Handles subscriber and dependent information
- Comprehensive error handling and validation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/X12Converter.git
   cd X12Converter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
.
├── EDIService.py         # Core EDI conversion service
├── json_to_edi.py       # Main script to convert JSON to EDI
├── examples/
│   ├── mojo_dojo_casa_house.json     # Example JSON input file
│   ├── mojo_dojo_casa_house.837      # Corresponding EDI file
│   ├── multi_procedure_barbie.json   # Example with multiple procedures
│   ├── multi_procedure_barbie.837    # Corresponding EDI file
│   ├── subscriber_with_a_dekendent.json  # Example with subscriber and dependent
│   └── subscriber_with_a_dekendent.837   # Corresponding EDI file
├── output/              # Directory for generated EDI files
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Usage

### Single File Conversion

1. Prepare your JSON input file following the structure in the example files
2. Run the conversion script:
   ```bash
   python json_to_edi.py <input_json_file> <output_edi_file>
   ```
   Example:
   ```bash
   python json_to_edi.py ./examples/mojo_dojo_casa_house.json ./output/mojo_dojo_casa_house.837
   ```

   Note: It's recommended to save all generated EDI files in the `output/` directory to keep the project organized.

## EDI 837P Output Format

The script generates an EDI 837P file following the standard format with these segments:

### Header Segments
- ISA (Interchange Control Header)
  - Sender and receiver identification
  - Date and time stamps
  - Control numbers
- GS (Functional Group Header)
  - Functional identifier code
  - Application sender/receiver codes
  - Date and time stamps
- ST (Transaction Set Header)
  - Transaction set identifier code
  - Control number

### Claim Information
- Billing Provider Information (NM1*85)
  - Provider name and NPI
  - Tax ID
  - Address information
- Subscriber Information (NM1*IL)
  - Subscriber name and ID
  - Group information
  - Address details
- Patient Information (NM1*QC)
  - Patient name and ID
  - Birth date and gender
  - Address information
- Claim Information (CLM)
  - Claim number
  - Total charges
  - Place of service
- Service Lines (SV1)
  - Procedure codes
  - Service dates
  - Charges and units
  - Place of service

### Trailer Segments
- SE (Transaction Set Trailer)
  - Segment count
  - Control number
- GE (Functional Group Trailer)
  - Number of transaction sets
  - Group control number
- IEA (Interchange Control Trailer)
  - Number of functional groups
  - Interchange control number

## Example Files

The project includes several example files demonstrating different use cases:
- `mojo_dojo_casa_house`: Basic claim example with a single procedure
- `multi_procedure_barbie`: Example with multiple procedures in a single claim
- `subscriber_with_a_dekendent`: Example with subscriber and dependent information

Each JSON example has a corresponding EDI 837 file for comparison. These examples cover common scenarios in healthcare claims processing.

## Dependencies

- Python 3.x
- pydantic >= 2.0.0 (for data validation)
- python-dateutil >= 2.8.2 (for date handling)

## Error Handling

The script includes comprehensive error handling and validation:

### Common Error Cases
- Invalid JSON format
- Missing required fields
- Invalid data types
- File system errors
- EDI segment validation errors

### Error Reporting
- Detailed error messages
- Stack traces for debugging
- Validation reports for data integrity

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This README and the `run_examples.py` script were created using [Cursor](https://cursor.sh), an AI-powered code editor.

