---
phase: quick-025
plan: 025
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - pytest.ini
  - upstream/tests/test_property_based.py
autonomous: true

must_haves:
  truths:
    - "Hypothesis library is installed and configured"
    - "Example property-based tests validate data constraints"
    - "API input fuzzing tests catch edge cases"
    - "Tests run as part of pytest suite"
  artifacts:
    - path: "requirements.txt"
      provides: "Hypothesis dependency"
      contains: "hypothesis"
    - path: "pytest.ini"
      provides: "Hypothesis configuration"
      contains: "hypothesis"
    - path: "upstream/tests/test_property_based.py"
      provides: "Property-based test examples"
      min_lines: 100
  key_links:
    - from: "upstream/tests/test_property_based.py"
      to: "hypothesis.strategies"
      via: "import statement"
      pattern: "from hypothesis import.*strategies"
    - from: "upstream/tests/test_property_based.py"
      to: "upstream.models"
      via: "model validation tests"
      pattern: "from upstream\\..*models import"
---

<objective>
Add property-based testing with Hypothesis library to improve test coverage and catch edge cases through automated fuzzing.

Purpose: Hypothesis generates hundreds of test cases automatically, discovering edge cases that manual tests miss - particularly valuable for data validation, API input handling, and model constraints
Output: Configured Hypothesis library with example property-based tests for data validation, API input fuzzing, and model constraint verification
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@upstream/core/models.py
@upstream/api/serializers.py
@upstream/tests/test_middleware.py
@pytest.ini
@requirements.txt
</context>

<tasks>

<task type="auto">
  <name>Task 1: Install and configure Hypothesis</name>
  <files>
    requirements.txt
    pytest.ini
  </files>
  <action>
    Add Hypothesis to requirements.txt:
    - Add line: `hypothesis~=6.92.0` in Testing & Code Coverage section (after factory-boy)
    - Use compatible version constraint (~=) matching project standards

    Configure Hypothesis in pytest.ini:
    - Add `[hypothesis]` section after coverage:report section
    - Set `max_examples = 100` (balance between thoroughness and CI time)
    - Set `derandomize = true` (reproducible test runs)
    - Set `deadline = None` (disable timeout for slow property tests)
    - Add `database = .hypothesis/` (cache for example database)

    Install the package:
    - Run `pip install hypothesis~=6.92.0` to install in current venv
    - Verify installation: `python -c "import hypothesis; print(hypothesis.__version__)"`
  </action>
  <verify>
    - `grep "hypothesis~=6.92.0" requirements.txt` finds the dependency
    - `grep -A4 "\[hypothesis\]" pytest.ini` shows configuration section
    - `python -c "import hypothesis; print(hypothesis.__version__)"` outputs version number without error
  </verify>
  <done>
    Hypothesis 6.92.0 is listed in requirements.txt, configured in pytest.ini with max_examples=100/derandomize=true/deadline=None, and successfully imports in Python
  </done>
</task>

