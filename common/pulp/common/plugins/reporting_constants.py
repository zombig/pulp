"""
Contains constants used for generic state processing & reporting for tasks
"""

PROGRESS_STEP_UUID = u'step_id'
PROGRESS_STEP_TYPE_KEY = u'step_type'
PROGRESS_ITEMS_TOTAL_KEY = u'items_total'
PROGRESS_NUM_PROCESSED_KEY = u'num_processed'
PROGRESS_NUM_SUCCESSES_KEY = u'num_success'
PROGRESS_NUM_FAILURES_KEY = u'num_failures'
PROGRESS_DESCRIPTION_KEY = u'description'
PROGRESS_DETAILS_KEY = u'details'
PROGRESS_STATE_KEY = u'state'
PROGRESS_ERROR_DETAILS_KEY = u'error_details'
PROGRESS_SUB_STEPS_KEY = u'sub_steps'

STATE_NOT_STARTED = u'NOT_STARTED'
STATE_RUNNING = u'IN_PROGRESS'
STATE_COMPLETE = u'FINISHED'
STATE_FAILED = u'FAILED'
STATE_SKIPPED = u'SKIPPED'
STATE_CANCELLED = u'CANCELLED'

FINAL_STATES = (STATE_COMPLETE, STATE_FAILED, STATE_SKIPPED)

PUBLISH_STEP_DIRECTORY = u'publish_directory'
PUBLISH_STEP_TAR = u'save_tar'
PUBLISH_STEP_COPY_DIRECTORY = u'copy_directory'

SYNC_STEP_GET_LOCAL = u'get_local'
REFRESH_STEP_CONTENT_SOURCE = u'refresh_content_source'
LAZY_STEP_DOWNLOAD = u'download_lazy_units'

STEP_CREATE_PULP_MANIFEST = u'create_pulp_manifest'
