from care.emr.resources.questionnaire.spec import QuestionnaireStatus


class InternalQuestionnaireRegistry:
    _questionnaires = {}

    @classmethod
    def register(cls, view) -> None:
        cls._questionnaires[view.questionnaire_type] = view

    @classmethod
    def serialize(cls, view):
        return {
            "version": 1,
            "title": "",
            "description": "",
            "type": view.questionnaire_type,
            "status": QuestionnaireStatus.active.value,
            "subject_type": view.questionnaire_subject_type,
        }

    @classmethod
    def search_questionnaire(cls, term):
        return [
            cls.serialize(cls._questionnaires[view])
            for view in cls._questionnaires
            if term in view
        ]
