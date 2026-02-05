import pandas as pd
from datetime import datetime


class FeatureBuilder:
    """
    Converts minimal backend inputs into the full
    feature schema used during model training.
    """

    @staticmethod
    def build(click):
        # Derive behavior patterns
        click_frequency = click.clicks_per_session / max(click.session_duration_minutes, 0.1)

        bot_score = 0.0
        if click.clicks_per_session > 10:
            bot_score += 0.3
        if click.time_gap_seconds < 1.0:
            bot_score += 0.4
        if click_frequency > 8:
            bot_score += 0.3
        bot_score = min(bot_score, 1.0)

        # Deterministic categorical inference
        if click.user_agent_category == 1:
            device_type = "Desktop"
        elif click.user_agent_category == 2:
            device_type = "Mobile"
        else:
            device_type = "Tablet"

        browser = "Chrome"
        operating_system = "Windows"

        ad_position = "Top"
        device_ip_reputation = "Bad" if bot_score > 0.6 else "Good"

        # Final feature row (MATCHES TRAINING SCHEMA FOR ANN)
        # Required numeric columns:
        # 'click_duration', 'scroll_depth', 'mouse_movement', 'keystrokes_detected',
        # 'click_frequency', 'time_since_last_click', 'bot_likelihood_score',
        # 'VPN_usage', 'proxy_usage'
        #
        # Required categorical columns:
        # 'device_type', 'browser', 'operating_system', 'ad_position', 'device_ip_reputation'

        row = {
            "device_type": device_type,
            "browser": browser,
            "operating_system": operating_system,
            "ad_position": ad_position,
            "device_ip_reputation": device_ip_reputation,

            "click_duration": click.time_gap_seconds,
            "scroll_depth": min(click.clicks_per_session * 10, 100),
            "mouse_movement": min(click.clicks_per_session * 40, 400),
            "keystrokes_detected": 0 if bot_score > 0.6 else 2,

            "click_frequency": click_frequency,
            "time_since_last_click": click.time_gap_seconds,

            "VPN_usage": 1 if bot_score > 0.7 else 0,
            "proxy_usage": 1 if bot_score > 0.7 else 0,
            "bot_likelihood_score": bot_score,
        }

        return pd.DataFrame([row])
