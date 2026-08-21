import time

from core.config.fields import REQUIRED_FIELDS


class DocumentValidator:

    def validate(self, data: dict) -> dict:

        start = time.perf_counter()

        if not isinstance(data, dict):
            raise ValueError(
                "LLM output must be a dictionary."
            )

        result = {
            field: data.get(field)
            for field in REQUIRED_FIELDS
        }

        elapsed = time.perf_counter() - start

        print(
            f"Validation: "
            f"{elapsed:.2f} seconds"
        )

        return result