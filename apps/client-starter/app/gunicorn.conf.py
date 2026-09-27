"""gunicorn settings shared by run.sh and the systemd unit.

post_worker_init starts the workflow runner (a daemon thread) in every
worker once the app is loaded, so scheduled automation emails are sent for
as long as the instance is up: no cron, no extra daemon. Several workers
are safe: each due step is claimed atomically in SQLite before it is sent.
Disable with CLIENT_WORKFLOW_RUNNER=0 (then use cron against
POST /api/process-workflows with the X-Cron-Key header).
"""


def post_worker_init(worker):
    import app as webapp
    webapp.start_workflow_runner()
