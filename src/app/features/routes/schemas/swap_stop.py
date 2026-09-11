from uuid import UUID

from pydantic import BaseModel, model_validator


class SwapStopsRequest(BaseModel):
    stop_id_1: UUID
    stop_id_2: UUID

    @model_validator(mode="after")
    def stops_must_not_be_same(self) -> "SwapStopsRequest":
        if self.stop_id_1 == self.stop_id_2:
            raise ValueError("stop_id_1 and stop_id_2 cannot be the same")
        return self