<task type="auto">
  <name>Task 2: Create property-based tests for model validation</name>
  <files>
    upstream/tests/test_property_based.py
  </files>
  <action>
    Create upstream/tests/test_property_based.py with comprehensive property-based tests:

    **Imports section:**
    - Import hypothesis (strategies as st, given decorator, assume, example)
    - Import Django test utilities (TestCase, override_settings)
    - Import models (Customer, Settings, ClaimRecord from upstream.models)
    - Import validation (ValidationError from django.core.exceptions)
    - Import decimal (Decimal) for money amounts

    **Test class 1: CustomerPropertyTests**
    Tests for Customer model validation using property-based testing.

    test_customer_name_validation_with_fuzzing:
    - Use @given(st.text(min_size=1, max_size=200)) for customer names
    - Test that Customer.objects.create(name=fuzzed_name) handles all string inputs
    - Should succeed for valid names (alphanumeric, spaces, common chars)
    - Should raise ValidationError for empty strings or exceed max_length
    - Use hypothesis.assume() to filter invalid test cases

    test_customer_status_constraints:
    - Use @given(st.sampled_from(['active', 'inactive', 'suspended', 'invalid_status']))
    - Test that only valid status values are accepted
    - Invalid values should raise ValidationError or IntegrityError

    **Test class 2: ClaimRecordPropertyTests**
    Tests for ClaimRecord data validation.

    test_claim_amount_validation:
    - Use @given(st.decimals(min_value=0, max_value=999999.99, places=2)) for amounts
    - Test that claim amounts handle all valid decimal values
    - Use @example() decorator for known edge cases (0.00, 0.01, 999999.99)
    - Negative amounts should fail validation

    test_claim_date_constraints:
    - Use @given(st.dates(min_value=date(2000,1,1), max_value=date(2050,12,31)))
    - Test that claim dates are within reasonable business range
    - Future dates beyond 1 year should fail validation (if constraint exists)

    test_claim_id_formats:
    - Use @given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=5, max_size=50))
    - Test that claim IDs handle various alphanumeric formats
    - Should reject IDs with special characters or too short/long

    **Test class 3: APISerializerPropertyTests**
    Tests for API serializer input validation via fuzzing.

    test_serializer_handles_malformed_json_safely:
    - Use @given(st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.floats(), st.none())))
    - Test that serializers validate and reject malformed input gracefully
    - Should return validation errors, never raise unhandled exceptions
    - Test with CustomerSerializer, UploadSerializer (import from api.serializers)

    test_pagination_parameters_fuzzing:
    - Use @given(st.integers(min_value=-100, max_value=10000)) for page/page_size
    - Test that pagination handles invalid integers (negative, zero, huge values)
    - Should clamp to valid ranges or return appropriate errors

    **Test class 4: ConstraintPropertyTests**
    Tests for database constraints using property-based testing.

    test_unique_constraint_enforcement:
    - Use @given(st.text(min_size=1, max_size=100)) for unique fields
    - Create object with value, attempt to create duplicate
    - Second create should raise IntegrityError with UNIQUE constraint message

    test_foreign_key_cascade_behavior:
    - Use @given(st.sampled_from(['CASCADE', 'SET_NULL', 'PROTECT']))
    - Test that foreign key deletions respect on_delete behavior
    - Create related objects, delete parent, verify child state

    **Documentation:**
    Add module docstring explaining:
    - Property-based testing discovers edge cases through automated fuzzing
    - Hypothesis generates hundreds of test inputs to validate invariants
    - Tests cover model validation, API serializers, and database constraints
    - Use @example() decorators for known critical edge cases
    - Run with: pytest upstream/tests/test_property_based.py -v

    **Important implementation notes:**
    - Use pytest-django @pytest.mark.django_db decorator for database tests
    - Clean up created objects in tearDown or use transactions
    - Use hypothesis.assume() to filter invalid strategy outputs (don't let them raise)
    - Add @example() decorators for known edge cases (0, -1, empty, None)
    - Keep strategies reasonable - don't test with unicode emoji unless relevant
  </action>
  <verify>
    - `grep "from hypothesis import" upstream/tests/test_property_based.py` shows hypothesis imports
    - `grep "@given" upstream/tests/test_property_based.py | wc -l` shows at least 8 property-based tests
    - `grep "class.*PropertyTests" upstream/tests/test_property_based.py | wc -l` shows 4 test classes
    - `pytest upstream/tests/test_property_based.py -v --hypothesis-show-statistics` runs successfully with statistics output
  </verify>
  <done>
    File test_property_based.py exists with 4 test classes (CustomerPropertyTests, ClaimRecordPropertyTests, APISerializerPropertyTests, ConstraintPropertyTests), 8+ @given decorated tests covering model validation/API fuzzing/constraints, and pytest runs successfully with Hypothesis statistics
  </done>
</task>

<task type="auto">
  <name>Task 3: Run tests and validate Hypothesis integration</name>
  <files>
    N/A (verification only)
  </files>
  <action>
    Run property-based tests with Hypothesis and validate integration:

    Execute tests with statistics:
    - Run `pytest upstream/tests/test_property_based.py -v --hypothesis-show-statistics`
    - Verify all tests pass (or expected failures for constraint violations)
    - Check Hypothesis statistics show 100 examples generated per test
    - Verify total runtime is reasonable (< 60 seconds for CI compatibility)

    Run full test suite to ensure no regression:
    - Run `pytest upstream/tests/ -k "not performance" --tb=short`
    - Verify existing tests still pass
    - Confirm no import errors or configuration conflicts

    Check Hypothesis database creation:
    - Verify `.hypothesis/` directory is created (example database cache)
    - Add `.hypothesis/` to .gitignore if not already present

    Validate test discovery:
    - Run `pytest --collect-only upstream/tests/test_property_based.py`
    - Confirm pytest discovers all property-based test methods
    - Verify test names are descriptive and follow naming convention

    Check coverage impact:
    - Run `pytest upstream/tests/test_property_based.py --cov=upstream --cov-report=term`
    - Property-based tests should increase coverage for validation code paths
    - Edge case handling should show improved branch coverage
  </action>
  <verify>
    - `pytest upstream/tests/test_property_based.py -v --hypothesis-show-statistics` exits 0 with "100 examples" in output
    - `ls -la .hypothesis/` shows example database directory exists
    - `pytest --collect-only upstream/tests/test_property_based.py | grep "test_" | wc -l` shows 8+ collected tests
    - Test output includes "Hypothesis Statistics" section showing example generation
  </verify>
  <done>
    Property-based tests run successfully with 100 examples per test, Hypothesis statistics displayed, .hypothesis/ cache directory created, all tests discovered by pytest, and no regression in existing test suite
  </done>
</task>

</tasks>

<verification>
Final verification checklist:
- [ ] Hypothesis 6.92.0 installed and configured in pytest.ini
- [ ] test_property_based.py exists with 4 test classes and 8+ property tests
- [ ] Tests cover model validation, API fuzzing, and database constraints
- [ ] `pytest upstream/tests/test_property_based.py -v` runs successfully
- [ ] Hypothesis generates 100 examples per test (shown in statistics)
- [ ] .hypothesis/ cache directory created and ignored by git
- [ ] No regression in existing test suite
- [ ] Property-based tests increase edge case coverage
</verification>

<success_criteria>
Property-based testing with Hypothesis is complete when:
1. Hypothesis library installed with version constraint in requirements.txt
2. pytest.ini configured with max_examples=100, derandomize=true, deadline=None
3. test_property_based.py exists with 4 test classes covering models/API/constraints
4. At least 8 @given decorated tests using hypothesis strategies
5. All property-based tests pass with 100 generated examples each
6. Hypothesis statistics displayed in test output showing example generation
7. .hypothesis/ cache directory created for reproducible test runs
8. Existing test suite runs without regression
</success_criteria>

<output>
After completion, create `.planning/quick/025-add-property-based-testing-with-hypo/025-SUMMARY.md`
</output>
