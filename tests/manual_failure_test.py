from fastapi import HTTPException

from app.api import routes


def simulate_failure(*args, **kwargs):
    raise RuntimeError("Simulated investigation failure")


original_function = routes.run_investigation

try:
    routes.run_investigation = simulate_failure

    try:
        routes.create_new_investigation(
            routes.InvestigationRequest(
                alert="Manual failure handling test",
                siem="microsoft_sentinel",
            )
        )

    except HTTPException as exc:
        print("HTTP status:", exc.status_code)
        print("API detail:", exc.detail)

finally:
    routes.run_investigation = original_function