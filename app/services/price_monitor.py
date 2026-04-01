"""
Price monitoring service
Periodically checks price alerts and notifies users when target prices are reached
"""
import logging
from datetime import datetime, timezone
from app.models.database import db
from app.models.tracking import TrackingEvent
from app.services.hotel_provider import get_provider, HotelProviderError

logger = logging.getLogger(__name__)


class PriceMonitor:
    """Check active price alerts against current prices."""

    def check_alerts(self):
        """
        Check all active price alerts.
        For each alert, fetch the current price and compare with target.
        """
        from app.models.database import PriceAlert

        alerts = db.session.query(PriceAlert).filter_by(is_active=True).all()
        checked = 0
        triggered = 0

        for alert in alerts:
            try:
                current_price = self._get_current_price(
                    alert.hotel_id, alert.provider, alert.check_in, alert.check_out
                )

                if current_price is not None:
                    alert.current_price = current_price
                    checked += 1

                    # Check if target price reached
                    if alert.target_price and current_price <= alert.target_price:
                        alert.is_active = False
                        alert.triggered_at = datetime.now(timezone.utc)
                        triggered += 1

                        # Record a tracking event for the triggered alert
                        event = TrackingEvent(
                            user_id=alert.user_id,
                            event_type='price_alert_triggered',
                            event_data=f'{{"hotel_id":"{alert.hotel_id}","target_price":{alert.target_price},"current_price":{current_price}}}',
                            page='/alerts',
                        )
                        db.session.add(event)

                        logger.info(
                            f"[PriceMonitor] Alert triggered: user={alert.user_id} "
                            f"hotel={alert.hotel_id} target={alert.target_price} current={current_price}"
                        )

            except Exception as e:
                logger.error(f"[PriceMonitor] Error checking alert {alert.id}: {e}")

        if checked > 0:
            db.session.commit()
            logger.info(f"[PriceMonitor] Checked {checked} alerts, triggered {triggered}")

        return {'checked': checked, 'triggered': triggered}

    def _get_current_price(self, hotel_id, provider, check_in, check_out):
        """Get current price for a hotel from the provider."""
        try:
            hotel_provider = get_provider(provider)

            if provider == 'tuniu' and check_in and check_out:
                # For Tuniu, we need to search and find the hotel
                # This is a simplified approach - in production, use hotel detail API
                return None  # Tuniu doesn't have a simple price check API
            else:
                return None  # Price checking needs provider-specific implementation

        except HotelProviderError:
            return None


# Singleton
price_monitor = PriceMonitor()
