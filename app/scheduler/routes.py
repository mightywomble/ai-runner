from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required
from . import bp
from app import db
from app import bg_scheduler as scheduler # Use the renamed scheduler object
from app.models import ScheduledJob, Pipeline
from croniter import croniter
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
from app.scheduler.tasks import pipeline_task # Import the task function

@bp.route('/')
@login_required
def schedule_list():
    """Displays the list of all scheduled jobs."""
    jobs = ScheduledJob.query.order_by(ScheduledJob.name).all()
    # Update next_run time for display
    for job in jobs:
        if job.is_enabled and croniter.is_valid(job.cron_string):
            try:
                job.next_run = croniter(job.cron_string, datetime.now()).get_next(datetime)
            except:
                job.next_run = None # Handle potential croniter errors
    
    pipelines = Pipeline.query.order_by(Pipeline.name).all()
    return render_template('scheduler/scheduler.html', title="Pipeline Scheduler", jobs=jobs, pipelines=pipelines)

@bp.route('/add', methods=['POST'])
@login_required
def add_schedule():
    """Adds a new scheduled job."""
    name = request.form.get('name')
    pipeline_id = request.form.get('pipeline_id')
    cron_string = request.form.get('cron_string')

    if not all([name, pipeline_id, cron_string]):
        flash('All fields are required.', 'error')
        return redirect(url_for('scheduler.schedule_list'))

    if not croniter.is_valid(cron_string):
        flash('Invalid CRON string format.', 'error')
        return redirect(url_for('scheduler.schedule_list'))

    try:
        new_job = ScheduledJob(name=name, pipeline_id=pipeline_id, cron_string=cron_string, is_enabled=True)
        db.session.add(new_job)
        db.session.commit()
        
        trigger = CronTrigger.from_crontab(cron_string)
        scheduler.add_job(
            id=str(new_job.id),
            func='app.scheduler.tasks:pipeline_task',
            args=[new_job.id],
            trigger=trigger,
            replace_existing=True
        )
        flash(f'Scheduled job "{name}" added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding scheduled job: {e}', 'error')
        
    return redirect(url_for('scheduler.schedule_list'))

@bp.route('/<int:job_id>/edit', methods=['POST'])
@login_required
def edit_schedule(job_id):
    """Edits an existing scheduled job."""
    job = ScheduledJob.query.get_or_404(job_id)
    name = request.form.get('name')
    pipeline_id = request.form.get('pipeline_id')
    cron_string = request.form.get('cron_string')

    if not all([name, pipeline_id, cron_string]):
        flash('All fields are required.', 'error')
        return redirect(url_for('scheduler.schedule_list'))

    if not croniter.is_valid(cron_string):
        flash('Invalid CRON string format.', 'error')
        return redirect(url_for('scheduler.schedule_list'))
        
    try:
        job.name = name
        job.pipeline_id = pipeline_id
        job.cron_string = cron_string
        
        trigger = CronTrigger.from_crontab(cron_string)
        scheduler.modify_job(id=str(job.id), trigger=trigger)
        
        db.session.commit()
        flash(f'Scheduled job "{job.name}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating scheduled job: {e}', 'error')

    return redirect(url_for('scheduler.schedule_list'))


@bp.route('/<int:job_id>/run_now', methods=['POST'])
@login_required
def run_now(job_id):
    """Triggers a scheduled job to run immediately."""
    job = ScheduledJob.query.get_or_404(job_id)
    try:
        scheduler.add_job(
            id=f"manual_run_{job.id}_{datetime.now().timestamp()}",
            func='app.scheduler.tasks:pipeline_task',
            args=[job.id],
            trigger='date',
            replace_existing=False
        )
        flash(f'Job "{job.name}" has been triggered to run now.', 'success')
    except Exception as e:
        flash(f'Error triggering job: {e}', 'error')
        
    return redirect(url_for('scheduler.schedule_list'))

@bp.route('/<int:job_id>/toggle', methods=['POST'])
@login_required
def toggle_schedule(job_id):
    """Enables or disables a scheduled job."""
    job = ScheduledJob.query.get_or_404(job_id)
    job.is_enabled = not job.is_enabled
    
    try:
        if job.is_enabled:
            scheduler.resume_job(str(job.id))
        else:
            scheduler.pause_job(str(job.id))
        db.session.commit()
        flash(f'Job "{job.name}" has been {"enabled" if job.is_enabled else "disabled"}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating job status: {e}', 'error')

    return redirect(url_for('scheduler.schedule_list'))

@bp.route('/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_schedule(job_id):
    """Deletes a scheduled job."""
    job = ScheduledJob.query.get_or_404(job_id)
    try:
        scheduler.remove_job(str(job.id))
        db.session.delete(job)
        db.session.commit()
        flash(f'Scheduled job "{job.name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting job: {e}', 'error')
        
    return redirect(url_for('scheduler.schedule_list'))
