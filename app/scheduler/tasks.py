from app import create_app, db
from app.models import ScheduledJob
from datetime import datetime

def pipeline_task(job_id):
    """
    The actual task that the scheduler will run in the background.
    It creates its own app context to access the database.
    """
    app = create_app()
    with app.app_context():
        job = ScheduledJob.query.get(job_id)
        if job and job.is_enabled:
            print(f"--- Running scheduled pipeline: {job.pipeline.name} ---")
            
            # TODO: Add the full pipeline execution logic here.
            # This would involve calling a function similar to run_pipeline()
            # from your pipelines/routes.py file. For now, it's a placeholder.
            
            job.last_run = datetime.utcnow()
            db.session.add(job)
            db.session.commit()
            
            print(f"--- Finished scheduled pipeline: {job.pipeline.name} ---")
