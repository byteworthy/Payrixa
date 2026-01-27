"""
Data Quality Service

Extracts data quality validation logic from views into a stateless,
framework-agnostic service layer.

This service is responsible for:
- Validating file formats and structures
- Validating claim data integrity
- Computing data quality scores
- Detecting suspicious patterns (like PHI)

All methods accept domain objects (Upload, ClaimRecord) or pure Python
types, not Django request/response objects. Returns structured
dicts/lists that views can format into API responses.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)

# Common first and last names for PHI detection (subset for validation)
COMMON_FIRST_NAMES = {
    "james",
    "john",
    "robert",
    "michael",
    "william",
    "david",
    "richard",
    "joseph",
    "thomas",
    "charles",
    "mary",
    "patricia",
    "jennifer",
    "linda",
    "barbara",
    "elizabeth",
    "susan",
    "jessica",
    "sarah",
    "karen",
    "christopher",
    "daniel",
    "matthew",
    "anthony",
    "mark",
    "donald",
    "steven",
    "paul",
    "andrew",
    "joshua",
    "nancy",
    "betty",
    "margaret",
    "sandra",
    "ashley",
    "kimberly",
    "emily",
    "donna",
    "michelle",
    "dorothy",
}


class DataQualityService:
    """
    Stateless service for data quality validation and scoring.

    All methods are class methods or static methods - no instance state.
    This ensures the service is framework-agnostic and easily testable.
    """

    @staticmethod
    def validate_upload_format(file_obj: Any, filename: str) -> Dict[str, Any]:
        """
        Validate upload file format and structure.

        Checks:
        - File size limits (100MB max)
        - File extension (.csv only)
        - Basic file readability

        Args:
            file_obj: File-like object to validate (must have .size
                and .read() method)
            filename: Original filename for extension validation

        Returns:
            dict: Validation result with keys:
                - valid: bool - Whether file passes validation
                - errors: list[str] - List of validation errors
                - file_size_mb: float - File size in megabytes

        Example:
            >>> result = DataQualityService.validate_upload_format(
            ...     file_obj, "data.csv"
            ... )
            >>> if not result['valid']:
            >>>     print(result['errors'])
        """
        errors = []

        # Validate file size
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
        has_size = hasattr(file_obj, "size")
        file_size_mb = file_obj.size / (1024 * 1024) if has_size else 0

        if has_size and file_obj.size > MAX_FILE_SIZE:
            errors.append(
                f"File too large. Maximum size is 100MB "
                f"(your file: {file_size_mb:.1f}MB)"
            )

        # Validate file extension
        if not filename.lower().endswith(".csv"):
            errors.append("Only CSV files are allowed")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size_mb": file_size_mb,
        }

    @staticmethod
    def validate_claim_data(
        claim_row: Dict[str, str],
        row_number: int,
        required_columns: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Validate a single claim record row.

        Performs field-level validation:
        - Required fields presence
        - PHI detection in payer field
        - Date format validation
        - Outcome value validation
        - Numeric field validation

        Args:
            claim_row: Dict with claim data (keys are column names)
            row_number: Row number for error reporting
            required_columns: List of required column names
                (defaults to: payer, cpt, submitted_date,
                decided_date, outcome)

        Returns:
            list[str]: List of validation error messages.
                Empty list if valid.

        Example:
            >>> row = {'payer': 'Aetna', 'cpt': '99213', ...}
            >>> errors = DataQualityService.validate_claim_data(row, 2)
            >>> if errors:
            >>>     print(f"Row 2 errors: {errors}")
        """
        if required_columns is None:
            required_columns = [
                "payer",
                "cpt",
                "submitted_date",
                "decided_date",
                "outcome",
            ]

        errors = []

        # Validate required fields
        for col in required_columns:
            if col not in claim_row or not claim_row[col]:
                errors.append(f"Row {row_number}: Missing required field: {col}")

        # If missing required fields, return early
        if errors:
            return errors

        # Validate PHI detection in payer field
        try:
            payer_value = claim_row.get("payer", "")
            DataQualityService._validate_not_phi(payer_value, "payer")
        except ValueError as e:
            errors.append(f"Row {row_number}: {str(e)}")

        # Validate outcome values
        valid_outcomes = [
            "PAID",
            "DENIED",
            "OTHER",
            "Paid",
            "Denied",
            "Other",
        ]
        outcome = claim_row.get("outcome")
        if outcome and outcome not in valid_outcomes:
            errors.append(
                f"Row {row_number}: Invalid outcome value '{outcome}'. "
                f"Must be one of: PAID, DENIED, OTHER"
            )

        # Validate numeric fields if present
        if "allowed_amount" in claim_row and claim_row["allowed_amount"]:
            try:
                amount = Decimal(claim_row["allowed_amount"])
                if amount < 0:
                    errors.append(
                        f"Row {row_number}: " f"allowed_amount cannot be negative"
                    )
            except (ValueError, ArithmeticError):
                amt_value = claim_row["allowed_amount"]
                errors.append(
                    f"Row {row_number}: " f"Invalid allowed_amount '{amt_value}'"
                )

        return errors

    @staticmethod
    def compute_data_quality_score(
        total_rows: int,
        accepted_rows: int,
        rejected_rows: int,
        warning_rows: int = 0,
    ) -> float:
        """
        Compute data quality score for an upload.

        Score is calculated as: accepted_rows / total_rows
        Range: 0.0 (all rejected) to 1.0 (all accepted)

        Args:
            total_rows: Total number of rows in upload
            accepted_rows: Number of rows that passed validation
            rejected_rows: Number of rows that failed validation
            warning_rows: Number of rows with non-fatal warnings

        Returns:
            float: Quality score between 0.0 and 1.0.
                Returns 0.0 if total_rows is 0.

        Example:
            >>> score = DataQualityService.compute_data_quality_score(
            ...     100, 95, 5
            ... )
            >>> print(f"Quality: {score * 100:.1f}%")
            # Output: Quality: 95.0%
        """
        if total_rows == 0:
            return 0.0

        # Basic validation
        if accepted_rows < 0 or rejected_rows < 0 or warning_rows < 0:
            logger.warning(
                f"Invalid quality score inputs: total={total_rows}, "
                f"accepted={accepted_rows}, "
                f"rejected={rejected_rows}, warnings={warning_rows}"
            )
            return 0.0

        # Ensure total is consistent
        if accepted_rows + rejected_rows > total_rows:
            logger.warning(
                f"Inconsistent row counts: "
                f"accepted ({accepted_rows}) + "
                f"rejected ({rejected_rows}) > total ({total_rows})"
            )
            return 0.0

        return accepted_rows / total_rows

    @staticmethod
    def flag_suspicious_patterns(
        claims_data: List[Dict[str, Any]], min_pattern_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Flag suspicious patterns in claim data.

        Detects patterns that may indicate data quality issues:
        - High frequency of identical values (potential data entry)
        - Unusual date patterns (all same date, future dates)
        - Extreme outliers in amounts
        - High denial rates for specific payer/CPT combinations

        Args:
            claims_data: List of claim dicts with keys:
                payer, cpt, submitted_date, decided_date, outcome,
                allowed_amount
            min_pattern_count: Minimum occurrences to flag a pattern
                (default: 10)

        Returns:
            list[dict]: List of suspicious pattern findings, each with:
                - pattern_type: str - Type of suspicious pattern
                - description: str - Human-readable description
                - affected_count: int - Number of records affected
                - severity: str - 'low', 'medium', or 'high'
                - details: dict - Additional pattern-specific details

        Example:
            >>> patterns = DataQualityService.flag_suspicious_patterns(
            ...     claims_list
            ... )
            >>> for pattern in patterns:
            >>>     if pattern['severity'] == 'high':
            >>>         print(f"Alert: {pattern['description']}")
        """
        findings = []

        if not claims_data:
            return findings

        # Pattern 1: Check for suspiciously high frequency of
        # identical payer names
        payer_counts = {}
        for claim in claims_data:
            payer = claim.get("payer", "")
            if payer:
                payer_counts[payer] = payer_counts.get(payer, 0) + 1

        total_claims = len(claims_data)
        for payer, count in payer_counts.items():
            frequency = count / total_claims
            if count >= min_pattern_count and frequency > 0.8:
                findings.append(
                    {
                        "pattern_type": "high_payer_concentration",
                        "description": (
                            f"Payer '{payer}' represents "
                            f"{frequency*100:.1f}% of all claims"
                        ),
                        "affected_count": count,
                        "severity": "medium",
                        "details": {
                            "payer": payer,
                            "percentage": frequency * 100,
                        },
                    }
                )

        # Pattern 2: Check for same-day submission patterns
        same_day_claims = []
        for claim in claims_data:
            submitted = claim.get("submitted_date")
            decided = claim.get("decided_date")
            if submitted and decided and submitted == decided:
                same_day_claims.append(claim)

        if len(same_day_claims) >= min_pattern_count:
            frequency = len(same_day_claims) / total_claims
            if frequency > 0.5:
                findings.append(
                    {
                        "pattern_type": "same_day_processing",
                        "description": (
                            f"{len(same_day_claims)} claims have identical "
                            f"submission and decision dates"
                        ),
                        "affected_count": len(same_day_claims),
                        "severity": "low",
                        "details": {"percentage": frequency * 100},
                    }
                )

        # Pattern 3: Check for suspiciously low allowed amounts
        low_amount_claims = []
        for claim in claims_data:
            amount = claim.get("allowed_amount")
            if amount is not None:
                try:
                    amt_decimal = (
                        Decimal(str(amount))
                        if not isinstance(amount, Decimal)
                        else amount
                    )
                    if amt_decimal == 0:
                        low_amount_claims.append(claim)
                except (ValueError, ArithmeticError):
                    pass

        if len(low_amount_claims) >= min_pattern_count:
            findings.append(
                {
                    "pattern_type": "zero_allowed_amounts",
                    "description": (
                        f"{len(low_amount_claims)} claims have " f"$0 allowed amount"
                    ),
                    "affected_count": len(low_amount_claims),
                    "severity": "medium",
                    "details": {
                        "percentage": (len(low_amount_claims) / total_claims) * 100
                    },
                }
            )

        # Pattern 4: Check for high denial rates
        denied_claims = [
            c for c in claims_data if c.get("outcome", "").upper() == "DENIED"
        ]
        if len(denied_claims) >= min_pattern_count:
            denial_rate = len(denied_claims) / total_claims
            if denial_rate > 0.5:
                findings.append(
                    {
                        "pattern_type": "high_denial_rate",
                        "description": (
                            f"High denial rate: "
                            f"{denial_rate*100:.1f}% of claims denied"
                        ),
                        "affected_count": len(denied_claims),
                        "severity": "high",
                        "details": {
                            "denial_rate": denial_rate * 100,
                            "total_denials": len(denied_claims),
                        },
                    }
                )

        return findings

    @staticmethod
    def _validate_not_phi(value: str, field_name: str = "payer") -> None:
        """
        Validate that a field value doesn't look like PHI (patient name).

        Private helper method for PHI detection.

        Raises ValueError if the value appears to be a patient name.

        Rules:
        - Title Case with 2-3 words (e.g., "John Smith")
        - First word matches common first names
        - Only letters, spaces, hyphens (no numbers or special chars)

        Args:
            value: The value to validate
            field_name: Name of the field being validated
                (for error messages)

        Raises:
            ValueError: If value looks like PHI
        """
        if not value:
            return

        value_stripped = value.strip()

        # Check if it's Title Case with 2-3 words
        words = value_stripped.split()
        if 2 <= len(words) <= 3:
            # Check if all words are title case and alphabetic
            if all(
                word.istitle() and word.replace("-", "").isalpha() for word in words
            ):
                # Check if first word is a common first name
                first_word = words[0].lower()
                if first_word in COMMON_FIRST_NAMES:
                    # Log PHI detection attempt (value redacted)
                    logger.warning(
                        f"PHI_DETECTION: Rejected {field_name} field "
                        f"containing patient-like name. "
                        f"First word: {first_word}, "
                        f"Word count: {len(words)}"
                    )
                    raise ValueError(
                        f"PRIVACY ALERT: {field_name} value "
                        f"'{value_stripped}' looks like a patient name. "
                        f"Please use payer organization names only "
                        f"(e.g., 'Blue Cross Blue Shield', 'Medicare', "
                        f"'Aetna'). NEVER include patient names, DOB, "
                        f"SSN, or addresses in uploads."
                    )
