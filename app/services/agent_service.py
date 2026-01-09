"""Agent service for orchestrating agent runs."""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4
from app.models.agent import AgentRun
from app.services.analytics_agent import AnalyticsAgent
from app.services.strategist_agent import StrategistAgent
from app.services.content_agent import ContentAgent
from app.services.aggregator import Aggregator


class AgentService:
    """Service for managing agent execution."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics_agent = AnalyticsAgent(db)
        self.strategist_agent = StrategistAgent(db)
        self.content_agent = ContentAgent(db)
        self.aggregator = Aggregator(db)

    def run_weekly_analysis(
        self,
        days_back: int = 30,
        comparison_days: int = 7,
    ) -> AgentRun:
        """
        Execute the full weekly agent pipeline.
        This is the main entry point called by the API.
        """
        # Create agent run record
        run = AgentRun(
            id=uuid4(),
            run_type="weekly",
            status="running",
            started_at=datetime.utcnow(),
            input_params={
                "days_back": days_back,
                "comparison_days": comparison_days,
            },
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            # Step 1: Analytics Agent - Analyze performance
            insights = self.analytics_agent.analyze(
                run_id=run.id,
                days_back=days_back,
                comparison_days=comparison_days,
            )

            # Step 2: Strategist Agent - Make decisions
            actions = self.strategist_agent.decide(
                run_id=run.id,
                insights=insights,
            )

            # Step 3: Content Agent - Generate creatives
            creatives = self.content_agent.create(
                run_id=run.id,
                actions=actions,
            )

            # Step 4: Aggregate results
            aggregated_output = self.aggregator.aggregate(
                run_id=run.id,
                insights=insights,
                actions=actions,
                creatives=creatives,
            )

            # Update run with results
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            run.output = aggregated_output
            self.db.commit()

            return run

        except Exception as e:
            # Mark run as failed
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            run.error_message = str(e)
            self.db.commit()
            raise

