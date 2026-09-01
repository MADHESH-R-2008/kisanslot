"""
Procurement service for managing procurement workflow.
In Phase 2, this provides basic CRUD. In Phase 3/4, this will be
enhanced with IoT weighing machine integration and automated grading.
"""


def get_procurement_step(status: str) -> int:
    """Map procurement status to a step number (0-6) for the timeline UI."""
    status_map = {
        "PENDING": 0,
        "QUALITY_CHECK": 2,
        "WEIGHING": 3,
        "COMPLETED": 6,
    }
    return status_map.get(status, 0)


def get_payment_step(status: str) -> int:
    """Map payment status to a timeline step."""
    status_map = {
        "PENDING": 0,
        "PROCESSING": 2,
        "COMPLETED": 3,
        "FAILED": -1,
    }
    return status_map.get(status, 0)
