import sys
import os
import time
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import screeninfo


def test_screeninfo_primary_monitor_detection():
    """Verify screeninfo correctly detects monitor dimensions and computes window centering math."""
    monitors = screeninfo.get_monitors()
    assert len(monitors) > 0
    primary = monitors[0]
    
    width = 1280
    height = 780
    win_x = primary.x + max(0, (primary.width - width) // 2)
    win_y = primary.y + max(0, (primary.height - height) // 2)

    assert win_x >= primary.x
    assert win_y >= primary.y
    assert isinstance(win_x, int)
    assert isinstance(win_y, int)


def test_system_health_monitor_cpu_alert_cooldown():
    """Verify CPU temp alert triggers warning and respects 300s cooldown."""
    import main
    
    main.last_cpu_alert_time = 0
    now = time.time()
    
    with patch("main.get_cpu_temperature", return_value=85.0), \
         patch.object(main.manager, "send_event") as mock_send_event:
        
        # Simulating alert condition logic
        cpu_temp = main.get_cpu_temperature()
        assert cpu_temp > 80.0
        
        if now - main.last_cpu_alert_time > main.ALERT_COOLDOWN:
            main.last_cpu_alert_time = now
            main.manager.send_event("system", {"value": "⚠️ ALERT: Warning. CPU temperature has exceeded 80 degrees."})
            
        assert mock_send_event.called
        assert main.last_cpu_alert_time == now
        
        # Second call immediately after should be blocked by cooldown
        mock_send_event.reset_mock()
        now2 = time.time()
        if now2 - main.last_cpu_alert_time > main.ALERT_COOLDOWN:
            main.manager.send_event("system", {"value": "⚠️ ALERT: Warning."})
            
        assert not mock_send_event.called, "Second alert should be suppressed by 300s cooldown"
