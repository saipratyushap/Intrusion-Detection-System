"""
=============================================================================
REPORT SCHEDULER MODULE
=============================================================================
Handles scheduled report generation using APScheduler
=============================================================================
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import os
from pathlib import Path

from business_intelligence import ReportGenerator
from email_service import EmailService


class ReportScheduler:
    """Automated report scheduling and generation"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.report_gen = ReportGenerator()
        self.email_service = EmailService()
        self.schedules_file = Path("data/report_schedules.json")
        self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing schedules
        self.load_schedules()
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("✅ Report scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏸️ Report scheduler stopped")
    
    def load_schedules(self):
        """Load and activate all saved schedules"""
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, 'r') as f:
                    schedules = json.load(f)
                
                for schedule in schedules:
                    if schedule.get('active', True):
                        self._add_schedule_to_scheduler(schedule)
                
                print(f"✅ Loaded {len(schedules)} report schedule(s)")
            except Exception as e:
                print(f"Error loading schedules: {e}")
    
    def save_schedules(self, schedules: List[Dict[str, Any]]):
        """Save schedules to file"""
        with open(self.schedules_file, 'w') as f:
            json.dump(schedules, f, indent=2)
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """Get all saved schedules"""
        if self.schedules_file.exists():
            with open(self.schedules_file, 'r') as f:
                return json.load(f)
        return []
    
    def add_schedule(self, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new report schedule
        
        schedule_config format:
        {
            "name": "Daily Security Report",
            "report_type": "daily",  # daily, weekly, monthly, compliance
            "frequency": "daily",    # daily, weekly, monthly
            "time": "08:00",         # HH:MM format
            "day_of_week": 0,        # 0-6 for Monday-Sunday (for weekly)
            "day_of_month": 1,       # 1-31 (for monthly)
            "email_recipients": ["email@example.com"],
            "active": true
        }
        """
        schedules = self.get_all_schedules()
        
        # Generate unique ID
        schedule_id = f"schedule_{len(schedules) + 1}_{int(datetime.now().timestamp())}"
        schedule_config['id'] = schedule_id
        schedule_config['created_at'] = datetime.now().isoformat()
        schedule_config['last_run'] = None
        schedule_config['active'] = schedule_config.get('active', True)
        
        # Add to scheduler
        if schedule_config['active']:
            self._add_schedule_to_scheduler(schedule_config)
        
        # Save to file
        schedules.append(schedule_config)
        self.save_schedules(schedules)
        
        return {
            "status": "success",
            "message": "Schedule added successfully",
            "schedule_id": schedule_id
        }
    
    def remove_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Remove a schedule"""
        schedules = self.get_all_schedules()
        
        # Find and remove
        updated_schedules = [s for s in schedules if s['id'] != schedule_id]
        
        if len(updated_schedules) == len(schedules):
            return {
                "status": "error",
                "message": "Schedule not found"
            }
        
        # Remove from scheduler
        try:
            self.scheduler.remove_job(schedule_id)
        except:
            pass
        
        # Save
        self.save_schedules(updated_schedules)
        
        return {
            "status": "success",
            "message": "Schedule removed successfully"
        }
    
    def toggle_schedule(self, schedule_id: str, active: bool) -> Dict[str, Any]:
        """Enable or disable a schedule"""
        schedules = self.get_all_schedules()
        
        # Find schedule
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        
        if not schedule:
            return {
                "status": "error",
                "message": "Schedule not found"
            }
        
        schedule['active'] = active
        
        if active:
            self._add_schedule_to_scheduler(schedule)
        else:
            try:
                self.scheduler.remove_job(schedule_id)
            except:
                pass
        
        # Save
        self.save_schedules(schedules)
        
        return {
            "status": "success",
            "message": f"Schedule {'enabled' if active else 'disabled'}"
        }
    
    def _add_schedule_to_scheduler(self, schedule: Dict[str, Any]):
        """Add a schedule to APScheduler"""
        schedule_id = schedule['id']
        frequency = schedule['frequency']
        time_str = schedule['time']
        hour, minute = map(int, time_str.split(':'))
        
        # Create trigger based on frequency
        if frequency == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute)
        elif frequency == 'weekly':
            day_of_week = schedule.get('day_of_week', 0)
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        elif frequency == 'monthly':
            day_of_month = schedule.get('day_of_month', 1)
            trigger = CronTrigger(day=day_of_month, hour=hour, minute=minute)
        else:
            print(f"Unknown frequency: {frequency}")
            return
        
        # Add job
        try:
            self.scheduler.add_job(
                func=self._execute_scheduled_report,
                trigger=trigger,
                id=schedule_id,
                args=[schedule],
                replace_existing=True
            )
            print(f"✅ Added schedule: {schedule.get('name', schedule_id)}")
        except Exception as e:
            print(f"Error adding schedule: {e}")
    
    def _execute_scheduled_report(self, schedule: Dict[str, Any]):
        """Execute a scheduled report generation"""
        print(f"📊 Executing scheduled report: {schedule.get('name', 'Unknown')}")
        
        try:
            # Generate report based on type
            report_type = schedule.get('report_type', 'daily')
            
            if report_type == 'daily':
                report = self.report_gen.generate_daily_report()
            elif report_type == 'weekly':
                report = self.report_gen.generate_weekly_report()
            elif report_type == 'monthly':
                report = self.report_gen.generate_monthly_report()
            elif report_type == 'compliance':
                compliance_type = schedule.get('compliance_type', 'OSHA')
                report = self.report_gen.generate_compliance_report(compliance_type)
            else:
                print(f"Unknown report type: {report_type}")
                return
            
            # Send email if recipients configured
            recipients = schedule.get('email_recipients', [])
            if recipients:
                result = self.email_service.send_report_email(report, recipients)
                print(f"📧 Email result: {result['message']}")
            
            # Update last run time
            schedules = self.get_all_schedules()
            for s in schedules:
                if s['id'] == schedule['id']:
                    s['last_run'] = datetime.now().isoformat()
                    break
            self.save_schedules(schedules)
            
            print(f"✅ Scheduled report completed: {schedule.get('name', 'Unknown')}")
        
        except Exception as e:
            print(f"❌ Error executing scheduled report: {e}")
    
    def execute_schedule_now(self, schedule_id: str) -> Dict[str, Any]:
        """Manually trigger a schedule immediately"""
        schedules = self.get_all_schedules()
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        
        if not schedule:
            return {
                "status": "error",
                "message": "Schedule not found"
            }
        
        try:
            self._execute_scheduled_report(schedule)
            return {
                "status": "success",
                "message": "Report generated and sent successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate report: {str(e)}"
            }


# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> ReportScheduler:
    """Get or create scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ReportScheduler()
        _scheduler_instance.start()
    return _scheduler_instance
