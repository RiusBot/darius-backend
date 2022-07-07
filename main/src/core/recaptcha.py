import logging

from google.cloud import recaptchaenterprise_v1

from main.src.config import app_config
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


# flake8: noqa: E128
async def create_recaptcha_assessment(token, recaptcha_action):
    """ Create an assessment to analyze the risk of a UI action.
    """
    if recaptcha_action.upper() not in app_config['RECAPTCHA_VALID_ACTIONS']:
        raise BackendException(f'Invalid reCAPTCHA action {recaptcha_action}')
    project_id = app_config['G_CLOUD_PROJECT_ID']
    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

    event = recaptchaenterprise_v1.Event()
    event.site_key = app_config['RECAPTCHA_SITE_KEY']
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    project_name = f'projects/{project_id}'

    request = recaptchaenterprise_v1.CreateAssessmentRequest()
    request.assessment = assessment
    request.parent = project_name

    response = client.create_assessment(request)

    if not response.token_properties.valid:
        logger.warning('Recaptcha createAssessment failed because the token was invalid '
            'for the following reasons: %s', response.token_properties.invalid_reason)
        raise BackendException('Invalid reCAPTCHA token')
    else:
        if response.token_properties.action.upper() == recaptcha_action.upper():
            logger.info('The reCAPTCHA score for this token is: %s, reasons: %s',
                response.risk_analysis.score, response.risk_analysis.reasons)
        else:
            logger.warning(
                'The action: %s in reCAPTCHA tag does not match the action: %s expecting to score',
                response.token_properties.action,
                recaptcha_action
            )
            raise BackendException(f'Mismatch reCAPTCHA action {recaptcha_action}')
