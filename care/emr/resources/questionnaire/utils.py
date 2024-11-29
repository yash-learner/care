import logging
import uuid
from datetime import datetime

from dateutil import parser
from rest_framework.exceptions import ValidationError

from care.emr.models.questionnaire import Questionnaire, QuestionnaireResponse
from care.emr.resources.observation.spec import ObservationStatus
from care.emr.resources.questionnaire.spec import QuestionType


def validate_types(values, value_type):
    """
    Validate the type of the value based on the question type.
    Args:
        values: List of values to validate
        value_type: Type of the question (from QuestionType enum)
    Returns:
        list: List of validation errors, empty if validation succeeds
    """
    errors = []
    if not values:
        return errors
    for value in values:
        if value.value is None:
            continue
        try:
            if value_type == QuestionType.integer.value:
                int(value.value)
            elif value_type == QuestionType.decimal.value:
                float(value.value)
            elif value_type == QuestionType.boolean.value:
                if value.value.lower() not in ["true", "false", "1", "0"]:
                    errors.append(f"Invalid boolean value: {value.value}")
            elif value_type == QuestionType.date.value:
                parser.parse(value.value).date()
            elif value_type == QuestionType.datetime.value:
                parser.parse(value.value)
            elif value_type == QuestionType.time.value:
                datetime.strptime(value.value, "%H:%M:%S")  # noqa DTZ007
        except ValueError:
            errors.append(f"Invalid {value_type} value: {value.value}")
        except Exception:
            errors.append(f"Error validating {value_type} value: {value.value}")

    return errors


def validate_question_result(questionnaire, responses, errors):
    # Validate question responses
    if questionnaire["type"] == QuestionType.group.value:
        # Iterate and call all child questions
        if questionnaire["questions"]:
            for question in questionnaire["questions"]:
                validate_question_result(question, responses, errors)
    else:
        if questionnaire["id"] not in responses:
            errors.append(
                {"question_id": questionnaire["id"], "error": "Question not answered"}
            )
            return
        value = responses[questionnaire["id"]].value
        value_type = questionnaire["type"]
        values = [value]
        if questionnaire.get("repeats", False):
            values = responses[questionnaire["id"]].values
        type_errors = validate_types(values, value_type)
        if type_errors:
            errors.append({"question_id": questionnaire["id"], "errors": type_errors})


def create_observation_spec(questionnaire, responses, parent_id=None):
    spec = {}
    spec["id"] = uuid.uuid4()
    spec["status"] = ObservationStatus.final.value
    if "category" in questionnaire:
        spec["category"] = questionnaire["category"]
    if "code" in questionnaire:
        spec["main_code"] = questionnaire["code"]
    if (
        responses
        and questionnaire["id"] in responses
        and responses[questionnaire["id"]].value
    ):
        if responses[questionnaire["id"]].value.value:
            spec["value"] = responses[questionnaire["id"]].value.value
        if responses[questionnaire["id"]].value.value_code:
            spec["value_code"] = responses[questionnaire["id"]].value_code
        if responses[questionnaire["id"]].note:
            spec["note"] = responses[questionnaire["id"]].note
    if parent_id:
        spec["parent"] = parent_id
    return spec


def convert_to_observation_spec(
    questionnaire_obj: Questionnaire, responses, parent_id=None
):
    constructed_observation_mapping = []
    for question in questionnaire_obj.get("questions", []):
        if question["type"] == QuestionType.group.value:
            observation = create_observation_spec(question, responses, parent_id)
            sub_mapping = convert_to_observation_spec(
                question, responses, observation["id"]
            )
            if sub_mapping:
                constructed_observation_mapping.append(observation)
                constructed_observation_mapping.extend(sub_mapping)
        elif question["code"]:
            constructed_observation_mapping.append(
                create_observation_spec(question, responses, parent_id)
            )
    return constructed_observation_mapping


def handle_response(questionnaire_obj: Questionnaire, results):
    """
    Generate observations and questionnaire responses after validation
    """
    # Construct questionnaire response
    responses = {}
    errors = []
    for result in results.results:
        responses[str(result.question_id)] = result
    for question in questionnaire_obj.questions:
        validate_question_result(question, responses, errors)
    if errors:
        raise ValidationError(errors)
    # Validate and create observation objects
    observations = convert_to_observation_spec(
        {"questions": questionnaire_obj.questions}, responses
    )
    logging.info(observations)
    # Bulk create observations
    # Create questionnaire response
    json_results = results.model_dump(mode="json", exclude_defaults=True)
    QuestionnaireResponse.objects.create(
        questionnaire=questionnaire_obj,
        subject_id=results.resource_id,
        encounter=results.encounter,
        responses=json_results["results"],
    )
    # Serialize and return questionnaire response
    return json_results
