from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from providers.base import ModelResponse, ToolCall


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


class DemoProvider:
    """Local deterministic provider for UI demos when no paid API is available."""

    default_model = "local-helpdesk-demo"

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        latest = messages[-1].get("content", "") if messages else ""
        if latest.startswith("TOOL_RESULTS_JSON:"):
            match = re.search(r"TOOL_RESULTS_JSON:\s*(\[.*?\])\s*\n\n", latest, re.DOTALL)
            events = json.loads(match.group(1)) if match else []
            if not events:
                return ModelResponse(text="Mình chưa nhận được kết quả từ công cụ.")
            event = events[-1]
            result = event.get("result", {})
            if result.get("error"):
                return ModelResponse(text=f"Công cụ {event.get('tool')} báo lỗi: {result.get('error')}. Vui lòng kiểm tra input và thử lại.")
            if event.get("tool") == "check_service_status":
                status = result.get("status", "không xác định")
                service = str(result.get("service", "dịch vụ")).upper()
                detail = result.get("message") or result.get("description") or ""
                return ModelResponse(text=f"Trạng thái {service}: {status}. {detail}".strip())
            if event.get("tool") == "search_kb":
                hits = result.get("results", [])
                if not hits:
                    return ModelResponse(text="Mình chưa tìm thấy hướng dẫn phù hợp trong kho kiến thức nội bộ.")
                hit = hits[0]
                content = str(hit.get("content", ""))[:900]
                return ModelResponse(text=f"Mình tìm thấy hướng dẫn “{hit.get('title', 'IT nội bộ')}”:\n\n{content}")
            return ModelResponse(text=f"Đã hoàn tất kiểm tra bằng {event.get('tool')}. Bạn có thể mở thẻ Tool activity để xem toàn bộ kết quả.")

        text = _fold(latest)
        service_map = {"vpn": "vpn", "email": "email", "sso": "sso", "wifi": "wifi", "wi-fi": "wifi", "may in": "printing", "printer": "printing"}
        if any(word in text for word in ("trang thai", "kiem tra dich vu", "dang loi", "hoat dong")):
            for keyword, service in service_map.items():
                if keyword in text:
                    return ModelResponse(tool_calls=[ToolCall("check_service_status", {"service": service, "environment": "production"})])
        if any(word in text for word in ("huong dan", "cach sua", "khac phuc", "loi", "khong ket noi")):
            category = "all"
            for keyword, value in service_map.items():
                if keyword in text:
                    category = "printing" if value == "printing" else value
                    break
            return ModelResponse(tool_calls=[ToolCall("search_kb", {"query": latest, "category": category, "top_k": 3})])
        if any(word in text for word in ("thiet bi", "may tinh", "laptop")):
            return ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Bạn vui lòng cung cấp mã tài sản (asset ID) của thiết bị cần kiểm tra.", "response_type": "text"})])
        return ModelResponse(text="Mình có thể kiểm tra trạng thái VPN/email/Wi-Fi, tìm hướng dẫn nội bộ hoặc hỗ trợ kiểm tra thiết bị. Bạn mô tả rõ sự cố giúp mình nhé.")
